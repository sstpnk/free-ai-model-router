"""Tests for report generation."""

from free_ai_model_router.models import (
    CanonicalModel,
    FreeStatus,
    ModelRating,
    ProviderEndpoint,
    QualityBand,
    RouterOutput,
    RoutedEndpoint,
    ScoringMode,
)
from free_ai_model_router.generation.reports import (
    generate_models_report,
    generate_changes_report,
    generate_sources_health_report,
)


def _sample_router_output() -> RouterOutput:
    ep = RoutedEndpoint(
        endpoint_id="test/ep",
        provider_id="test",
        provider_name="TestProvider",
        canonical_model_id="test/model",
        model_name="test-v1",
        final_score=88.0,
        quality_band=QualityBand.EXCELLENT,
        free_status=FreeStatus.VERIFIED_FREE,
        rank=1,
        is_primary=True,
    )
    return RouterOutput(
        endpoints=[ep],
        fallback_chain=["test/ep"],
        scoring_mode=ScoringMode.COMPOSITE_PRIMARY,
    )


def test_models_report_generated() -> None:
    output = _sample_router_output()
    rating = ModelRating(canonical_model_id="test/model")
    endpoint = ProviderEndpoint(
        endpoint_id="test/ep",
        provider_id="test",
        canonical_model_id="test/model",
        provider_model_id="test-v1",
    )
    report = generate_models_report(output, [rating], [endpoint])
    assert "TestProvider" in report
    assert "88.0" in report
    assert "Free AI Model Router" in report


def test_changes_report_no_changes() -> None:
    output = _sample_router_output()
    report = generate_changes_report(output, output, [])
    assert "Изменений" in report


def test_sources_health_report() -> None:
    from free_ai_model_router.models import SourceHealth
    health = {
        "test_source": SourceHealth(source_id="test_source", consecutive_failures=0),
    }
    report = generate_sources_health_report(health)
    assert "test_source" in report
