"""OpenRouter provider adapter."""

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
    RuntimeCheck,
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

OPENROUTER_API_BASE = "https://openrouter.ai/api/v1"
OPENROUTER_MODELS_URL = f"{OPENROUTER_API_BASE}/models"


class OpenRouterAdapter:
    """Adapter for OpenRouter API."""

    provider_id = "openrouter"

    def __init__(self, http_client: HttpClient, api_key: Optional[str] = None) -> None:
        self.http = http_client
        self.api_key = api_key

    async def discover_models(self) -> list[ProviderModel]:
        """Fetch all models from OpenRouter."""
        headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else None
        data = await self.http.fetch_json(
            OPENROUTER_MODELS_URL,
            headers=headers,
            use_cache=True,
            cache_ttl_seconds=7200,
        )
        models_raw = data.get("data", [])
        results: list[ProviderModel] = []
        for m in models_raw:
            model_id: str = m.get("id", "")
            if not model_id:
                continue

            # Determine free status from OpenRouter naming convention
            free_status = FreeStatus.VERIFIED_FREE if ":free" in model_id else FreeStatus.UNKNOWN

            # Check if model is free via pricing
            pricing = m.get("pricing", {})
            if pricing.get("prompt") == "0" and pricing.get("completion") == "0":
                free_status = FreeStatus.VERIFIED_FREE

            context = m.get("context_length")
            limits = Limits(
                requests_per_day=None,
                tokens_per_day=None,
            )

            results.append(ProviderModel(
                provider_model_id=model_id,
                name=m.get("name", model_id),
                litellm_model=f"openrouter/{model_id}",
                api_base=OPENROUTER_API_BASE,
                api_style=ApiStyle.OPENAI_COMPATIBLE,
                context_tokens=context,
                max_output_tokens=None,
                free_status=free_status,
                limits=limits,
                tool_calling=True,  # OpenRouter generally supports tool calling
                raw_data=m,
            ))
        return results

    async def fetch_pricing(self) -> list[PricingRecord]:
        """Pricing is returned inline with model list."""
        data = await self.http.fetch_json(OPENROUTER_MODELS_URL, use_cache=True)
        models_raw = data.get("data", [])
        results: list[PricingRecord] = []
        for m in models_raw:
            pricing = m.get("pricing", {})
            results.append(PricingRecord(
                provider_model_id=m.get("id", ""),
                input_price_per_million=float(pricing.get("prompt", 0)) * 1_000_000 if pricing.get("prompt") else None,
                output_price_per_million=float(pricing.get("completion", 0)) * 1_000_000 if pricing.get("completion") else None,
                free_input=pricing.get("prompt") == "0",
                free_output=pricing.get("completion") == "0",
                source_url=OPENROUTER_MODELS_URL,
            ))
        return results

    async def fetch_limits(self) -> list[LimitRecord]:
        """OpenRouter rate limits are account-based, not per-model."""
        return []

    async def verify_model(self, model: ProviderModel, api_key: str) -> VerificationResult:
        """Verify model by sending a minimal chat completion request."""
        import httpx
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                import time
                start = time.monotonic()
                response = await client.post(
                    f"{OPENROUTER_API_BASE}/chat/completions",
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
                elif response.status_code == 401:
                    return VerificationResult(
                        provider_model_id=model.provider_model_id,
                        status=VerificationStatus.AUTHENTICATION_FAILED,
                        http_status=401,
                    )
                elif response.status_code == 429:
                    return VerificationResult(
                        provider_model_id=model.provider_model_id,
                        status=VerificationStatus.RATE_LIMITED,
                        http_status=429,
                    )
                else:
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
        except Exception as e:
            return VerificationResult(
                provider_model_id=model.provider_model_id,
                status=VerificationStatus.PROVIDER_UNAVAILABLE,
                error_message=str(e),
            )

    def to_provider_endpoint(self, model: ProviderModel) -> ProviderEndpoint:
        return ProviderEndpoint(
            endpoint_id=f"openrouter/{model.provider_model_id}",
            provider_id="openrouter",
            canonical_model_id=f"openrouter/{model.provider_model_id}",
            provider_model_id=model.provider_model_id,
            litellm_model=f"openrouter/{model.provider_model_id}",
            api_base=OPENROUTER_API_BASE,
            api_style=ApiStyle.OPENAI_COMPATIBLE,
            availability=Availability.AVAILABLE,
            free_status=model.free_status,
            limits=model.limits,
            context_tokens=model.context_tokens,
            discovered_at=datetime.now(timezone.utc),
        )

    def to_litellm_model_string(self, model: ProviderModel) -> str:
        return f"openrouter/{model.provider_model_id}"
