"""Tests for runtime catalog generation."""

from datetime import UTC, datetime

from free_ai_model_router.generation.catalog import generate_runtime_catalog
from free_ai_model_router.models import (
    AccessVerdict,
    ApiStyle,
    FreeStatus,
    ProviderEndpoint,
    RoutedEndpoint,
    RouterOutput,
    VerificationStatus,
)


def test_generate_runtime_catalog_includes_verification_metadata() -> None:
    checked_at = datetime(2026, 1, 2, 3, 4, 5, tzinfo=UTC)
    endpoint = ProviderEndpoint(
        endpoint_id="test/model",
        provider_id="test",
        canonical_model_id="test/model",
        provider_model_id="model",
        litellm_model="test/model",
        api_base="https://api.test/v1",
        api_style=ApiStyle.OPENAI_COMPATIBLE,
        free_status=FreeStatus.VERIFIED_FREE,
    )
    endpoint.runtime_check.retry_after_seconds = 7

    output = RouterOutput(
        generated_at=checked_at,
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
                latency_ms=123,
                last_checked_at=checked_at,
                tool_calling=True,
                modalities=["text"],
            )
        ],
        fallback_chain=["test/model"],
    )

    catalog = generate_runtime_catalog(output, {"test/model": endpoint})

    assert catalog["schema_version"] == 1
    assert catalog["endpoint_count"] == 1
    assert catalog["fallback_chain"] == ["test/model"]
    assert catalog["endpoints"][0]["access_verdict"] == "exists_but_throttled"
    assert catalog["endpoints"][0]["runtime_status"] == "rate_limited"
    assert catalog["endpoints"][0]["retry_after_seconds"] == 7
    assert catalog["endpoints"][0]["api_base"] == "https://api.test/v1"
