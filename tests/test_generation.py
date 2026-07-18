"""Tests for LiteLLM config generation."""

from free_ai_model_router.models import (
    FreeStatus,
    ProviderEndpoint,
    QualityBand,
    RouterOutput,
    RoutedEndpoint,
    ScoringMode,
    Limits,
)
from free_ai_model_router.generation.litellm_config import (
    generate_litellm_config,
    build_fallback_chain,
)


def _sample_endpoint(ep_id: str, provider: str, model: str) -> ProviderEndpoint:
    return ProviderEndpoint(
        endpoint_id=ep_id,
        provider_id=provider,
        canonical_model_id=f"{provider}/{model}",
        provider_model_id=model,
        litellm_model=f"{provider}/{model}",
        api_base=f"https://api.{provider}.com/v1",
        free_status=FreeStatus.VERIFIED_FREE,
        limits=Limits(requests_per_day=1000),
    )


def _sample_routed(ep_id: str, provider: str, model: str, score: float, rank: int) -> RoutedEndpoint:
    return RoutedEndpoint(
        endpoint_id=ep_id,
        provider_id=provider,
        provider_name=provider,
        canonical_model_id=f"{provider}/{model}",
        model_name=model,
        final_score=score,
        quality_band=QualityBand.GOOD,
        free_status=FreeStatus.VERIFIED_FREE,
        rank=rank,
        is_primary=(rank == 1),
    )


def test_generate_litellm_config() -> None:
    ep = _sample_endpoint("test/ep1", "test", "model-v1")
    routed = _sample_routed("test/ep1", "test", "model-v1", 85.0, 1)

    output = RouterOutput(
        endpoints=[routed],
        fallback_chain=["test/ep1"],
        scoring_mode=ScoringMode.COMPOSITE_PRIMARY,
    )

    yaml_str = generate_litellm_config(output, {"test/ep1": ep})
    assert "model_list:" in yaml_str
    assert "coding-primary" in yaml_str
    assert "os.environ/TEST_API_KEY" in yaml_str
    assert "router_settings:" in yaml_str
    assert "fallbacks:" in yaml_str
    assert "coding-auto:" in yaml_str


def test_build_fallback_chain() -> None:
    ep1 = _sample_endpoint("ep1", "provider_a", "model-a")
    ep2 = _sample_endpoint("ep2", "provider_b", "model-b")
    ep3 = _sample_endpoint("ep3", "provider_a", "model-c")  # same provider as ep1

    from free_ai_model_router.models import ModelRating, CanonicalModel, BenchmarkScores, NormalizedScores
    rating1 = ModelRating(
        canonical_model_id="provider_a/model-a",
        normalized_scores=NormalizedScores(final_router_score=90.0),
    )
    rating2 = ModelRating(
        canonical_model_id="provider_b/model-b",
        normalized_scores=NormalizedScores(final_router_score=80.0),
    )
    rating3 = ModelRating(
        canonical_model_id="provider_a/model-c",
        normalized_scores=NormalizedScores(final_router_score=75.0),
    )

    from free_ai_model_router.models import ScoringConfig
    config = ScoringConfig(quality_threshold_percent=70.0)

    paired = [(ep1, rating1), (ep2, rating2), (ep3, rating3)]
    chain = build_fallback_chain(paired, config)

    # Should include ep1 (primary) and ep2 (different provider)
    # ep3 should be skipped because same provider as ep1 and diversity is preferred
    assert len(chain) >= 2
    assert chain[0].is_primary is True
    # Verify provider diversity
    providers = {r.provider_id for r in chain}
    assert len(providers) >= 2


def test_build_fallback_chain_empty() -> None:
    from free_ai_model_router.models import ScoringConfig
    config = ScoringConfig()
    chain = build_fallback_chain([], config)
    assert chain == []
