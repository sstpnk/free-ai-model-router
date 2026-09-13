"""Shared interpretation of provider verification responses."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime

from free_ai_model_router.models import AccessVerdict, VerificationStatus

EVIDENCE_STATUSES = {
    VerificationStatus.SUCCESS,
    VerificationStatus.RATE_LIMITED,
    VerificationStatus.QUOTA_EXHAUSTED,
}

ROUTABLE_VERIFICATION_STATUSES = {
    VerificationStatus.SUCCESS,
    VerificationStatus.RATE_LIMITED,
    VerificationStatus.QUOTA_EXHAUSTED,
    VerificationStatus.NOT_TESTED,
}


def access_verdict_for_status(status: VerificationStatus) -> AccessVerdict:
    """Map a low-level probe status to a user-facing access verdict."""
    if status == VerificationStatus.SUCCESS:
        return AccessVerdict.USABLE_NOW
    if status == VerificationStatus.RATE_LIMITED:
        return AccessVerdict.EXISTS_BUT_THROTTLED
    if status == VerificationStatus.QUOTA_EXHAUSTED:
        return AccessVerdict.QUOTA_EXHAUSTED_FOR_ACCOUNT
    if status == VerificationStatus.NOT_TESTED:
        return AccessVerdict.UNKNOWN
    return AccessVerdict.NOT_ACCESSIBLE


def is_evidence_status(status: VerificationStatus) -> bool:
    """Return true when the probe proves endpoint existence/access path."""
    return status in EVIDENCE_STATUSES


def is_routable_status(status: VerificationStatus) -> bool:
    """Return true when the endpoint can remain in generated routing outputs."""
    return status in ROUTABLE_VERIFICATION_STATUSES


def classify_http_status(status_code: int, body_text: str = "") -> VerificationStatus:
    """Classify HTTP status codes consistently across provider adapters."""
    body = body_text.lower()
    quota_markers = (
        "quota",
        "insufficient_quota",
        "billing",
        "credit",
        "credits",
        "balance",
        "exceeded your current quota",
        "resource_exhausted",
    )
    region_markers = ("region", "country", "geo", "location is not supported")

    if status_code == 200:
        return VerificationStatus.SUCCESS
    if status_code == 401:
        return VerificationStatus.AUTHENTICATION_FAILED
    if status_code == 402:
        return VerificationStatus.QUOTA_EXHAUSTED
    if status_code == 403:
        if any(marker in body for marker in quota_markers):
            return VerificationStatus.QUOTA_EXHAUSTED
        if any(marker in body for marker in region_markers):
            return VerificationStatus.REGION_BLOCKED
        return VerificationStatus.AUTHENTICATION_FAILED
    if status_code == 404:
        return VerificationStatus.MODEL_NOT_FOUND
    if status_code in {408, 504}:
        return VerificationStatus.TIMEOUT
    if status_code == 429:
        if any(marker in body for marker in quota_markers):
            return VerificationStatus.QUOTA_EXHAUSTED
        return VerificationStatus.RATE_LIMITED
    if 500 <= status_code <= 599:
        return VerificationStatus.PROVIDER_UNAVAILABLE
    return VerificationStatus.INVALID_RESPONSE


def parse_retry_after_seconds(headers: Mapping[str, str]) -> int | None:
    """Parse Retry-After as delta seconds when the provider sends it."""
    raw = headers.get("retry-after") or headers.get("Retry-After")
    if not raw:
        return None
    raw = raw.strip()
    if raw.isdigit():
        return int(raw)
    try:
        retry_at = parsedate_to_datetime(raw)
    except (TypeError, ValueError):
        return None
    if retry_at.tzinfo is None:
        retry_at = retry_at.replace(tzinfo=UTC)
    delta = retry_at - datetime.now(UTC)
    return max(0, int(delta.total_seconds()))


def response_error_message(body_text: str, *, max_chars: int = 500) -> str | None:
    """Keep a compact, non-secret error snippet for evidence reports."""
    message = " ".join(body_text.split())
    if not message:
        return None
    return message[:max_chars]
