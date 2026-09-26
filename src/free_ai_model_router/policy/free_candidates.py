"""Free-access candidate policy.

This module is intentionally side-effect free: it explains why a model should
be probed as a possible free endpoint without making network calls.
"""

from __future__ import annotations

from free_ai_model_router.models import FreeCandidateEvidence, FreeStatus, ProviderEndpoint

ROUTABLE_FREE_STATUSES = {
    FreeStatus.VERIFIED_FREE,
    FreeStatus.DOCUMENTED_FREE,
    FreeStatus.ACCOUNT_SPECIFIC_FREE,
    FreeStatus.TEMPORARY_FREE,
}

CANDIDATE_FREE_STATUSES = {
    *ROUTABLE_FREE_STATUSES,
    FreeStatus.TRIAL_CREDIT,
}

_STATUS_REASONS = {
    FreeStatus.VERIFIED_FREE: "provider_verified_free_status",
    FreeStatus.DOCUMENTED_FREE: "provider_documented_free_status",
    FreeStatus.ACCOUNT_SPECIFIC_FREE: "provider_account_specific_free_status",
    FreeStatus.TEMPORARY_FREE: "provider_temporary_free_status",
    FreeStatus.TRIAL_CREDIT: "provider_trial_credit_status",
}


def model_id_has_free_marker(provider_model_id: str) -> bool:
    """Return true when the provider model id explicitly marks a free model."""
    normalized = provider_model_id.lower()
    return ":free" in normalized or normalized.endswith("-free")


def classify_free_candidate(
    *,
    provider_model_id: str,
    free_status: FreeStatus,
) -> FreeCandidateEvidence:
    """Classify whether a model should be considered a free-access candidate."""
    if free_status in CANDIDATE_FREE_STATUSES:
        return FreeCandidateEvidence(
            is_candidate=True,
            route_eligible=free_status in ROUTABLE_FREE_STATUSES,
            source="free_status",
            reason=_STATUS_REASONS[free_status],
            detail=free_status.value,
        )

    if model_id_has_free_marker(provider_model_id):
        return FreeCandidateEvidence(
            is_candidate=True,
            route_eligible=True,
            source="model_id",
            reason="model_id_free_marker",
            detail=provider_model_id,
        )

    return FreeCandidateEvidence()


def evaluate_free_candidate(endpoint: ProviderEndpoint) -> FreeCandidateEvidence:
    """Classify an endpoint and return the free candidate evidence."""
    return classify_free_candidate(
        provider_model_id=endpoint.provider_model_id,
        free_status=endpoint.free_status,
    )


def annotate_free_candidate(endpoint: ProviderEndpoint) -> ProviderEndpoint:
    """Attach free candidate evidence to an endpoint and return it."""
    endpoint.free_candidate = evaluate_free_candidate(endpoint)
    return endpoint
