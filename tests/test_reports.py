"""Tests for report generation."""

from free_ai_model_router.generation.reports import (
    generate_and_write_reports,
    generate_changes_report,
    generate_history_summary_report,
    generate_models_report,
    generate_provider_access_report,
    generate_provider_health_report,
    generate_throttled_report,
)
from free_ai_model_router.models import (
    AccessVerdict,
    ApiStyle,
    FreeStatus,
    ProviderAccessRecord,
    ProviderConfig,
    ProviderEndpoint,
    RoutedEndpoint,
    RouterOutput,
    VerificationStats,
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
    assert "Listed" in report
    assert "assumed" in report
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


def test_provider_access_report_shows_key_and_working_statuses() -> None:
    providers = [
        ProviderConfig(
            provider_id="working",
            name="Working Provider",
            api_style=ApiStyle.OPENAI_COMPATIBLE,
            discovery_priority=1,
        ),
        ProviderConfig(
            provider_id="missing",
            name="Missing Key Provider",
            api_style=ApiStyle.OPENAI_COMPATIBLE,
            discovery_priority=2,
        ),
        ProviderConfig(
            provider_id="keyless",
            name="Keyless Provider",
            api_style=ApiStyle.OPENAI_COMPATIBLE,
            api_key_required=False,
            discovery_priority=3,
        ),
        ProviderConfig(
            provider_id="badkey",
            name="Bad Key Provider",
            api_style=ApiStyle.OPENAI_COMPATIBLE,
            discovery_priority=4,
        ),
    ]
    working = ProviderEndpoint(
        endpoint_id="working/model",
        provider_id="working",
        canonical_model_id="working/model",
        provider_model_id="model",
    )
    working.runtime_check.checked = True
    working.runtime_check.status = VerificationStatus.SUCCESS
    badkey = ProviderEndpoint(
        endpoint_id="badkey/model",
        provider_id="badkey",
        canonical_model_id="badkey/model",
        provider_model_id="model",
    )
    badkey.runtime_check.checked = True
    badkey.runtime_check.status = VerificationStatus.AUTHENTICATION_FAILED

    report = generate_provider_access_report(
        providers=providers,
        endpoints=[working, badkey],
        api_key_presence={"working": True, "badkey": True},
        provider_errors={"badkey": "HTTP 403 Forbidden"},
        provider_access_records={
            "working": ProviderAccessRecord(
                run_id="run-1",
                checked_at=working.discovered_at,
                provider_id="working",
                api_key_present=True,
                models_api_checked=True,
                models_api_status=VerificationStatus.SUCCESS,
                models_found=2,
            )
        },
    )

    assert "подключен и работает" in report
    assert "success (2)" in report
    assert "ключ не добавлен" in report
    assert "ключ не требуется" in report
    assert "ошибка доступа/ключа" in report
    assert "HTTP 403 Forbidden" in report


def test_history_summary_report_includes_reliability_metrics() -> None:
    endpoint = ProviderEndpoint(
        endpoint_id="test/model",
        provider_id="test",
        canonical_model_id="test/model",
        provider_model_id="model",
    )
    stats = VerificationStats(
        endpoint_id="test/model",
        attempts=4,
        success_count=3,
        success_rate=0.75,
        rate_limited_count=1,
        p50_latency_ms=100,
        p95_latency_ms=250,
    )

    report = generate_history_summary_report(
        endpoints=[endpoint],
        verification_stats={"test/model": stats},
    )

    assert "75%" in report
    assert "| test | model | 4 |" in report
    assert "| 1 | 0 | 0 | 100 | 250 |" in report


def test_provider_access_report_uses_historical_runtime_statuses() -> None:
    provider = ProviderConfig(
        provider_id="limited",
        name="Limited Provider",
        api_style=ApiStyle.OPENAI_COMPATIBLE,
    )

    report = generate_provider_access_report(
        providers=[provider],
        endpoints=[],
        api_key_presence={"limited": True},
        provider_runtime_statuses={"limited": [VerificationStatus.RATE_LIMITED]},
    )

    assert "подключен, но лимит" in report
    assert "| limited | Limited Provider | подключен, но лимит | добавлен | — | 1 | 0 | 0 | 1 |" in report


def test_provider_access_report_distinguishes_quota_from_rate_limit() -> None:
    provider = ProviderConfig(
        provider_id="quota",
        name="Quota Provider",
        api_style=ApiStyle.OPENAI_COMPATIBLE,
    )

    report = generate_provider_access_report(
        providers=[provider],
        endpoints=[],
        api_key_presence={"quota": True},
        provider_runtime_statuses={"quota": [VerificationStatus.QUOTA_EXHAUSTED]},
    )

    assert "требуется баланс/квота" in report
    assert "генерация требует баланс" in report


def test_status_reports_can_skip_routing_reports(tmp_path) -> None:
    output = _sample_router_output()

    generate_and_write_reports(
        router_output=output,
        endpoints=[],
        changes=[],
        previous_output=None,
        reports_dir=tmp_path,
        providers=[],
        write_routing_reports=False,
    )

    assert not (tmp_path / "models.md").exists()
    assert not (tmp_path / "changes.md").exists()
    assert (tmp_path / "provider-health.md").exists()
