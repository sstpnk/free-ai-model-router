"""Tests for data models."""

from datetime import datetime, timezone

from free_ai_model_router.models import (
    CanonicalModel,
    FreeStatus,
    ProviderEndpoint,
    ModelRating,
    RouterOutput,
    RoutedEndpoint,
    QualityBand,
    ConfidenceLevel,
    ScoringMode,
)


def test_canonical_model_defaults() -> None:
    m = CanonicalModel(canonical_model_id="test/model", name="test")
    assert m.canonical_model_id == "test/model"
    assert m.name == "test"
    assert m.open_weights is False
    assert m.capabilities.coding is False


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


def test_model_rating_bands() -> None:
    r = ModelRating(canonical_model_id="test/model")
    assert r.quality_band == QualityBand.UNRATED
    assert r.ranking_confidence == ConfidenceLevel.LOW


def test_router_output() -> None:
    ep = RoutedEndpoint(
        endpoint_id="test/ep",
        provider_id="test",
        provider_name="Test",
        canonical_model_id="test/model",
        model_name="model-v1",
        final_score=85.0,
        quality_band=QualityBand.EXCELLENT,
        free_status=FreeStatus.VERIFIED_FREE,
        rank=1,
        is_primary=True,
    )
    output = RouterOutput(
        endpoints=[ep],
        fallback_chain=["test/ep"],
        scoring_mode=ScoringMode.COMPOSITE_PRIMARY,
    )
    assert len(output.endpoints) == 1
    assert output.endpoints[0].final_score == 85.0
    assert output.endpoints[0].is_primary is True


def test_sourced_value() -> None:
    from free_ai_model_router.models import SourcedValue, SourceType
    sv = SourcedValue(value=42, source_type=SourceType.OFFICIAL_API)
    assert sv.value == 42
    assert sv.source_type == SourceType.OFFICIAL_API
