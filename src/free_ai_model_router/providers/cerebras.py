"""Cerebras provider adapter."""

from __future__ import annotations

from datetime import UTC, datetime

from free_ai_model_router.http_client.client import HttpClient
from free_ai_model_router.models import (
    ApiStyle,
    Availability,
    FreeStatus,
    ProviderEndpoint,
    VerificationStatus,
)
from free_ai_model_router.providers.base import (
    LimitRecord,
    PricingRecord,
    ProviderModel,
    VerificationResult,
)

CEREBRAS_API_BASE = "https://api.cerebras.ai/v1"
CEREBRAS_MODELS_URL = f"{CEREBRAS_API_BASE}/models"
_NON_CHAT_MODEL_MARKERS = ("whisper", "distil", "guard", "tts", "speech", "playai", "embedding", "rerank")
_FREE_MODEL_IDS = {"gpt-oss-120b", "gemma-4-31b", "zai-glm-4.7"}


class CerebrasAdapter:
    """Adapter for Cerebras API."""

    provider_id = "cerebras"

    def __init__(self, http_client: HttpClient, api_key: str | None = None) -> None:
        self.http = http_client
        self.api_key = api_key

    async def discover_models(self) -> list[ProviderModel]:
        headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else None
        data = await self.http.fetch_json(
            CEREBRAS_MODELS_URL,
            headers=headers,
            use_cache=True,
            cache_ttl_seconds=3600,
        )
        models_raw = data.get("data", []) if isinstance(data.get("data"), list) else []
        results: list[ProviderModel] = []
        for m in models_raw:
            model_id = str(m.get("id", ""))
            if not model_id:
                continue

            if any(marker in model_id.lower() for marker in _NON_CHAT_MODEL_MARKERS):
                continue

            capabilities = m.get("capabilities") if isinstance(m.get("capabilities"), dict) else {}
            tool_calling = bool(
                m.get("tool_calling")
                or m.get("supports_tool_calling")
                or capabilities.get("tool_calling")
            )
            context_tokens = m.get("context_length")
            free_status = FreeStatus.VERIFIED_FREE if model_id.lower() in _FREE_MODEL_IDS else FreeStatus.UNKNOWN
            results.append(
                ProviderModel(
                    provider_model_id=model_id,
                    name=str(m.get("id", model_id)),
                    litellm_model=f"cerebras/{model_id}",
                    api_base=CEREBRAS_API_BASE,
                    api_style=ApiStyle.OPENAI_COMPATIBLE,
                    context_tokens=context_tokens if isinstance(context_tokens, int) else None,
                    free_status=free_status,
                    tool_calling=tool_calling,
                    raw_data=m,
                )
            )
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
            async with httpx.AsyncClient(timeout=15) as client:
                response = await client.post(
                    f"{CEREBRAS_API_BASE}/chat/completions",
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
            endpoint_id=f"cerebras/{model.provider_model_id}",
            provider_id="cerebras",
            canonical_model_id=f"cerebras/{model.provider_model_id}",
            provider_model_id=model.provider_model_id,
            litellm_model=f"cerebras/{model.provider_model_id}",
            api_base=CEREBRAS_API_BASE,
            api_style=ApiStyle.OPENAI_COMPATIBLE,
            availability=Availability.AVAILABLE,
            free_status=model.free_status,
            limits=model.limits,
            context_tokens=model.context_tokens,
            discovered_at=datetime.now(UTC),
        )

    def to_litellm_model_string(self, model: ProviderModel) -> str:
        return f"cerebras/{model.provider_model_id}"
