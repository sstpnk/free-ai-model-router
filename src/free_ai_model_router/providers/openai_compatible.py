"""Generic adapter for providers that expose OpenAI-compatible APIs."""

from __future__ import annotations

from datetime import UTC, datetime

from free_ai_model_router.http_client.client import HttpClient
from free_ai_model_router.models import (
    ApiStyle,
    Availability,
    FreeStatus,
    ProviderConfig,
    ProviderEndpoint,
    VerificationStatus,
)
from free_ai_model_router.providers.base import (
    LimitRecord,
    PricingRecord,
    ProviderModel,
    VerificationResult,
)
from free_ai_model_router.verification.status import (
    classify_http_status,
    parse_retry_after_seconds,
    response_error_message,
)

_NON_CHAT_MODEL_MARKERS = ("embedding", "rerank", "whisper", "tts", "speech", "moderation")


class GenericOpenAICompatibleAdapter:
    """Adapter for providers with standard /models and /chat/completions endpoints."""

    def __init__(
        self,
        http_client: HttpClient,
        provider_config: ProviderConfig,
        api_key: str | None = None,
    ) -> None:
        self.http = http_client
        self.config = provider_config
        self.provider_id = provider_config.provider_id
        self.api_key = api_key

    async def discover_models(self) -> list[ProviderModel]:
        models_url = self.config.sources.models_api
        if not models_url and self.config.api_base:
            models_url = f"{self.config.api_base.rstrip('/')}/models"
        if not models_url:
            return []

        headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else None
        data = await self.http.fetch_json(
            models_url,
            headers=headers,
            use_cache=True,
            cache_ttl_seconds=3600,
        )
        raw_models = data.get("data", []) if isinstance(data.get("data"), list) else []

        results: list[ProviderModel] = []
        for raw in raw_models:
            model_id = str(raw.get("id", ""))
            if not model_id:
                continue
            if any(marker in model_id.lower() for marker in _NON_CHAT_MODEL_MARKERS):
                continue

            capabilities = raw.get("capabilities") if isinstance(raw.get("capabilities"), dict) else {}
            context = raw.get("context_length") or raw.get("context_window")
            free_status = FreeStatus.VERIFIED_FREE if ":free" in model_id else FreeStatus.UNKNOWN
            results.append(
                ProviderModel(
                    provider_model_id=model_id,
                    name=str(raw.get("name", model_id)),
                    litellm_model=f"{self.provider_id}/{model_id}",
                    api_base=self.config.api_base,
                    api_style=ApiStyle.OPENAI_COMPATIBLE,
                    context_tokens=context if isinstance(context, int) else None,
                    free_status=free_status,
                    tool_calling=bool(
                        raw.get("tool_calling")
                        or raw.get("supports_tool_calling")
                        or capabilities.get("tool_calling")
                    ),
                    raw_data=raw,
                )
            )
        return results

    async def fetch_pricing(self) -> list[PricingRecord]:
        return []

    async def fetch_limits(self) -> list[LimitRecord]:
        return []

    async def verify_model(self, model: ProviderModel, api_key: str) -> VerificationResult:
        import time

        import httpx

        api_base = (model.api_base or self.config.api_base or "").rstrip("/")
        if not api_base:
            return VerificationResult(
                provider_model_id=model.provider_model_id,
                status=VerificationStatus.PROVIDER_UNAVAILABLE,
                error_message="api_base is not configured",
            )

        try:
            start = time.monotonic()
            async with httpx.AsyncClient(timeout=15) as client:
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
        except Exception as exc:
            return VerificationResult(
                provider_model_id=model.provider_model_id,
                status=VerificationStatus.PROVIDER_UNAVAILABLE,
                error_message=str(exc),
            )

    def to_provider_endpoint(self, model: ProviderModel) -> ProviderEndpoint:
        return ProviderEndpoint(
            endpoint_id=f"{self.provider_id}/{model.provider_model_id}",
            provider_id=self.provider_id,
            canonical_model_id=f"{self.provider_id}/{model.provider_model_id}",
            provider_model_id=model.provider_model_id,
            litellm_model=model.litellm_model or self.to_litellm_model_string(model),
            api_base=model.api_base or self.config.api_base,
            api_style=ApiStyle.OPENAI_COMPATIBLE,
            availability=Availability.AVAILABLE,
            free_status=model.free_status,
            limits=model.limits,
            context_tokens=model.context_tokens,
            discovered_at=datetime.now(UTC),
            source_url=self.config.sources.models_api,
        )

    def to_litellm_model_string(self, model: ProviderModel) -> str:
        return f"{self.provider_id}/{model.provider_model_id}"
