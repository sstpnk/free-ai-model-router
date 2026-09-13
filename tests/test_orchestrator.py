"""Tests for pipeline orchestration wiring."""

from pathlib import Path
from types import SimpleNamespace

from free_ai_model_router.models import ApiStyle, ProviderConfig
from free_ai_model_router.pipeline.orchestrator import PipelineOrchestrator
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
