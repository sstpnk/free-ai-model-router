"""Tests for persisted pipeline artifacts."""

import json
from datetime import datetime

from free_ai_model_router.models import (
    AccessVerdict,
    ProviderAccessRecord,
    ProviderEndpoint,
    VerificationStatus,
)
from free_ai_model_router.storage.state import (
    append_provider_access_history,
    append_verification_history,
    load_latest_provider_access_records,
    load_latest_verification_records,
    load_verification_stats,
)


def test_append_verification_history_writes_checked_records(tmp_path) -> None:
    endpoint = ProviderEndpoint(
        endpoint_id="test/model",
        provider_id="test",
        canonical_model_id="test/model",
        provider_model_id="model",
    )
    endpoint.runtime_check.checked = True
    endpoint.runtime_check.status = VerificationStatus.RATE_LIMITED
    endpoint.runtime_check.access_verdict = AccessVerdict.EXISTS_BUT_THROTTLED
    endpoint.runtime_check.http_status = 429
    endpoint.runtime_check.retry_after_seconds = 30
    endpoint.runtime_check.checked_at = endpoint.discovered_at
    endpoint.models_api_checked_at = endpoint.discovered_at
    endpoint.models_api_source_url = "https://api.test/v1/models"

    unchecked = ProviderEndpoint(
        endpoint_id="test/unchecked",
        provider_id="test",
        canonical_model_id="test/unchecked",
        provider_model_id="unchecked",
    )

    path = tmp_path / "history" / "verification.jsonl"
    written = append_verification_history(
        endpoints=[endpoint, unchecked],
        run_id="run-1",
        path=path,
    )

    assert written == 1
    lines = path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    record = json.loads(lines[0])
    assert record["run_id"] == "run-1"
    assert record["endpoint_id"] == "test/model"
    assert record["status"] == "rate_limited"
    assert record["access_verdict"] == "exists_but_throttled"
    assert record["retry_after_seconds"] == 30
    assert datetime.fromisoformat(record["models_api_checked_at"]) == endpoint.discovered_at
    assert record["models_api_source_url"] == "https://api.test/v1/models"


def test_append_verification_history_filters_old_records(tmp_path) -> None:
    endpoint = ProviderEndpoint(
        endpoint_id="test/model",
        provider_id="test",
        canonical_model_id="test/model",
        provider_model_id="model",
    )
    endpoint.runtime_check.checked = True
    endpoint.runtime_check.status = VerificationStatus.SUCCESS
    endpoint.runtime_check.access_verdict = AccessVerdict.USABLE_NOW
    endpoint.runtime_check.checked_at = endpoint.discovered_at

    path = tmp_path / "history" / "verification.jsonl"
    written = append_verification_history(
        endpoints=[endpoint],
        run_id="run-1",
        path=path,
        checked_after=endpoint.discovered_at.replace(year=endpoint.discovered_at.year + 1),
    )

    assert written == 0
    assert not path.exists()


def test_load_latest_verification_records_uses_newest_record(tmp_path) -> None:
    first = ProviderEndpoint(
        endpoint_id="test/model",
        provider_id="test",
        canonical_model_id="test/model",
        provider_model_id="model",
    )
    first.runtime_check.checked = True
    first.runtime_check.status = VerificationStatus.RATE_LIMITED
    first.runtime_check.access_verdict = AccessVerdict.EXISTS_BUT_THROTTLED
    first.runtime_check.checked_at = first.discovered_at

    second = ProviderEndpoint(
        endpoint_id="test/model",
        provider_id="test",
        canonical_model_id="test/model",
        provider_model_id="model",
    )
    second.runtime_check.checked = True
    second.runtime_check.status = VerificationStatus.SUCCESS
    second.runtime_check.access_verdict = AccessVerdict.USABLE_NOW
    second.runtime_check.checked_at = first.discovered_at.replace(year=first.discovered_at.year + 1)

    path = tmp_path / "history" / "verification.jsonl"
    append_verification_history(endpoints=[first], run_id="run-1", path=path)
    append_verification_history(endpoints=[second], run_id="run-2", path=path)

    latest = load_latest_verification_records(path)

    assert latest["test/model"].run_id == "run-2"
    assert latest["test/model"].status == VerificationStatus.SUCCESS


def test_load_latest_verification_records_normalizes_client_restricted_history(tmp_path) -> None:
    path = tmp_path / "history" / "verification.jsonl"
    path.parent.mkdir(parents=True)
    path.write_text(
        json.dumps(
            {
                "run_id": "run-1",
                "checked_at": "2026-01-01T00:00:00+00:00",
                "endpoint_id": "opencode/free",
                "provider_id": "opencode",
                "canonical_model_id": "opencode/free",
                "provider_model_id": "free",
                "status": "authentication_failed",
                "access_verdict": "not_accessible",
                "http_status": 403,
                "error_message": (
                    '{"error":{"type":"FreeTierError",'
                    '"message":"free tier can only be used from within OpenCode"}}'
                ),
            }
        )
        + "\n",
        encoding="utf-8",
    )

    latest = load_latest_verification_records(path)

    assert latest["opencode/free"].status == VerificationStatus.CLIENT_RESTRICTED
    assert latest["opencode/free"].access_verdict == AccessVerdict.NOT_ACCESSIBLE


def test_provider_access_history_keeps_latest_record(tmp_path) -> None:
    path = tmp_path / "history" / "provider-access.jsonl"
    first = ProviderAccessRecord(
        run_id="run-1",
        checked_at=datetime.fromisoformat("2026-01-01T00:00:00+00:00"),
        provider_id="test",
        api_key_present=True,
        models_api_checked=True,
        models_api_status=VerificationStatus.AUTHENTICATION_FAILED,
        error_message="HTTP 403",
    )
    second = ProviderAccessRecord(
        run_id="run-2",
        checked_at=datetime.fromisoformat("2026-01-02T00:00:00+00:00"),
        provider_id="test",
        api_key_present=True,
        models_api_checked=True,
        models_api_status=VerificationStatus.SUCCESS,
        models_found=2,
    )

    assert append_provider_access_history(records=[first, second], path=path) == 2

    latest = load_latest_provider_access_records(path)

    assert latest["test"].run_id == "run-2"
    assert latest["test"].models_api_status == VerificationStatus.SUCCESS
    assert latest["test"].models_found == 2


def test_load_verification_stats_aggregates_endpoint_history(tmp_path) -> None:
    success = ProviderEndpoint(
        endpoint_id="test/model",
        provider_id="test",
        canonical_model_id="test/model",
        provider_model_id="model",
    )
    success.runtime_check.checked = True
    success.runtime_check.status = VerificationStatus.SUCCESS
    success.runtime_check.access_verdict = AccessVerdict.USABLE_NOW
    success.runtime_check.latency_ms = 100
    success.runtime_check.checked_at = success.discovered_at

    limited = ProviderEndpoint(
        endpoint_id="test/model",
        provider_id="test",
        canonical_model_id="test/model",
        provider_model_id="model",
    )
    limited.runtime_check.checked = True
    limited.runtime_check.status = VerificationStatus.RATE_LIMITED
    limited.runtime_check.access_verdict = AccessVerdict.EXISTS_BUT_THROTTLED
    limited.runtime_check.latency_ms = 300
    limited.runtime_check.checked_at = success.discovered_at.replace(year=success.discovered_at.year + 1)

    path = tmp_path / "history" / "verification.jsonl"
    append_verification_history(endpoints=[success], run_id="run-1", path=path)
    append_verification_history(endpoints=[limited], run_id="run-2", path=path)

    stats = load_verification_stats(path)

    assert stats["test/model"].attempts == 2
    assert stats["test/model"].success_count == 1
    assert stats["test/model"].rate_limited_count == 1
    assert stats["test/model"].success_rate == 0.5
    assert stats["test/model"].last_success_at == success.discovered_at
    assert stats["test/model"].p50_latency_ms == 100
    assert stats["test/model"].p95_latency_ms == 300
