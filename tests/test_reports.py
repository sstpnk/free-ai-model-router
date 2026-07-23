"""Tests for report generation."""

from free_ai_model_router.models import (
    FreeStatus,
    ProviderEndpoint,
    RouterOutput,
    RoutedEndpoint,
)
from free_ai_model_router.generation.reports import (
    generate_models_report,
    generate_changes_report,
)


def _sample_router_output() -> RouterOutput:
    ep = RoutedEndpoint(
        endpoint_id="test/ep",
        provider_id="test",
        provider_name="TestProvider",
        canonical_model_id="test/model",
        model_name="test-v1:free",
        free_status=FreeStatus.VERIFIED_FREE,
        tool_calling=True,
        modalities=["text"],
    )
    return RouterOutput(
        endpoints=[ep],
        fallback_chain=["test/ep"],
    )


def test_models_report_generated() -> None:
    output = _sample_router_output()
    endpoint = ProviderEndpoint(
        endpoint_id="test/ep",
        provider_id="test",
        canonical_model_id="test/model",
        provider_model_id="test-v1:free",
    )
    report = generate_models_report(output, [endpoint])
    assert "TestProvider" in report
    assert "test-v1:free" in report
    assert "Free AI Model Router" in report
    assert "✓" in report  # tool_calling indicator


def test_changes_report_no_changes() -> None:
    output = _sample_router_output()
    report = generate_changes_report(output, output, [])
    assert "Изменений" in report
