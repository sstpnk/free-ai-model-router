"""DeepInfra provider adapter."""

from __future__ import annotations

import json
from collections.abc import Iterable
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
from free_ai_model_router.verification.status import (
    classify_http_status,
    parse_retry_after_seconds,
    response_error_message,
)

DEEPINFRA_API_BASE = "https://api.deepinfra.com/v1/openai"
DEEPINFRA_MODELS_URL = "https://api.deepinfra.com/models/list"
_TEXT_MODEL_TYPES = {"text-generation", "text2text-generation", "chat-completion"}
_NON_CHAT_MODEL_MARKERS = ("embedding", "rerank", "whisper", "tts", "speech")
_CATALOG_MODEL_LIMIT = 250


def _extract_json_array_objects(chunks: Iterable[bytes], *, max_objects: int) -> list[dict]:
    """Extract complete objects from a streamed JSON array without waiting for EOF."""
    decoder = json.JSONDecoder()
    buffer = ""
    search_pos = 0
    results: list[dict] = []

    for chunk in chunks:
        buffer += chunk.decode("utf-8", errors="replace")
        while len(results) < max_objects:
            start = buffer.find("{", search_pos)
            if start == -1:
                search_pos = max(0, len(buffer) - 1)
                break
            try:
                value, end = decoder.raw_decode(buffer[start:])
            except json.JSONDecodeError:
                search_pos = start
                break
            if isinstance(value, dict):
                results.append(value)
            search_pos = start + end
        if len(results) >= max_objects:
            break

    return results


class DeepInfraAdapter:
    """Adapter for DeepInfra catalog plus OpenAI-compatible chat API."""

    provider_id = "deepinfra"

    def __init__(self, http_client: HttpClient, api_key: str | None = None) -> None:
        self.http = http_client
        self.api_key = api_key

    async def discover_models(self) -> list[ProviderModel]:
        headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else None
        models_raw = await self._fetch_catalog(headers)
        results: list[ProviderModel] = []
        for raw in models_raw:
            model_id = str(raw.get("model_name", ""))
            if not model_id:
                continue
            if any(marker in model_id.lower() for marker in _NON_CHAT_MODEL_MARKERS):
                continue

            reported_type = str(raw.get("reported_type") or raw.get("type") or "").lower()
            if reported_type and reported_type not in _TEXT_MODEL_TYPES:
                continue

            context = raw.get("max_tokens")
            results.append(
                ProviderModel(
                    provider_model_id=model_id,
                    name=model_id,
                    litellm_model=f"deepinfra/{model_id}",
                    api_base=DEEPINFRA_API_BASE,
                    api_style=ApiStyle.OPENAI_COMPATIBLE,
                    context_tokens=context if isinstance(context, int) else None,
                    free_status=FreeStatus.ACCOUNT_SPECIFIC_FREE,
                    raw_data=raw,
                )
            )
        return results

    async def _fetch_catalog(self, headers: dict[str, str] | None) -> list[dict]:
        import httpx

        parsed: list[dict] = []
        try:
            async with httpx.AsyncClient(
                timeout=httpx.Timeout(20.0, connect=10.0, read=5.0),
                follow_redirects=True,
            ) as client:
                async with client.stream("GET", DEEPINFRA_MODELS_URL, headers=headers) as response:
                    response.raise_for_status()

                    async def chunks():
                        async for chunk in response.aiter_bytes():
                            yield chunk

                    chunk_buffer: list[bytes] = []
                    async for chunk in chunks():
                        chunk_buffer.append(chunk)
                        parsed = _extract_json_array_objects(chunk_buffer, max_objects=_CATALOG_MODEL_LIMIT)
                        if len(parsed) >= _CATALOG_MODEL_LIMIT:
                            break
        except httpx.ReadTimeout:
            if not parsed:
                raise

        return parsed

    async def fetch_pricing(self) -> list[PricingRecord]:
        return []

    async def fetch_limits(self) -> list[LimitRecord]:
        return []

    async def verify_model(self, model: ProviderModel, api_key: str) -> VerificationResult:
        import time

        import httpx

        try:
            start = time.monotonic()
            async with httpx.AsyncClient(timeout=15) as client:
                response = await client.post(
                    f"{DEEPINFRA_API_BASE}/chat/completions",
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
            endpoint_id=f"deepinfra/{model.provider_model_id}",
            provider_id="deepinfra",
            canonical_model_id=f"deepinfra/{model.provider_model_id}",
            provider_model_id=model.provider_model_id,
            litellm_model=model.litellm_model or f"deepinfra/{model.provider_model_id}",
            api_base=DEEPINFRA_API_BASE,
            api_style=ApiStyle.OPENAI_COMPATIBLE,
            availability=Availability.AVAILABLE,
            free_status=model.free_status,
            limits=model.limits,
            context_tokens=model.context_tokens,
            discovered_at=datetime.now(UTC),
            source_url=DEEPINFRA_MODELS_URL,
        )

    def to_litellm_model_string(self, model: ProviderModel) -> str:
        return f"deepinfra/{model.provider_model_id}"
