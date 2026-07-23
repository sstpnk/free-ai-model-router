"""Tests for LiteLLM config generation."""

from free_ai_model_router.models import (
    FreeStatus,
    Limits,
    ProviderEndpoint,
    RouterOutput,
    RoutedEndpoint,
)
from free_ai_model_router.generation.litellm_config import (
    generate_litellm_config,
)


def _sample_endpoint(ep_id: str, provider: str, model: str) -> ProviderEndpoint:
    return ProviderEndpoint(
        endpoint_id=ep_id,
        provider_id=provider,
        canonical_model_id=f"{provider}/{model}",
        provider_model_id=model,
        litellm_model=f"{provider}/{model}",
        api_base=f"https://api.{provider}.com/v1",
        free_status=FreeStatus.VERIFIED_FREE,
        limits=Limits(requests_per_day=1000),
    )


def _sample_routed(ep_id: str, provider: str, model: str) -> RoutedEndpoint:
    return RoutedEndpoint(
        endpoint_id=ep_id,
        provider_id=provider,
        provider_name=provider,
        canonical_model_id=f"{provider}/{model}",
        model_name=model,
        free_status=FreeStatus.VERIFIED_FREE,
        tool_calling=True,
        modalities=["text"],
    )


def test_generate_litellm_config() -> None:
    ep = _sample_endpoint("test/ep1", "test", "model-v1:free")
    routed = _sample_routed("test/ep1", "test", "model-v1:free")

    output = RouterOutput(
        endpoints=[routed],
        fallback_chain=["test/ep1"],
    )

    yaml_str = generate_litellm_config(output, {"test/ep1": ep})
    assert "model_list:" in yaml_str
    assert "coding-auto-1" in yaml_str
    assert "os.environ/TEST_API_KEY" in yaml_str
    assert "router_settings:" in yaml_str
    assert "fallbacks:" in yaml_str


def test_generate_litellm_config_shows_tools_and_modality() -> None:
    ep = _sample_endpoint("test/ep1", "test", "model-v1:free")
    routed = _sample_routed("test/ep1", "test", "model-v1:free")

    output = RouterOutput(endpoints=[routed], fallback_chain=["test/ep1"])
    yaml_str = generate_litellm_config(output, {"test/ep1": ep})
    assert "Tools:" in yaml_str
    assert "Modality:" in yaml_str
