"""Tests for data models."""

from datetime import datetime, timezone

from free_ai_model_router.models import (
    CanonicalModel,
    FreeStatus,
    Modality,
    ProviderEndpoint,
    RouterOutput,
    RoutedEndpoint,
)


def test_canonical_model_defaults() -> None:
    m = CanonicalModel(canonical_model_id="test/model", name="test")
    assert m.canonical_model_id == "test/model"
    assert m.name == "test"
    assert m.open_weights is False
    assert m.capabilities.tool_calling is False
    assert Modality.TEXT in m.capabilities.modalities


def test_provider_endpoint_defaults() -> None:
    ep = ProviderEndpoint(
        endpoint_id="test/endpoint",
        provider_id="test",
        canonical_model_id="test/model",
        provider_model_id="model-v1",
    )
    assert ep.free_status == FreeStatus.UNKNOWN
    assert ep.runtime_check.checked is False
    assert ep.runtime_check.status.value == "not_tested"


def test_router_output() -> None:
    ep = RoutedEndpoint(
        endpoint_id="test/ep",
        provider_id="test",
        provider_name="Test",
        canonical_model_id="test/model",
        model_name="model-v1",
        free_status=FreeStatus.VERIFIED_FREE,
        tool_calling=True,
        modalities=["text"],
    )
    output = RouterOutput(
        endpoints=[ep],
        fallback_chain=["test/ep"],
    )
    assert len(output.endpoints) == 1
    assert output.endpoints[0].tool_calling is True
    assert "text" in output.endpoints[0].modalities


def test_modality_enum() -> None:
    assert Modality.TEXT.value == "text"
    assert Modality.IMAGE_ANALYSIS.value == "image_analysis"
    assert Modality.IMAGE_GENERATION.value == "image_generation"
    assert Modality.AUDIO_ANALYSIS.value == "audio_analysis"
    assert Modality.AUDIO_GENERATION.value == "audio_generation"
    assert Modality.VIDEO_ANALYSIS.value == "video_analysis"
    assert Modality.VIDEO_GENERATION.value == "video_generation"
