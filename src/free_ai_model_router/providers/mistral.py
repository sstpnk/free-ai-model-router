"""Mistral AI provider adapter."""

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

MISTRAL_API_BASE = "https://api.mistral.ai/v1"
MISTRAL_MODELS_URL = f"{MISTRAL_API_BASE}/models"


class MistralAdapter:
    """Adapter for Mistral AI API."""

    provider_id = "mistral"

    def __init__(self, http_client: HttpClient, api_key: Optional[str] = None) -> None:
        self.http = http_client
        self.api_key = api_key

    async def discover_models(self) -> list[ProviderModel]:
        headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else None
        data = await self.http.fetch_json(
            MISTRAL_MODELS_URL,
            headers=headers,
            use_cache=True,
            cache_ttl_seconds=7200,
        )
        models_raw = data.get("data", []) if isinstance(data.get("data"), list) else []
        results: list[ProviderModel] = []
        for m in models_raw:
            model_id: str = m.get("id", "")
            if not model_id:
                continue

            # All models accessible via user's Mistral API key.
            # Mistral doesn't expose free/paid via model list endpoint.
            # User's key determines access, so all are account-specific free.
            free_status = FreeStatus.ACCOUNT_SPECIFIC_FREE

            results.append(ProviderModel(
                provider_model_id=model_id,
                name=m.get("id", model_id),
                litellm_model=f"mistral/{model_id}",
                api_base=MISTRAL_API_BASE,
                api_style=ApiStyle.OPENAI_COMPATIBLE,
                free_status=free_status,
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
                    f"{MISTRAL_API_BASE}/chat/completions",
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
            endpoint_id=f"mistral/{model.provider_model_id}",
            provider_id="mistral",
            canonical_model_id=f"mistral/{model.provider_model_id}",
            provider_model_id=model.provider_model_id,
            litellm_model=f"mistral/{model.provider_model_id}",
            api_base=MISTRAL_API_BASE,
            api_style=ApiStyle.OPENAI_COMPATIBLE,
            availability=Availability.AVAILABLE,
            free_status=model.free_status,
            limits=model.limits,
            context_tokens=model.context_tokens,
            discovered_at=datetime.now(timezone.utc),
        )

    def to_litellm_model_string(self, model: ProviderModel) -> str:
        return f"mistral/{model.provider_model_id}"
