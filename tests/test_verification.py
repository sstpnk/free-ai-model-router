"""Tests for verification status interpretation."""

from datetime import UTC, datetime

from free_ai_model_router.generation.reports import generate_models_report
from free_ai_model_router.models import (
    AccessVerdict,
    FreeStatus,
    ProviderEndpoint,
    RoutedEndpoint,
    RouterOutput,
    VerificationStatus,
)
from free_ai_model_router.verification.status import (
    access_verdict_for_status,
    classify_http_status,
    is_evidence_status,
    is_routable_status,
    parse_retry_after_seconds,
)


def test_rate_limit_is_endpoint_evidence_not_unavailable() -> None:
    status = classify_http_status(429, '{"error":"rate limit exceeded"}')

    assert status == VerificationStatus.RATE_LIMITED
    assert access_verdict_for_status(status) == AccessVerdict.EXISTS_BUT_THROTTLED
    assert is_evidence_status(status) is True
    assert is_routable_status(status) is True


def test_quota_exhaustion_has_account_specific_verdict() -> None:
    status = classify_http_status(429, '{"error":"quota exceeded"}')

    assert status == VerificationStatus.QUOTA_EXHAUSTED
    assert access_verdict_for_status(status) == AccessVerdict.QUOTA_EXHAUSTED_FOR_ACCOUNT
    assert is_evidence_status(status) is True
    assert is_routable_status(status) is False


def test_model_not_found_is_not_routable() -> None:
    status = classify_http_status(404, "model not found")

    assert status == VerificationStatus.MODEL_NOT_FOUND
    assert access_verdict_for_status(status) == AccessVerdict.NOT_ACCESSIBLE
    assert is_routable_status(status) is False


def test_retry_after_delta_seconds() -> None:
    assert parse_retry_after_seconds({"Retry-After": "17"}) == 17


def test_models_report_keeps_throttled_endpoint_visible() -> None:
    endpoint = ProviderEndpoint(
        endpoint_id="test/model",
        provider_id="test",
        canonical_model_id="test/model",
        provider_model_id="model",
        free_status=FreeStatus.VERIFIED_FREE,
    )
    endpoint.runtime_check.checked = True
    endpoint.runtime_check.status = VerificationStatus.RATE_LIMITED
    endpoint.runtime_check.access_verdict = AccessVerdict.EXISTS_BUT_THROTTLED
    endpoint.runtime_check.checked_at = datetime.now(UTC)
    endpoint.runtime_check.http_status = 429
    endpoint.runtime_check.retry_after_seconds = 10

    output = RouterOutput(
        endpoints=[
            RoutedEndpoint(
                endpoint_id="test/model",
                provider_id="test",
                provider_name="test",
                canonical_model_id="test/model",
                model_name="model",
                free_status=FreeStatus.VERIFIED_FREE,
                runtime_status=VerificationStatus.RATE_LIMITED,
                access_verdict=AccessVerdict.EXISTS_BUT_THROTTLED,
            )
        ],
        fallback_chain=["test/model"],
    )

    report = generate_models_report(output, [endpoint])

    assert "exists_but_throttled" in report
    assert "rate_limited" in report
    assert "10s" in report
