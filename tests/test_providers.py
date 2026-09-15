"""Tests for provider adapters — zero-network unit tests for conversion logic."""

import os
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from free_ai_model_router.models import ApiStyle, FreeStatus, Modality, ProviderConfig, VerificationStatus
from free_ai_model_router.providers.base import PricingRecord, ProviderModel, VerificationResult
from free_ai_model_router.providers.cerebras import CerebrasAdapter
from free_ai_model_router.providers.cloudflare import (
    CloudflareAdapter,
    _get_modalities,
    _infer_task_type,
)
from free_ai_model_router.providers.deepinfra import DeepInfraAdapter, _extract_json_array_objects
from free_ai_model_router.providers.openai_compatible import GenericOpenAICompatibleAdapter


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
async def test_deepinfra_discover_models_from_catalog_list() -> None:
    class FakeDeepInfraAdapter(DeepInfraAdapter):
        async def _fetch_catalog(self, _headers):
            return [
                {
                    "model_name": "deepseek-ai/DeepSeek-V3",
                    "reported_type": "text-generation",
                    "max_tokens": 163840,
                },
                {
                    "model_name": "BAAI/bge-large-en-v1.5",
                    "reported_type": "sentence-similarity",
                },
                {
                    "model_name": "black-forest-labs/FLUX-1-schnell",
                    "reported_type": "text-to-image",
                },
            ]

    adapter = FakeDeepInfraAdapter(SimpleNamespace(), api_key="key")

    models = await adapter.discover_models()

    assert [m.provider_model_id for m in models] == ["deepseek-ai/DeepSeek-V3"]
    assert models[0].api_base == "https://api.deepinfra.com/v1/openai"
    assert models[0].context_tokens == 163840


def test_deepinfra_endpoint_and_litellm_string() -> None:
    adapter = DeepInfraAdapter(SimpleNamespace())
    model = ProviderModel(provider_model_id="deepseek-ai/DeepSeek-V3")

    endpoint = adapter.to_provider_endpoint(model)

    assert endpoint.endpoint_id == "deepinfra/deepseek-ai/DeepSeek-V3"
    assert endpoint.provider_id == "deepinfra"
    assert endpoint.source_url == "https://api.deepinfra.com/models/list"
    assert adapter.to_litellm_model_string(model) == "deepinfra/deepseek-ai/DeepSeek-V3"


def test_deepinfra_extracts_objects_from_partial_catalog_stream() -> None:
    chunks = [
        b'[{"model_name":"a","reported_type":"text-generation"},',
        b'{"model_name":"b","reported_type":"text-generation"},',
        b'{"model_name":"unfinished","reported_type":"text',
    ]

    parsed = _extract_json_array_objects(chunks, max_objects=10)

    assert [item["model_name"] for item in parsed] == ["a", "b"]


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


# ─── Cloudflare Workers AI ────────────────────────────────────────────────


def test_infer_task_type_text_generation() -> None:
    assert _infer_task_type("@cf/meta/llama-3.1-8b-instruct") == "text-generation"
    assert _infer_task_type("@cf/qwen/qwen2.5-coder-32b-instruct") == "text-generation"
    assert _infer_task_type("@cf/google/gemma-4-26b-a4b-it") == "text-generation"


def test_infer_task_type_text_to_image() -> None:
    assert _infer_task_type("@cf/black-forest-labs/flux-1-schnell") == "text-to-image"
    assert _infer_task_type("@cf/lykon/dreamshaper-8-lcm") == "text-to-image"


def test_infer_task_type_audio() -> None:
    assert _infer_task_type("@cf/openai/whisper") == "automatic-speech-recognition"
    assert _infer_task_type("@cf/deepgram/aura") == "text-to-speech"


def test_infer_task_type_embeddings() -> None:
    assert _infer_task_type("@cf/baai/bge-base-en-v1.5") == "text-embeddings"


def test_infer_task_type_image_analysis() -> None:
    assert _infer_task_type("@cf/meta/detr-resnet-50") == "object-detection"
    assert _infer_task_type("@cf/huggingface/distilbert-sst-2-int8") == "text-classification"
    assert _infer_task_type("@cf/unum/uform-gen2-qwen-500m") == "image-to-text"


def test_get_modalities() -> None:
    assert _get_modalities("text-generation") == [Modality.TEXT]
    assert _get_modalities("text-to-image") == [Modality.IMAGE_GENERATION]
    assert _get_modalities("text-to-speech") == [Modality.AUDIO_GENERATION]
    assert _get_modalities("automatic-speech-recognition") == [Modality.AUDIO_ANALYSIS]
    assert _get_modalities("image-to-text") == [Modality.IMAGE_ANALYSIS]
    assert _get_modalities("unknown-task") == [Modality.TEXT]


def test_cloudflare_missing_account_id_returns_empty(monkeypatch: pytest.MonkeyPatch) -> None:
    """Without CLOUDFLARE_ACCOUNT_ID, discover_models returns []."""
    monkeypatch.delenv("CLOUDFLARE_ACCOUNT_ID", raising=False)
    adapter = CloudflareAdapter(SimpleNamespace(), api_key="test-key")
    import asyncio
    models = asyncio.run(adapter.discover_models())
    assert models == []


@pytest.mark.asyncio
async def test_cloudflare_discover_filters_to_cf_models() -> None:
    """Only @cf/ models are returned; @hf/, @https:// etc. are excluded."""
    fake_response = {
        "success": True,
        "result": {
            "models": [
                {
                    "id": "@cf/meta/llama-3.1-8b-instruct",
                    "name": "Llama 3.1 8B Instruct",
                    "task": {"id": "text-generation", "name": "Text Generation"},
                    "capabilities": ["function-calling"],
                },
                {
                    "id": "@cf/black-forest-labs/flux-1-schnell",
                    "name": "FLUX.1 Schnell",
                    "task": {"id": "text-to-image", "name": "Text-to-Image"},
                },
                {
                    "id": "@hf/thebloke/mistral-7b-instruct-awq",
                    "name": "Mistral 7B (AWQ)",
                    "task": {"id": "text-generation", "name": "Text Generation"},
                },
                {
                    "id": "@cf/deepgram/aura-2-en",
                    "name": "Aura 2 English",
                    "task": {"id": "text-to-speech", "name": "Text-to-Speech"},
                },
                {
                    "id": "@cf/baai/bge-base-en-v1.5",
                    "name": "BGE Base EN v1.5",
                    "task": {"id": "text-embeddings", "name": "Text Embeddings"},
                    "properties": {"context_length": 512},
                },
            ],
        },
    }

    class FakeHttp:
        async def fetch_json(self, *_a, **_kw):
            return fake_response

    with patch.dict(os.environ, {"CLOUDFLARE_ACCOUNT_ID": "test-account"}):
        adapter = CloudflareAdapter(FakeHttp(), api_key="test-key")
        models = await adapter.discover_models()

    # Only 4 @cf/ models (hf one excluded)
    assert len(models) == 4
    ids = [m.provider_model_id for m in models]
    assert "@cf/meta/llama-3.1-8b-instruct" in ids
    assert "@cf/black-forest-labs/flux-1-schnell" in ids
    assert "@cf/deepgram/aura-2-en" in ids
    assert "@cf/baai/bge-base-en-v1.5" in ids
    assert "@hf/thebloke/mistral-7b-instruct-awq" not in ids

    # Check modalities
    for m in models:
        if "llama" in m.provider_model_id:
            assert m.modalities == [Modality.TEXT]
            assert m.tool_calling is True
        elif "flux" in m.provider_model_id:
            assert m.modalities == [Modality.IMAGE_GENERATION]
        elif "aura" in m.provider_model_id:
            assert m.modalities == [Modality.AUDIO_GENERATION]
        elif "bge" in m.provider_model_id:
            assert m.modalities == [Modality.TEXT]
            assert m.context_tokens == 512

    # All should be DOCUMENTED_FREE
    assert all(m.free_status == FreeStatus.DOCUMENTED_FREE for m in models)

    # Check daily neuron limit
    for m in models:
        assert m.limits.requests_per_day == 10_000


@pytest.mark.asyncio
async def test_cloudflare_discover_fallback_task_heuristics() -> None:
    """When API doesn't provide a task, model-name heuristics kick in."""
    fake_no_task = {
        "success": True,
        "result": {
            "models": [
                {"id": "@cf/lykon/dreamshaper-8-lcm", "name": "Dreamshaper"},
                {"id": "@cf/meta/llama-3.2-3b-instruct", "name": "Llama 3.2"},
            ],
        },
    }

    class FakeHttp:
        async def fetch_json(self, *_a, **_kw):
            return fake_no_task

    with patch.dict(os.environ, {"CLOUDFLARE_ACCOUNT_ID": "test-account"}):
        adapter = CloudflareAdapter(FakeHttp(), api_key="test-key")
        models = await adapter.discover_models()

    assert len(models) == 2
    by_id = {m.provider_model_id: m for m in models}
    assert by_id["@cf/lykon/dreamshaper-8-lcm"].modalities == [Modality.IMAGE_GENERATION]
    assert by_id["@cf/meta/llama-3.2-3b-instruct"].modalities == [Modality.TEXT]


def test_cloudflare_endpoint_and_litellm_string() -> None:
    adapter = CloudflareAdapter(SimpleNamespace())
    model = ProviderModel(
        provider_model_id="@cf/meta/llama-3.1-8b-instruct",
        free_status=FreeStatus.DOCUMENTED_FREE,
        api_base="https://api.cloudflare.com/client/v4/accounts/test/ai/v1",
    )
    ep = adapter.to_provider_endpoint(model)
    assert ep.endpoint_id == "cloudflare/@cf/meta/llama-3.1-8b-instruct"
    assert ep.provider_id == "cloudflare"
    assert adapter.to_litellm_model_string(model) == "cloudflare/@cf/meta/llama-3.1-8b-instruct"


@pytest.mark.asyncio
async def test_cloudflare_verify_model_success(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeResponse:
        status_code = 200

    class FakeHttpxClient:
        async def __aenter__(self):
            return self
        async def __aexit__(self, *args):
            return None
        async def post(self, *_args, **_kwargs):
            return FakeResponse()

    monkeypatch.setattr("httpx.AsyncClient", lambda timeout=None, **kw: FakeHttpxClient())

    with patch.dict(os.environ, {"CLOUDFLARE_ACCOUNT_ID": "test-account"}):
        adapter = CloudflareAdapter(SimpleNamespace())
        result = await adapter.verify_model(
            ProviderModel(provider_model_id="@cf/meta/llama-3.1-8b-instruct"),
            api_key="test-key",
        )
    assert result.status == VerificationStatus.SUCCESS
    assert result.http_status == 200


@pytest.mark.asyncio
async def test_cloudflare_fetch_pricing_and_limits() -> None:
    adapter = CloudflareAdapter(SimpleNamespace())
    pricing = await adapter.fetch_pricing()
    assert len(pricing) == 1
    assert pricing[0].trial_credit is True

    limits = await adapter.fetch_limits()
    assert len(limits) == 1
    assert limits[0].requests_per_day == 10_000


# ─── Generic OpenAI-Compatible Adapter ───────────────────────────────────────


def _generic_provider_config() -> ProviderConfig:
    return ProviderConfig(
        provider_id="generic",
        name="Generic",
        api_base="https://api.generic.test/v1",
        api_style=ApiStyle.OPENAI_COMPATIBLE,
        sources={"models_api": "https://api.generic.test/v1/models"},
    )


@pytest.mark.asyncio
async def test_generic_openai_compatible_discover_models() -> None:
    class FakeHttp:
        async def fetch_json(self, *_args, **_kwargs):
            return {
                "data": [
                    {"id": "chat-free:free", "context_length": 8192, "tool_calling": True},
                    {"id": "text-embedding-3-small"},
                ]
            }

    adapter = GenericOpenAICompatibleAdapter(FakeHttp(), _generic_provider_config())

    models = await adapter.discover_models()

    assert [m.provider_model_id for m in models] == ["chat-free:free"]
    assert models[0].free_status == FreeStatus.VERIFIED_FREE
    assert models[0].tool_calling is True
    assert models[0].context_tokens == 8192


@pytest.mark.asyncio
async def test_generic_openai_compatible_verify_rate_limited(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeResponse:
        status_code = 429
        text = '{"error":"rate limit exceeded"}'
        headers = {"Retry-After": "12"}

    class FakeHttpxClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return None

        async def post(self, *_args, **_kwargs):
            return FakeResponse()

    monkeypatch.setattr("httpx.AsyncClient", lambda timeout=None, **_kw: FakeHttpxClient())

    adapter = GenericOpenAICompatibleAdapter(SimpleNamespace(), _generic_provider_config())
    result = await adapter.verify_model(
        ProviderModel(provider_model_id="chat-free:free", api_base="https://api.generic.test/v1"),
        api_key="key",
    )

    assert result.status == VerificationStatus.RATE_LIMITED
    assert result.http_status == 429
    assert result.retry_after_seconds == 12
