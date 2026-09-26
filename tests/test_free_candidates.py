"""Tests for free-candidate policy decisions."""

from free_ai_model_router.models import FreeStatus, ProviderEndpoint
from free_ai_model_router.policy.free_candidates import annotate_free_candidate, classify_free_candidate


def test_classify_free_candidate_from_free_status() -> None:
    evidence = classify_free_candidate(
        provider_model_id="model",
        free_status=FreeStatus.ACCOUNT_SPECIFIC_FREE,
    )

    assert evidence.is_candidate is True
    assert evidence.route_eligible is True
    assert evidence.source == "free_status"
    assert evidence.reason == "provider_account_specific_free_status"


def test_classify_trial_credit_as_candidate_but_not_route_eligible() -> None:
    evidence = classify_free_candidate(
        provider_model_id="model",
        free_status=FreeStatus.TRIAL_CREDIT,
    )

    assert evidence.is_candidate is True
    assert evidence.route_eligible is False
    assert evidence.reason == "provider_trial_credit_status"


def test_classify_free_candidate_from_model_id_marker() -> None:
    evidence = classify_free_candidate(
        provider_model_id="provider/model:free",
        free_status=FreeStatus.UNKNOWN,
    )

    assert evidence.is_candidate is True
    assert evidence.route_eligible is True
    assert evidence.source == "model_id"
    assert evidence.reason == "model_id_free_marker"


def test_annotate_free_candidate_updates_endpoint() -> None:
    endpoint = ProviderEndpoint(
        endpoint_id="test/model-free",
        provider_id="test",
        canonical_model_id="test/model-free",
        provider_model_id="model-free",
    )

    annotate_free_candidate(endpoint)

    assert endpoint.free_candidate.is_candidate is True
    assert endpoint.free_candidate.reason == "model_id_free_marker"
