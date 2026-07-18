"""Scoring engine — computes final router scores from benchmarks and config."""

from __future__ import annotations

import logging
from typing import Optional

from free_ai_model_router.models import (
    BenchmarkScores,
    CanonicalModel,
    ConfidenceLevel,
    ModelRating,
    NormalizedScores,
    PenaltiesConfig,
    ProviderEndpoint,
    QualityBand,
    ScoringConfig,
    ScoringMode,
    WeightsConfig,
)

logger = logging.getLogger(__name__)


class ScoreInput:
    """All data needed to compute a final score for a single model."""

    def __init__(
        self,
        model: CanonicalModel,
        endpoint: Optional[ProviderEndpoint] = None,
        rating: Optional[ModelRating] = None,
    ) -> None:
        self.model = model
        self.endpoint = endpoint
        self.rating = rating or ModelRating(canonical_model_id=model.canonical_model_id)


class ScoringEngine:
    """Scoring engine that computes final router scores.

    Supports two modes:
    - composite_primary: Coding Agent Index is the main aggregator (default)
    - component_weighted: recalculate from individual components
    """

    def __init__(
        self,
        config: ScoringConfig,
        reference_value: Optional[float] = None,
    ) -> None:
        self.config = config
        self.reference_value = reference_value or config.reference.manual_reference_value

    def compute_score(
        self,
        score_input: ScoreInput,
    ) -> ModelRating:
        """Compute final rating for a model."""
        model = score_input.model
        rating = score_input.rating
        endpoint = score_input.endpoint
        benchmark = rating.benchmark

        normalized = NormalizedScores()

        if self.config.scoring_mode == ScoringMode.COMPOSITE_PRIMARY:
            normalized = self._score_composite_primary(benchmark, model, endpoint)
        else:
            normalized = self._score_component_weighted(benchmark, model, endpoint)

        # Apply penalties
        normalized = self._apply_penalties(normalized, model, endpoint, rating)

        # Calculate final score
        final = self._calculate_final(normalized)

        # Determine quality band
        quality_band = self._determine_band(final)

        # Determine confidence
        confidence = rating.ranking_confidence
        if benchmark.artificial_analysis_coding_agent_index is not None:
            confidence = ConfidenceLevel.HIGH
        elif benchmark.artificial_analysis_coding_index is not None:
            confidence = ConfidenceLevel.MEDIUM
        elif benchmark.terminal_bench_v2 is not None:
            confidence = ConfidenceLevel.MEDIUM

        return ModelRating(
            canonical_model_id=model.canonical_model_id,
            benchmark=benchmark,
            normalized_scores=normalized,
            quality_band=quality_band,
            ranking_confidence=confidence,
        )

    def _score_composite_primary(
        self,
        benchmark: BenchmarkScores,
        model: CanonicalModel,
        endpoint: Optional[ProviderEndpoint],
    ) -> NormalizedScores:
        """Composite primary: Coding Agent Index drives the score, others adjust."""
        scores = NormalizedScores()

        coding_agent = benchmark.artificial_analysis_coding_agent_index
        if coding_agent is not None:
            # Use the raw AA index score directly — it's already a percentage-like value
            base_score = coding_agent
        else:
            # Fall back to coding index if available
            coding_index = benchmark.artificial_analysis_coding_index
            if coding_index is not None:
                base_score = coding_index * 0.8  # discount non-agent score
            else:
                base_score = 0.0

        scores.coding_quality_percent = base_score

        # Small adjustments from other metrics (max ±5%)
        adjustment = 0.0
        if benchmark.terminal_bench_v2 is not None:
            adjustment += benchmark.terminal_bench_v2 * 0.02
        if benchmark.swe_atlas_qna is not None:
            adjustment += benchmark.swe_atlas_qna * 0.01
        if benchmark.intelligence_index is not None:
            adjustment += benchmark.intelligence_index * 0.02

        # Endpoint reliability adjustment
        if endpoint and endpoint.runtime_check.checked:
            if endpoint.runtime_check.status.value == "success":
                adjustment += 2.0
            elif endpoint.runtime_check.consecutive_failures > 0:
                adjustment -= 5.0 * endpoint.runtime_check.consecutive_failures

        scores.coding_quality_percent = base_score + adjustment

        return scores

    def _score_component_weighted(
        self,
        benchmark: BenchmarkScores,
        model: CanonicalModel,
        endpoint: Optional[ProviderEndpoint],
    ) -> NormalizedScores:
        """Component weighted: recalculate from individual components."""
        w = self.config.weights
        scores = NormalizedScores()
        components: list[tuple[Optional[float], float]] = []

        def add_component(value: Optional[float], weight: float) -> None:
            if value is not None and value > 0:
                components.append((value, weight))

        add_component(benchmark.artificial_analysis_coding_agent_index, w.coding_agent_index)
        add_component(benchmark.artificial_analysis_coding_index, w.coding_model_index)
        add_component(benchmark.terminal_bench_v2, w.terminal_bench)
        add_component(benchmark.swe_atlas_qna, w.repository_understanding)
        add_component(benchmark.intelligence_index, w.context_utility)

        if not components:
            scores.coding_quality_percent = 0.0
            return scores

        total_weight = sum(w for _, w in components)
        weighted_sum = sum(v * w for v, w in components)
        scores.coding_quality_percent = (weighted_sum / total_weight) if total_weight > 0 else 0.0

        return scores

    def _apply_penalties(
        self,
        scores: NormalizedScores,
        model: CanonicalModel,
        endpoint: Optional[ProviderEndpoint],
        rating: ModelRating,
    ) -> NormalizedScores:
        """Apply configured penalties."""
        p = self.config.penalties
        penalties_applied: list[str] = []

        if scores.coding_quality_percent is None:
            return scores

        score = scores.coding_quality_percent

        # No tool calling
        if not model.capabilities.tool_calling:
            score += p.no_tool_calling
            penalties_applied.append(f"no_tool_calling: {p.no_tool_calling}")

        # Context below minimum
        if endpoint and endpoint.context_tokens and endpoint.context_tokens < self.config.minimum_context_tokens:
            score += p.context_below_minimum
            penalties_applied.append(f"context_below_minimum ({endpoint.context_tokens} < {self.config.minimum_context_tokens}): {p.context_below_minimum}")

        # Temporary free
        if endpoint and endpoint.free_status.value == "temporary_free":
            score += p.temporary_free
            penalties_applied.append(f"temporary_free: {p.temporary_free}")

        # Trial credit
        if endpoint and endpoint.free_status.value == "trial_credit":
            score += p.trial_credit_only
            penalties_applied.append(f"trial_credit: {p.trial_credit_only}")

        # Consecutive failures
        if endpoint and endpoint.runtime_check.consecutive_failures >= 2:
            score += p.two_consecutive_failures
            penalties_applied.append(f"two_consecutive_failures ({endpoint.runtime_check.consecutive_failures}): {p.two_consecutive_failures}")

        # Low confidence
        if rating.ranking_confidence == ConfidenceLevel.LOW:
            score += p.low_match_confidence
            penalties_applied.append(f"low_match_confidence: {p.low_match_confidence}")

        scores.coding_quality_percent = max(0.0, min(100.0, score))
        scores.penalties_applied = penalties_applied
        return scores

    def _calculate_final(self, scores: NormalizedScores) -> float:
        """Calculate final router score from normalized scores."""
        quality = scores.coding_quality_percent or 0.0
        reliability = scores.reliability_percent or 90.0  # default if unknown

        # Simple weighted: 80% quality, 20% reliability
        final = quality * 0.8 + reliability * 0.2
        scores.final_router_score = round(final, 1)
        scores.reliability_percent = reliability
        return final

    def _determine_band(self, score: float) -> QualityBand:
        """Determine quality band from score."""
        if score >= self.config.excellent_threshold_percent:
            return QualityBand.EXCELLENT
        elif score >= self.config.quality_threshold_percent:
            return QualityBand.GOOD
        else:
            return QualityBand.BELOW_THRESHOLD

    def passes_threshold(self, rating: ModelRating) -> bool:
        """Check if a model passes the inclusion threshold."""
        final = rating.normalized_scores.final_router_score or 0
        threshold = self.config.quality_threshold_percent

        # Stricter threshold for low confidence
        if rating.ranking_confidence == ConfidenceLevel.LOW:
            threshold = self.config.low_confidence_threshold_percent

        return final >= threshold
