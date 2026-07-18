"""Tests for provider adapters — zero-network unit tests for conversion logic."""

from free_ai_model_router.models import ApiStyle, FreeStatus, VerificationStatus
from free_ai_model_router.providers.base import ProviderModel, PricingRecord, VerificationResult


def test_provider_model_defaults() -> None:
    pm = ProviderModel(provider_model_id="test/model")
    assert pm.provider_model_id == "test/model"
    assert pm.api_style == ApiStyle.OPENAI_COMPATIBLE
    assert pm.free_status == FreeStatus.UNKNOWN
    assert pm.tool_calling is False


def test_pricing_record() -> None:
    pr = PricingRecord(
        provider_model_id="test/model",
        free_input=True,
        free_output=True,
    )
    assert pr.free_input is True
    assert pr.free_output is True
    assert pr.input_price_per_million is None


def test_verification_result() -> None:
    vr = VerificationResult(
        provider_model_id="test/model",
        status=VerificationStatus.SUCCESS,
        latency_ms=150,
        http_status=200,
    )
    assert vr.status == VerificationStatus.SUCCESS
    assert vr.latency_ms == 150
    assert vr.tool_calling_verified is False
