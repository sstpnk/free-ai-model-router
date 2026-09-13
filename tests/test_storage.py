"""Tests for persisted pipeline artifacts."""

import json

from free_ai_model_router.models import AccessVerdict, ProviderEndpoint, VerificationStatus
from free_ai_model_router.storage.state import append_verification_history


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
