"""Tests for report generation."""

from free_ai_model_router.generation.reports import (
    generate_changes_report,
    generate_models_report,
    generate_provider_health_report,
    generate_throttled_report,
)
from free_ai_model_router.models import (
    AccessVerdict,
    FreeStatus,
    ProviderEndpoint,
    RoutedEndpoint,
    RouterOutput,
    VerificationStatus,
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


def test_provider_health_report_counts_statuses() -> None:
    usable = ProviderEndpoint(
        endpoint_id="test/usable",
        provider_id="test",
        canonical_model_id="test/usable",
        provider_model_id="usable",
    )
    usable.runtime_check.checked = True
    usable.runtime_check.status = VerificationStatus.SUCCESS
    usable.runtime_check.access_verdict = AccessVerdict.USABLE_NOW
    usable.runtime_check.latency_ms = 100

    throttled = ProviderEndpoint(
        endpoint_id="test/throttled",
        provider_id="test",
        canonical_model_id="test/throttled",
        provider_model_id="throttled",
    )
    throttled.runtime_check.checked = True
    throttled.runtime_check.status = VerificationStatus.RATE_LIMITED
    throttled.runtime_check.access_verdict = AccessVerdict.EXISTS_BUT_THROTTLED
    throttled.runtime_check.latency_ms = 300

    report = generate_provider_health_report([usable, throttled])

    assert "| test | 2 | 2 | 1 | 1 | 0 | 0 | 0 | 200 ms |" in report


def test_throttled_report_lists_rate_limited_and_quota() -> None:
    endpoint = ProviderEndpoint(
        endpoint_id="test/throttled",
        provider_id="test",
        canonical_model_id="test/throttled",
        provider_model_id="throttled",
    )
    endpoint.runtime_check.checked = True
    endpoint.runtime_check.status = VerificationStatus.RATE_LIMITED
    endpoint.runtime_check.access_verdict = AccessVerdict.EXISTS_BUT_THROTTLED
    endpoint.runtime_check.http_status = 429
    endpoint.runtime_check.retry_after_seconds = 9
    endpoint.runtime_check.checked_at = endpoint.discovered_at

    report = generate_throttled_report([endpoint])

    assert "throttled" in report
    assert "exists_but_throttled" in report
    assert "9s" in report
