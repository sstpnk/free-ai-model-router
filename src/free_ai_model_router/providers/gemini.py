"""Google Gemini API / AI Studio provider adapter."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Optional

from free_ai_model_router.http_client.client import HttpClient
from free_ai_model_router.models import (
    ApiStyle,
    Availability,
    FreeStatus,
    Limits,
    ProviderEndpoint,
    VerificationStatus,
)
from free_ai_model_router.providers.base import (
    LimitRecord,
    PricingRecord,
    ProviderAdapter,
    ProviderModel,
    VerificationResult,
)

logger = logging.getLogger(__name__)

GEMINI_API_BASE = "https://generativelanguage.googleapis.com/v1beta"
GEMINI_MODELS_URL = f"{GEMINI_API_BASE}/models"


class GeminiAdapter:
    """Adapter for Google Gemini API."""

    provider_id = "gemini"

    def __init__(self, http_client: HttpClient) -> None:
        self.http = http_client

    async def discover_models(self) -> list[ProviderModel]:
        data = await self.http.fetch_json(
            GEMINI_MODELS_URL,
            use_cache=True,
            cache_ttl_seconds=7200,
        )
        models_raw = data.get("models", []) if isinstance(data.get("models"), list) else []
        results: list[ProviderModel] = []
        for m in models_raw:
            name: str = m.get("name", "")
            model_id = name.replace("models/", "", 1) if name else ""
            if not model_id:
                continue

            display_name: str = m.get("displayName", model_id)
            supported_methods = m.get("supportedGenerationMethods", [])

            # Only include text generation models
            if "generateContent" not in supported_methods:
                continue

            # Exclude non-chat models
            exclude = ["embedding", "aqa", "nano", "tts", "vision"]
            if any(x in model_id.lower() for x in exclude):
                continue

            # Gemini offers a free tier (AI Studio)
            # Models from gemini-2.5+ are the target
            is_generative = any("generate" in m for m in supported_methods)
            free_status = FreeStatus.DOCUMENTED_FREE if is_generative else FreeStatus.UNKNOWN

            results.append(ProviderModel(
                provider_model_id=model_id,
                name=display_name,
                litellm_model=f"gemini/{model_id}",
                api_base=GEMINI_API_BASE,
                api_style=ApiStyle.GOOGLE_AI,
                context_tokens=None,  # Not exposed in list endpoint
                free_status=free_status,
                tool_calling=True,
                vision="vision" in model_id.lower() or "imagen" in model_id.lower(),
                raw_data=m,
            ))
        return results

    async def fetch_pricing(self) -> list[PricingRecord]:
        return []

    async def fetch_limits(self) -> list[LimitRecord]:
        return []

    async def verify_model(self, model: ProviderModel, api_key: str) -> VerificationResult:
        import httpx
        try:
            import time
            start = time.monotonic()
            async with httpx.AsyncClient(timeout=30) as client:
                url = f"{GEMINI_API_BASE}/models/{model.provider_model_id}:generateContent?key={api_key}"
                response = await client.post(
                    url,
                    json={
                        "contents": [{"parts": [{"text": "Say OK"}]}],
                        "generationConfig": {"maxOutputTokens": 5},
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
                return VerificationResult(
                    provider_model_id=model.provider_model_id,
                    status=VerificationStatus.INVALID_RESPONSE,
                    http_status=response.status_code,
                )
        except httpx.TimeoutException:
            return VerificationResult(provider_model_id=model.provider_model_id, status=VerificationStatus.TIMEOUT)
        except Exception as e:
            return VerificationResult(
                provider_model_id=model.provider_model_id,
                status=VerificationStatus.PROVIDER_UNAVAILABLE,
                error_message=str(e),
            )

    def to_provider_endpoint(self, model: ProviderModel) -> ProviderEndpoint:
        return ProviderEndpoint(
            endpoint_id=f"gemini/{model.provider_model_id}",
            provider_id="gemini",
            canonical_model_id=f"google/{model.provider_model_id}",
            provider_model_id=model.provider_model_id,
            litellm_model=model.litellm_model or f"gemini/{model.provider_model_id}",
            api_base=GEMINI_API_BASE,
            api_style=ApiStyle.GOOGLE_AI,
            availability=Availability.AVAILABLE,
            free_status=model.free_status,
            limits=model.limits,
            context_tokens=model.context_tokens,
            discovered_at=datetime.now(timezone.utc),
        )

    def to_litellm_model_string(self, model: ProviderModel) -> str:
        return f"gemini/{model.provider_model_id}"
