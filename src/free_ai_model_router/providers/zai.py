"""z.ai provider adapter."""

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
from free_ai_model_router.verification.status import (
    classify_http_status,
    parse_retry_after_seconds,
    response_error_message,
)

logger = logging.getLogger(__name__)

ZAI_API_BASE = "https://api.z.ai/api/paas/v4"
ZAI_MODELS_URL = f"{ZAI_API_BASE}/models"


class ZAIAdapter:
    """Adapter for z.ai API."""

    provider_id = "zai"

    def __init__(self, http_client: HttpClient, api_key: Optional[str] = None) -> None:
        self.http = http_client
        self.api_key = api_key

    async def discover_models(self) -> list[ProviderModel]:
        headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else None
        data = await self.http.fetch_json(
            ZAI_MODELS_URL,
            headers=headers,
            use_cache=True,
            cache_ttl_seconds=3600,
        )
        models_raw = data.get("data", []) if isinstance(data.get("data"), list) else []
        results: list[ProviderModel] = []
        for m in models_raw:
            model_id: str = m.get("id", "")
            if not model_id:
                continue

            results.append(ProviderModel(
                provider_model_id=model_id,
                name=m.get("id", model_id),
                litellm_model=f"openai/{model_id}",
                api_base=ZAI_API_BASE,
                api_style=ApiStyle.OPENAI_COMPATIBLE,
                free_status=FreeStatus.ACCOUNT_SPECIFIC_FREE,  # z.ai is account-specific free
                tool_calling=True,
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
            async with httpx.AsyncClient(timeout=15) as client:
                response = await client.post(
                    f"{ZAI_API_BASE}/chat/completions",
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
                body_text = getattr(response, "text", "")
                headers = getattr(response, "headers", {})
                status = classify_http_status(response.status_code, body_text)
                return VerificationResult(
                    provider_model_id=model.provider_model_id,
                    status=status,
                    latency_ms=latency,
                    http_status=response.status_code,
                    retry_after_seconds=parse_retry_after_seconds(headers),
                    error_message=None if status == VerificationStatus.SUCCESS else response_error_message(body_text),
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
            endpoint_id=f"zai/{model.provider_model_id}",
            provider_id="zai",
            canonical_model_id=f"zai/{model.provider_model_id}",
            provider_model_id=model.provider_model_id,
            litellm_model=f"openai/{model.provider_model_id}",
            api_base=ZAI_API_BASE,
            api_style=ApiStyle.OPENAI_COMPATIBLE,
            availability=Availability.AVAILABLE,
            free_status=model.free_status,
            limits=model.limits,
            context_tokens=model.context_tokens,
            discovered_at=datetime.now(timezone.utc),
        )

    def to_litellm_model_string(self, model: ProviderModel) -> str:
        return f"openai/{model.provider_model_id}"
