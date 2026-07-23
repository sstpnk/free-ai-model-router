"""Tests for provider adapters — zero-network unit tests for conversion logic."""

from types import SimpleNamespace

import pytest

from free_ai_model_router.models import ApiStyle, FreeStatus, VerificationStatus
from free_ai_model_router.providers.base import PricingRecord, ProviderModel, VerificationResult
from free_ai_model_router.providers.cerebras import CerebrasAdapter


def test_provider_model_defaults() -> None:
    pm = ProviderModel(provider_model_id="test/model")
    assert pm.provider_model_id == "test/model"
    assert pm.api_style == ApiStyle.OPENAI_COMPATIBLE
    assert pm.free_status == FreeStatus.UNKNOWN
    assert pm.tool_calling is False


def test_pricing_record() -> None:
    pr = PricingRecord(
        provider_model_id="test/model",
        free_input=True,
        free_output=True,
    )
    assert pr.free_input is True
    assert pr.free_output is True
    assert pr.input_price_per_million is None


def test_verification_result() -> None:
    vr = VerificationResult(
        provider_model_id="test/model",
        status=VerificationStatus.SUCCESS,
        latency_ms=150,
        http_status=200,
    )
    assert vr.status == VerificationStatus.SUCCESS
    assert vr.latency_ms == 150
    assert vr.tool_calling_verified is False


@pytest.mark.asyncio
async def test_cerebras_discover_models_filters_and_marks_free_models() -> None:
    class FakeHttpClient:
        async def fetch_json(self, *_args, **_kwargs):
            return {
                "data": [
                    {"id": "gpt-oss-120b", "context_length": 131072, "tool_calling": True},
                    {"id": "cerebras/whisper-large"},
                    {"id": "gemma-4-31b", "capabilities": {"tool_calling": True}},
                    {"id": "zai-glm-4.7", "supports_tool_calling": True},
                    {"id": "custom-chat", "capabilities": {"tool_calling": False}},
                ]
            }

    adapter = CerebrasAdapter(FakeHttpClient())

    models = await adapter.discover_models()

    assert [m.provider_model_id for m in models] == ["gpt-oss-120b", "gemma-4-31b", "zai-glm-4.7", "custom-chat"]
    assert models[0].free_status == FreeStatus.VERIFIED_FREE
    assert models[0].litellm_model == "cerebras/gpt-oss-120b"
    assert models[0].tool_calling is True
    assert models[1].tool_calling is True
    assert models[2].tool_calling is True
    assert models[3].free_status == FreeStatus.UNKNOWN


def test_cerebras_endpoint_and_litellm_string() -> None:
    adapter = CerebrasAdapter(SimpleNamespace())
    model = ProviderModel(provider_model_id="gpt-oss-120b", free_status=FreeStatus.VERIFIED_FREE)

    endpoint = adapter.to_provider_endpoint(model)

    assert endpoint.endpoint_id == "cerebras/gpt-oss-120b"
    assert endpoint.provider_id == "cerebras"
    assert adapter.to_litellm_model_string(model) == "cerebras/gpt-oss-120b"


@pytest.mark.asyncio
async def test_cerebras_verify_model_success(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeResponse:
        status_code = 200

    class FakeClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return None

        async def post(self, *_args, **_kwargs):
            return FakeResponse()

    monkeypatch.setattr("httpx.AsyncClient", lambda timeout: FakeClient())

    adapter = CerebrasAdapter(SimpleNamespace())
    result = await adapter.verify_model(ProviderModel(provider_model_id="gpt-oss-120b"), api_key="key")

    assert result.status == VerificationStatus.SUCCESS
    assert result.http_status == 200
