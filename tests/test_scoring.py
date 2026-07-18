"""Tests for scoring engine."""

from free_ai_model_router.models import (
    BenchmarkScores,
    CanonicalModel,
    ModelRating,
    NormalizedScores,
    QualityBand,
    ScoringConfig,
    ScoringMode,
    ConfidenceLevel,
    FreeStatus,
    ProviderEndpoint,
    Limits,
)
from free_ai_model_router.scoring.engine import ScoringEngine, ScoreInput


def _make_scoring_config(**overrides) -> ScoringConfig:
    config = ScoringConfig(**overrides)
    return config


def test_scoring_default_config() -> None:
    config = _make_scoring_config()
    assert config.quality_threshold_percent == 70.0
    assert config.excellent_threshold_percent == 85.0
    assert config.scoring_mode == ScoringMode.COMPOSITE_PRIMARY


def test_compute_score_with_aa_data() -> None:
    config = _make_scoring_config()
    engine = ScoringEngine(config)

    model = CanonicalModel(
        canonical_model_id="test/model",
        name="Test-Model",
        capabilities={"coding": True, "tool_calling": True},
    )

    rating = ModelRating(
        canonical_model_id="test/model",
        benchmark=BenchmarkScores(
            artificial_analysis_coding_agent_index=90.0,
        ),
    )

    si = ScoreInput(model=model, rating=rating)
    result = engine.compute_score(si)

    assert result.normalized_scores.coding_quality_percent is not None
    assert result.normalized_scores.coding_quality_percent > 0
    assert result.quality_band in (QualityBand.EXCELLENT, QualityBand.GOOD)


def test_low_score_below_threshold() -> None:
    config = _make_scoring_config()
    engine = ScoringEngine(config)

    model = CanonicalModel(
        canonical_model_id="test/model",
        name="Test-Model",
        capabilities={"coding": True, "tool_calling": False},
    )
    # Low score with no tool calling
    rating = ModelRating(
        canonical_model_id="test/model",
        benchmark=BenchmarkScores(
            artificial_analysis_coding_agent_index=30.0,
        ),
    )

    si = ScoreInput(model=model, rating=rating)
    result = engine.compute_score(si)

    assert result.quality_band == QualityBand.BELOW_THRESHOLD
    assert not engine.passes_threshold(result)


def test_penalties_applied() -> None:
    config = _make_scoring_config()
    engine = ScoringEngine(config)

    model = CanonicalModel(
        canonical_model_id="test/model",
        name="Test-Model",
        capabilities={"coding": True, "tool_calling": False},
    )

    endpoint = ProviderEndpoint(
        endpoint_id="test/ep",
        provider_id="test",
        canonical_model_id="test/model",
        provider_model_id="test-v1",
        free_status=FreeStatus.TEMPORARY_FREE,
        context_tokens=32000,
        limits=Limits(requests_per_day=10),
    )

    rating = ModelRating(
        canonical_model_id="test/model",
        benchmark=BenchmarkScores(
            artificial_analysis_coding_agent_index=80.0,
        ),
    )

    si = ScoreInput(model=model, endpoint=endpoint, rating=rating)
    result = engine.compute_score(si)

    assert len(result.normalized_scores.penalties_applied) >= 1
    has_no_tool = any("no_tool_calling" in p for p in result.normalized_scores.penalties_applied)
    assert has_no_tool


def test_confidence_levels() -> None:
    config = _make_scoring_config()
    engine = ScoringEngine(config)

    # High confidence — direct AA data
    model = CanonicalModel(canonical_model_id="test/model", name="direct-test")
    rating = ModelRating(
        canonical_model_id="test/model",
        benchmark=BenchmarkScores(
            artificial_analysis_coding_agent_index=85.0,
        ),
    )
    si = ScoreInput(model=model, rating=rating)
    result = engine.compute_score(si)
    assert result.ranking_confidence == ConfidenceLevel.HIGH

    # Low confidence — no AA data
    model2 = CanonicalModel(canonical_model_id="test/model2", name="no-data")
    rating2 = ModelRating(canonical_model_id="test/model2")
    si2 = ScoreInput(model=model2, rating=rating2)
    result2 = engine.compute_score(si2)
    assert result2.ranking_confidence == ConfidenceLevel.LOW


def test_component_weighted_mode() -> None:
    config = _make_scoring_config(scoring_mode=ScoringMode.COMPONENT_WEIGHTED)
    engine = ScoringEngine(config)

    model = CanonicalModel(canonical_model_id="test/model", name="comp-test")
    rating = ModelRating(
        canonical_model_id="test/model",
        benchmark=BenchmarkScores(
            artificial_analysis_coding_agent_index=90.0,
            terminal_bench_v2=85.0,
            intelligence_index=80.0,
        ),
    )
    si = ScoreInput(model=model, rating=rating)
    result = engine.compute_score(si)
    # Should have a positive score from components
    assert result.normalized_scores.coding_quality_percent is not None
    assert result.normalized_scores.coding_quality_percent > 0
