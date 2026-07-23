"""Cloudflare Workers AI provider adapter.

Only Cloudflare-hosted models (@cf/ prefix) are included — third-party
models running on Cloudflare's infrastructure are excluded.

Free tier: 10,000 neurons/day (resets at 00:00 UTC).
Rate limits vary by task type (text-generation: 300 req/min, text-to-image: 720, ...).

Requires two env vars:
  CLOUDFLARE_API_KEY    — API token (cfut_...)
  CLOUDFLARE_ACCOUNT_ID — Cloudflare account ID (hex string)
"""

from __future__ import annotations

import logging
import os
import time
from datetime import UTC, datetime

import httpx

from free_ai_model_router.http_client.client import HttpClient
from free_ai_model_router.models import (
    ApiStyle,
    Availability,
    FreeStatus,
    Limits,
    Modality,
    ProviderEndpoint,
    VerificationStatus,
)
from free_ai_model_router.providers.base import (
    LimitRecord,
    PricingRecord,
    ProviderModel,
    VerificationResult,
)

logger = logging.getLogger(__name__)

CLOUDFLARE_API_BASE = "https://api.cloudflare.com/client/v4"

# Only include Cloudflare-hosted models (not third-party @hf/, @cf/ is first-party)
CLOUDFLARE_HOSTED_PREFIX = "@cf/"

# Rate limits by task type — from Cloudflare docs (2026-07-23)
TASK_RATE_LIMITS: dict[str, int] = {
    "automatic-speech-recognition": 720,
    "image-classification": 3000,
    "image-to-text": 720,
    "object-detection": 3000,
    "summarization": 1500,
    "text-classification": 2000,
    "text-embeddings": 3000,
    "text-generation": 300,
    "text-to-image": 720,
    "translation": 720,
}

# Task type → Modality mapping
TASK_MODALITIES: dict[str, list[Modality]] = {
    "text-generation": [Modality.TEXT],
    "text-to-image": [Modality.IMAGE_GENERATION],
    "text-to-speech": [Modality.AUDIO_GENERATION],
    "automatic-speech-recognition": [Modality.AUDIO_ANALYSIS],
    "image-to-text": [Modality.IMAGE_ANALYSIS],
    "summarization": [Modality.TEXT],
    "translation": [Modality.TEXT],
    "text-classification": [Modality.TEXT],
    "text-embeddings": [Modality.TEXT],
    "object-detection": [Modality.IMAGE_ANALYSIS],
    "image-classification": [Modality.IMAGE_ANALYSIS],
}

# Model-name heuristics → task type (fallback when API doesn't provide it)
_MODEL_NAME_TASK_HINTS: list[tuple[list[str], str]] = [
    (["whisper", "deepgram/flux"], "automatic-speech-recognition"),
    (["flux", "stable-diffusion", "dreamshaper", "schnell", "klein",
      "latent-consistency", "lcm", "playground"], "text-to-image"),
    (["aura"], "text-to-speech"),
    (["bge", "embedding"], "text-embeddings"),
    (["detr", "resnet", "yolo"], "object-detection"),
    (["distilbert", "llama-guard", "sst-2", "reranker"], "text-classification"),
    (["bart"], "summarization"),
    (["uform"], "image-to-text"),
]

# Free tier: 10,000 neurons per day
CLOUDFLARE_DAILY_NEURON_LIMIT = 10_000


def _infer_task_type(model_id: str) -> str:
    """Guess task type from model ID when the API doesn't provide it."""
    model_lower = model_id.lower()
    for patterns, task in _MODEL_NAME_TASK_HINTS:
        if any(p in model_lower for p in patterns):
            return task
    # Default: most chat-capable models are text-generation
    return "text-generation"


def _get_modalities(task_type: str) -> list[Modality]:
    return TASK_MODALITIES.get(task_type, [Modality.TEXT])


class CloudflareAdapter:
    """Adapter for Cloudflare Workers AI API.

    Only discovers **Cloudflare-hosted** models (``@cf/...``).  Third-party
    models that run on Cloudflare's network (``@hf/...`` etc.) are excluded
    because their availability / pricing is not controlled by Cloudflare.
    """

    provider_id = "cloudflare"

    def __init__(self, http_client: HttpClient, api_key: str | None = None) -> None:
        self.http = http_client
        self.api_key = api_key
        self.account_id = os.environ.get("CLOUDFLARE_ACCOUNT_ID")

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _api_base(self) -> str | None:
        """OpenAI-compatible base URL (requires account_id)."""
        if not self.account_id:
            return None
        return (
            f"{CLOUDFLARE_API_BASE}/accounts/{self.account_id}/ai/v1"
        )

    def _models_search_url(self) -> str | None:
        if not self.account_id:
            return None
        return (
            f"{CLOUDFLARE_API_BASE}/accounts/{self.account_id}/ai/models/search"
        )

    # ------------------------------------------------------------------
    # Model discovery
    # ------------------------------------------------------------------

    async def discover_models(self) -> list[ProviderModel]:
        if not self.account_id:
            logger.warning(
                "CLOUDFLARE_ACCOUNT_ID not set — skipping model discovery. "
                "Set the env var to enable Cloudflare Workers AI."
            )
            return []
        if not self.api_key:
            logger.warning("CLOUDFLARE_API_KEY not set — skipping model discovery")
            return []

        search_url = self._models_search_url()
        api_base = self._api_base()
        assert search_url is not None and api_base is not None

        try:
            data = await self.http.fetch_json(
                search_url,
                headers={"Authorization": f"Bearer {self.api_key}"},
                use_cache=True,
                cache_ttl_seconds=7200,
            )
        except Exception as exc:
            logger.warning("Failed to fetch Cloudflare model catalog: %s", exc)
            return []

        # Log raw response structure
        logger.info("Cloudflare API response: success=%s, result_type=%s, keys=%s",
                   data.get("success"), type(data.get("result")).__name__,
                   list(data.keys()))

        raw_models = self._extract_models(data)
        if not raw_models:
            logger.info("No models returned by Cloudflare API")
            return []

        logger.info("Extracted %d models from API (before filtering)", len(raw_models))

        results: list[ProviderModel] = []
        for m in raw_models:
            # Log full model structure for debugging
            logger.debug("Full model object: %s", m)
            model_id = str(m.get("id") or "")
            cloudflare_model_id = str(m.get("model") or model_id)
            if not cloudflare_model_id:
                continue

            logger.info("Cloudflare model: id=%s, model=%s (starts with @cf/: %s)",
                       model_id, cloudflare_model_id, cloudflare_model_id.startswith(CLOUDFLARE_HOSTED_PREFIX))

            # Only Cloudflare-hosted models
            if not cloudflare_model_id.startswith(CLOUDFLARE_HOSTED_PREFIX):
                logger.info("Model %s filtered out (model field doesn't start with @cf/)", cloudflare_model_id)
                continue

            logger.info("Cloudflare model passed filter: %s", model_id)

            # Determine task type
            task_type = self._resolve_task_type(m, cloudflare_model_id)
            modalities = _get_modalities(task_type)
            rate_limit = TASK_RATE_LIMITS.get(task_type, 300)

            # Context length from properties if available
            props = m.get("properties") or {}
            ctx = (
                int(props["context_length"])
                if isinstance(props, dict) and "context_length" in props
                else None
            )

            # Tool calling / function calling capability
            caps_raw = m.get("capabilities") or []
            caps_str = " ".join(
                c.lower() if isinstance(c, str) else str(c).lower()
                for c in (caps_raw if isinstance(caps_raw, list) else [caps_raw])
            )
            tool_calling = "function-calling" in caps_str or "function calling" in caps_str

            results.append(ProviderModel(
                provider_model_id=cloudflare_model_id,
                name=str(m.get("name", cloudflare_model_id)),
                litellm_model=f"cloudflare/{cloudflare_model_id}",
                api_base=api_base,
                api_style=ApiStyle.OPENAI_COMPATIBLE,
                context_tokens=ctx,
                free_status=FreeStatus.DOCUMENTED_FREE,
                limits=Limits(
                    requests_per_minute=rate_limit,
                    requests_per_day=CLOUDFLARE_DAILY_NEURON_LIMIT,
                ),
                tool_calling=tool_calling,
                modalities=modalities,
                raw_data=m,
            ))

        logger.info("Discovered %d Cloudflare-hosted models", len(results))
        return results

    # ------------------------------------------------------------------
    # Response parsing helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _resolve_task_type(model: dict, model_id: str) -> str:
        """Read task from API response or fall back to heuristics."""
        task_obj = model.get("task")
        if isinstance(task_obj, dict):
            tid = str(task_obj.get("id", ""))
            if tid:
                return tid
        if isinstance(task_obj, str) and task_obj:
            return task_obj
        return _infer_task_type(model_id)

    @staticmethod
    def _extract_models(data: dict) -> list[dict]:
        """Try several Cloudflare API response shapes to extract model list."""
        result = data.get("result")

        # { success, result: { models: [...] } }
        if isinstance(result, dict):
            models = result.get("models")
            if isinstance(models, list):
                return models
            # Single model object?
            if result.get("id"):
                return [result]
            return []

        # { success, result: [...] }
        if isinstance(result, list):
            return result

        # { models: [...] }  (Workers binding format)
        models = data.get("models")
        if isinstance(models, list):
            return models

        # { data: [...] }  (OpenAI-compatible format)
        lst = data.get("data")
        if isinstance(lst, list):
            return lst

        return []

    # ------------------------------------------------------------------
    # Pricing & limits
    # ------------------------------------------------------------------

    async def fetch_pricing(self) -> list[PricingRecord]:
        """Cloudflare uses a neuron-based billing model; no per-model prices."""
        return [
            PricingRecord(
                provider_model_id="*",
                trial_credit=True,
                source_url="https://developers.cloudflare.com/workers-ai/platform/pricing",
            ),
        ]

    async def fetch_limits(self) -> list[LimitRecord]:
        """Report the daily free-tier neuron quota."""
        return [
            LimitRecord(
                provider_model_id="*",
                requests_per_day=CLOUDFLARE_DAILY_NEURON_LIMIT,
                source_url="https://developers.cloudflare.com/workers-ai/platform/pricing",
            ),
        ]

    # ------------------------------------------------------------------
    # Verification
    # ------------------------------------------------------------------

    async def verify_model(self, model: ProviderModel, api_key: str) -> VerificationResult:
        """Verify via the OpenAI-compatible /chat/completions endpoint.

        Only works for text-generation models.  Image / audio / embedding
        models will return INVALID_RESPONSE, which is expected.
        """
        api_base = self._api_base()
        if not api_base:
            return VerificationResult(
                provider_model_id=model.provider_model_id,
                status=VerificationStatus.PROVIDER_UNAVAILABLE,
                error_message="CLOUDFLARE_ACCOUNT_ID not set",
            )

        try:
            start = time.monotonic()
            async with httpx.AsyncClient(timeout=20) as client:
                response = await client.post(
                    f"{api_base}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": model.provider_model_id,
                        "messages": [{"role": "user", "content": "Say OK"}],
                        "max_tokens": 5,
                    },
                )
                latency = int((time.monotonic() - start) * 1000)

                if response.status_code == 200:
                    return VerificationResult(
                        provider_model_id=model.provider_model_id,
                        status=VerificationStatus.SUCCESS,
                        latency_ms=latency,
                        http_status=200,
                    )
                if response.status_code == 401:
                    return VerificationResult(
                        provider_model_id=model.provider_model_id,
                        status=VerificationStatus.AUTHENTICATION_FAILED,
                        http_status=401,
                    )
                if response.status_code == 429:
                    return VerificationResult(
                        provider_model_id=model.provider_model_id,
                        status=VerificationStatus.RATE_LIMITED,
                        http_status=429,
                    )
                return VerificationResult(
                    provider_model_id=model.provider_model_id,
                    status=VerificationStatus.INVALID_RESPONSE,
                    http_status=response.status_code,
                )

        except httpx.TimeoutException:
            return VerificationResult(
                provider_model_id=model.provider_model_id,
                status=VerificationStatus.TIMEOUT,
            )
        except Exception as exc:
            return VerificationResult(
                provider_model_id=model.provider_model_id,
                status=VerificationStatus.PROVIDER_UNAVAILABLE,
                error_message=str(exc),
            )

    # ------------------------------------------------------------------
    # Conversion
    # ------------------------------------------------------------------

    def to_provider_endpoint(self, model: ProviderModel) -> ProviderEndpoint:
        return ProviderEndpoint(
            endpoint_id=f"cloudflare/{model.provider_model_id}",
            provider_id="cloudflare",
            canonical_model_id=f"cloudflare/{model.provider_model_id}",
            provider_model_id=model.provider_model_id,
            litellm_model=model.litellm_model or f"cloudflare/{model.provider_model_id}",
            api_base=model.api_base,
            api_style=ApiStyle.OPENAI_COMPATIBLE,
            availability=Availability.AVAILABLE,
            free_status=model.free_status,
            limits=model.limits,
            context_tokens=model.context_tokens,
            discovered_at=datetime.now(UTC),
        )

    def to_litellm_model_string(self, model: ProviderModel) -> str:
        return f"cloudflare/{model.provider_model_id}"
