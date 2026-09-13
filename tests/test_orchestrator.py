"""Tests for pipeline orchestration wiring."""

import asyncio
from pathlib import Path
from types import SimpleNamespace

from free_ai_model_router.models import ApiStyle, ProviderConfig, ProviderEndpoint, VerificationStatus
from free_ai_model_router.pipeline.orchestrator import PipelineOrchestrator
from free_ai_model_router.providers.base import VerificationResult
from free_ai_model_router.providers.openai_compatible import GenericOpenAICompatibleAdapter


def test_init_adapters_uses_generic_openai_compatible_for_null_adapter(tmp_path: Path) -> None:
    provider = ProviderConfig(
        provider_id="generic",
        name="Generic",
        api_base="https://api.generic.test/v1",
        api_style=ApiStyle.OPENAI_COMPATIBLE,
        adapter=None,
    )
    settings = SimpleNamespace(
        providers=SimpleNamespace(providers=[provider]),
        get_provider_api_key=lambda _provider_id: None,
    )
    orchestrator = PipelineOrchestrator(settings, tmp_path)
    orchestrator.http = SimpleNamespace()

    adapters = orchestrator._init_adapters()

    assert len(adapters) == 1
    assert isinstance(adapters[0], GenericOpenAICompatibleAdapter)


def test_init_adapters_filters_by_provider_id(tmp_path: Path) -> None:
    providers = [
        ProviderConfig(
            provider_id="first",
            name="First",
            api_base="https://api.first.test/v1",
            api_style=ApiStyle.OPENAI_COMPATIBLE,
            adapter=None,
        ),
        ProviderConfig(
            provider_id="second",
            name="Second",
            api_base="https://api.second.test/v1",
            api_style=ApiStyle.OPENAI_COMPATIBLE,
            adapter=None,
        ),
    ]
    settings = SimpleNamespace(
        providers=SimpleNamespace(providers=providers),
        get_provider_api_key=lambda _provider_id: None,
    )
    orchestrator = PipelineOrchestrator(settings, tmp_path)
    orchestrator.http = SimpleNamespace()

    adapters = orchestrator._init_adapters({"second"})

    assert len(adapters) == 1
    assert adapters[0].provider_id == "second"


def test_verify_models_filters_by_provider_id(tmp_path: Path) -> None:
    class FakeAdapter:
        provider_id = "wanted"

        async def verify_model(self, model, api_key: str) -> VerificationResult:
            return VerificationResult(
                provider_model_id=model.provider_model_id,
                status=VerificationStatus.SUCCESS,
            )

    settings = SimpleNamespace(
        history_dir=tmp_path / "history",
        providers=SimpleNamespace(providers=[]),
        get_provider_api_key=lambda provider_id: "key" if provider_id == "wanted" else None,
    )
    orchestrator = PipelineOrchestrator(settings, tmp_path)
    orchestrator.http = SimpleNamespace()
    orchestrator._init_adapters = lambda _provider_ids=None: [FakeAdapter()]
    wanted = ProviderEndpoint(
        endpoint_id="wanted/model",
        provider_id="wanted",
        canonical_model_id="wanted/model",
        provider_model_id="model",
    )
    limited_out = ProviderEndpoint(
        endpoint_id="wanted/model-2",
        provider_id="wanted",
        canonical_model_id="wanted/model-2",
        provider_model_id="model-2",
    )
    skipped = ProviderEndpoint(
        endpoint_id="skipped/model",
        provider_id="skipped",
        canonical_model_id="skipped/model",
        provider_model_id="model",
    )
    orchestrator.collected_endpoints = [wanted, limited_out, skipped]

    asyncio.run(orchestrator._verify_models({"wanted"}, max_probes=1))

    assert wanted.runtime_check.status == VerificationStatus.SUCCESS
    assert limited_out.runtime_check.status == VerificationStatus.NOT_TESTED
    assert skipped.runtime_check.status == VerificationStatus.NOT_TESTED
