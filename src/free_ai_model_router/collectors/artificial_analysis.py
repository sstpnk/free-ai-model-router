"""Artificial Analysis data collector — Coding Agent Index and benchmarks."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Optional

from free_ai_model_router.http_client.client import HttpClient
from free_ai_model_router.models import (
    BenchmarkScores,
    CanonicalModel,
    ModelRating,
    NormalizedScores,
    QualityBand,
    ConfidenceLevel,
)

logger = logging.getLogger(__name__)

# Official AA Data API endpoints (v2)
AA_API_BASE_V2 = "https://artificialanalysis.ai/api/v2"
AA_FREE_MODELS_URL = f"{AA_API_BASE_V2}/language/models/free"

# Public page as fallback
AA_CODING_AGENTS_PAGE = "https://artificialanalysis.ai/agents/coding-agents"
AA_DATA_API_DOCS = "https://artificialanalysis.ai/data-api/docs"


class ArtificialAnalysisCollector:
    """Collector for Artificial Analysis benchmark data."""

    def __init__(
        self,
        http_client: HttpClient,
        api_key: Optional[str] = None,
    ) -> None:
        self.http = http_client
        self.api_key = api_key
        self._current_run_source: str = "none"

    async def fetch_coding_agent_index(self) -> list[dict[str, Any]]:
        """Fetch coding index from AA v2 API (free tier) or fall back to page."""
        if self.api_key:
            try:
                data = await self.http.fetch_json(
                    AA_FREE_MODELS_URL,
                    auth_header="x-api-key",
                    auth_token=self.api_key,
                    use_cache=True,
                    cache_ttl_seconds=14400,  # 4 hours — preserve quota
                )
                self._current_run_source = "api"
                return data.get("data", []) if isinstance(data, dict) else (data if isinstance(data, list) else [])
            except Exception as e:
                logger.warning("AA API fetch failed, will try page fallback: %s", e)

        # Fallback: structured page data
        try:
            logger.info("Falling back to AA Coding Agents page data")
            html = await self.http.fetch_text(AA_CODING_AGENTS_PAGE)
            self._current_run_source = "page_fallback"
            return self._parse_page_data(html)
        except Exception as e:
            logger.error("AA page fallback also failed: %s", e)
            self._current_run_source = "failed"
            return []

    def _parse_page_data(self, html: str) -> list[dict[str, Any]]:
        """Parse structured data from AA public page (simple extraction)."""
        import json
        import re

        results: list[dict[str, Any]] = []

        # Try to find embedded JSON data (Next.js __NEXT_DATA__)
        next_data_match = re.search(r'__NEXT_DATA__\s*=\s*({.*?});', html, re.DOTALL)
        if next_data_match:
            try:
                next_data = json.loads(next_data_match.group(1))
                # Navigate typical Next.js props structure
                props = next_data.get("props", {}).get("pageProps", {})
                agents_data = props.get("agents") or props.get("results") or props.get("models") or []
                if isinstance(agents_data, list):
                    results = agents_data
            except (json.JSONDecodeError, KeyError) as e:
                logger.warning("Failed to parse AA page data: %s", e)

        # Attempt table row extraction if no JSON found
        if not results:
            rows = re.findall(r'<tr[^>]*>(.*?)</tr>', html, re.DOTALL)
            for row in rows:
                cells = re.findall(r'<td[^>]*>(.*?)</td>', row, re.DOTALL)
                if len(cells) >= 4:
                    model_name = re.sub(r'<[^>]+>', '', cells[0]).strip()
                    score_str = re.sub(r'<[^>]+>', '', cells[1]).strip() if len(cells) > 1 else ""
                    try:
                        score = float(score_str.replace(",", ""))
                    except ValueError:
                        score = 0.0
                    results.append({"model": model_name, "score": score})

        return results

    def _find_model_in_index(
        self,
        model_name: str,
        index_data: list[dict[str, Any]],
    ) -> Optional[dict[str, Any]]:
        """Find a model entry in the coding agent index by name matching."""
        name_lower = model_name.lower()
        for entry in index_data:
            entry_name = str(entry.get("name", entry.get("id", ""))).lower()
            if name_lower in entry_name or entry_name in name_lower:
                return entry
            # Also check slug
            slug = entry.get("slug", "")
            if slug and name_lower in slug.lower():
                return entry
        return None

    async def rate_model(
        self,
        model: CanonicalModel,
        index_data: list[dict[str, Any]],
        reference_value: Optional[float] = None,
    ) -> ModelRating:
        """Compute rating for a single model using AA v2 API data."""
        entry = self._find_model_in_index(model.name, index_data)

        benchmark = BenchmarkScores()
        normalized = NormalizedScores()

        if entry:
            evals = entry.get("evaluations", {})

            raw_score = evals.get("artificial_analysis_coding_index")
            coding_index = evals.get("artificial_analysis_coding_index")
            terminal_bench = evals.get("terminalbench_v2_1", evals.get("terminalbench_hard"))
            deep_swe = evals.get("deep_swe")
            intelligence = evals.get("artificial_analysis_intelligence_index")
            agentic_index = evals.get("artificial_analysis_agentic_index")

            benchmark.artificial_analysis_coding_agent_index = raw_score
            benchmark.artificial_analysis_coding_index = coding_index
            benchmark.terminal_bench_v2 = terminal_bench
            benchmark.deep_swe = deep_swe
            benchmark.intelligence_index = intelligence
            benchmark.agentic_index = agentic_index
            benchmark.evaluated_at = datetime.now(timezone.utc)
            benchmark.source_url = AA_DATA_API_DOCS

            # Normalize to percentage
            if raw_score is not None:
                ref = reference_value or raw_score  # if this IS the reference
                if ref and ref > 0:
                    normalized.coding_quality_percent = round((raw_score / ref) * 100, 1)
                else:
                    normalized.coding_quality_percent = raw_score

            ranking_confidence = ConfidenceLevel.HIGH
        else:
            ranking_confidence = ConfidenceLevel.LOW
            logger.info("No AA data for model %s", model.name)

        rating = ModelRating(
            canonical_model_id=model.canonical_model_id,
            benchmark=benchmark,
            normalized_scores=normalized,
            ranking_confidence=ranking_confidence,
        )

        # Determine quality band
        if normalized.coding_quality_percent is not None:
            if normalized.coding_quality_percent >= 85:
                rating.quality_band = QualityBand.EXCELLENT
            elif normalized.coding_quality_percent >= 70:
                rating.quality_band = QualityBand.GOOD
            else:
                rating.quality_band = QualityBand.BELOW_THRESHOLD

        return rating

    def get_source_info(self) -> dict[str, Any]:
        """Return metadata about which source was used."""
        return {
            "source": self._current_run_source,
            "api_key_configured": bool(self.api_key),
            "documentation": AA_DATA_API_DOCS,
            "attribution_required": True,
        }


async def collect_aa_ratings(
    models: list[CanonicalModel],
    http_client: HttpClient,
    api_key: Optional[str] = None,
    reference_value: Optional[float] = None,
) -> tuple[list[ModelRating], dict[str, Any]]:
    """Convenience: fetch AA index and rate all models."""
    collector = ArtificialAnalysisCollector(http_client, api_key)
    index_data = await collector.fetch_coding_agent_index()
    ratings: list[ModelRating] = []
    for model in models:
        rating = await collector.rate_model(model, index_data, reference_value)
        ratings.append(rating)
    return ratings, collector.get_source_info()
