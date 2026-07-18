"""Pipeline orchestrator — coordinates collect → discover → verify → score → generate → report flow."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from free_ai_model_router.collectors.artificial_analysis import ArtificialAnalysisCollector
from free_ai_model_router.collectors.huggingface import HuggingFaceCollector
from free_ai_model_router.config_loader import Settings
from free_ai_model_router.generation.litellm_config import build_fallback_chain, generate_litellm_config_file
from free_ai_model_router.generation.reports import write_reports
from free_ai_model_router.http_client.client import HttpClient
from free_ai_model_router.models import (
    CanonicalModel,
    ChangeRecord,
    ModelRating,
    PipelineState,
    ProviderEndpoint,
    RouterOutput,
    RoutedEndpoint,
    SourceHealth,
    FreeStatus,
)
from free_ai_model_router.providers.base import ProviderModel
from free_ai_model_router.providers.gemini import GeminiAdapter
from free_ai_model_router.providers.groq import GroqAdapter
from free_ai_model_router.providers.mistral import MistralAdapter
from free_ai_model_router.providers.opencode_zen import OpenCodeZenAdapter
from free_ai_model_router.providers.openrouter import OpenRouterAdapter
from free_ai_model_router.providers.zai import ZAIAdapter
from free_ai_model_router.scoring.engine import ScoreInput, ScoringEngine
from free_ai_model_router.storage.state import (
    load_normalized_data,
    load_previous_output,
    save_normalized_data,
    save_pipeline_state,
    save_router_output,
)

logger = logging.getLogger(__name__)


class PipelineOrchestrator:
    """Orchestrates the full daily pipeline run."""

    def __init__(
        self,
        settings: Settings,
        base_dir: Path,
    ) -> None:
        self.settings = settings
        self.base_dir = base_dir
        self.state = PipelineState()
        self.http: Optional[HttpClient] = None
        self.collected_models: list[CanonicalModel] = []
        self.collected_endpoints: list[ProviderEndpoint] = []
        self.ratings: list[ModelRating] = []
        self.discovered_candidates: list[dict] = []
        self.changes: list[ChangeRecord] = []
        self.source_health: dict[str, SourceHealth] = {}
        self.aa_attribution: Optional[str] = None

    async def run_all(
        self,
        *,
        use_cache: bool = True,
        no_runtime_checks: bool = False,
        offline: bool = False,
    ) -> PipelineState:
        """Run the complete pipeline: collect → discover → verify → score → generate → report."""
        logger.info("Starting full pipeline run")
        self.state = PipelineState()

        try:
            # Initialize HTTP client with SSRF protection
            allowed_domains = [
                "openrouter.ai", "opencode.cloud", "z.ai",
                "api.groq.com", "generativelanguage.googleapis.com",
                "api.mistral.ai", "api.openai.com",
                "api.anthropic.com", "api.x.ai",
                "huggingface.co", "api.artificialanalysis.ai",
                "artificialanalysis.ai", "github.com",
                "raw.githubusercontent.com", "docs.litellm.ai",
                "models.inference.ai.azure.com",
                "api.cloudflare.com", "api.cerebras.ai",
                "api.sambanova.ai", "api.together.xyz",
                "api.fireworks.ai", "api.deepinfra.com",
                "api.siliconflow.cn", "api.studio.nebius.ai",
                "api.hyperbolic.xyz", "api.replicate.com",
                "api.cohere.com", "api.deepseek.com",
                "api.z.ai",
            ]
            self.http = HttpClient(
                cache_dir=self.settings.cache_dir,
                allowed_domains=allowed_domains,
            )

            # Step 1: Collect from providers
            if not offline:
                await self._collect_providers()
            else:
                logger.info("Offline mode: skipping provider collection")

            # Step 2: Discover candidates from HF / other sources
            if not offline:
                await self._discover_candidates()

            # Step 3: Collect benchmarks (Artificial Analysis)
            if not offline:
                await self._collect_benchmarks()

            # Step 4: Verify models (if keys configured and checks not disabled)
            if not no_runtime_checks and not offline:
                await self._verify_models()

            # Step 5: Score models
            self._score_models()

            # Step 6: Build router output
            router_output = self._build_router()

            # Step 7: Generate LiteLLM config
            self._generate_config(router_output)

            # Step 8: Generate reports
            previous_output = load_previous_output(self.settings.output_dir / "latest.json")
            self._detect_changes(router_output, previous_output)
            self._generate_reports(router_output, previous_output)

            # Step 9: Save state
            save_router_output(router_output, self.settings.output_dir / "latest.json")
            save_normalized_data(
                self.collected_models,
                self.collected_endpoints,
                self.ratings,
                self.settings.normalized_dir,
            )

            self.state.success = True
            self.state.completed_at = datetime.now(timezone.utc)
            logger.info("Pipeline run completed successfully")

        except Exception as e:
            self.state.success = False
            self.state.partial_success = True
            self.state.errors.append(str(e))
            logger.error("Pipeline run failed: %s", e, exc_info=True)
        finally:
            if self.http:
                await self.http.close()
            save_pipeline_state(self.state, self.base_dir / "data" / "pipeline-state.json")

        return self.state

    async def _collect_providers(self) -> None:
        """Discover models from configured providers."""
        assert self.http is not None
        adapters = self._init_adapters()
        all_models: list[ProviderModel] = []
        logger.info("Collecting models from %d providers...", len(adapters))

        for adapter in adapters:
            try:
                models = await adapter.discover_models()
                all_models.extend(models)
                for m in models:
                    ep = adapter.to_provider_endpoint(m)
                    self.collected_endpoints.append(ep)
                    # Create canonical model from endpoint
                    canonical = CanonicalModel(
                        canonical_model_id=ep.canonical_model_id,
                        name=m.name or m.provider_model_id,
                        creator=adapter.provider_id,
                        capabilities=CanonicalModel(
                            canonical_model_id=ep.canonical_model_id,
                            name="",
                        ).capabilities,
                    )
                    canonical.capabilities.tool_calling = m.tool_calling
                    canonical.capabilities.vision = m.vision
                    if m.context_tokens:
                        canonical.capabilities.context_tokens = m.context_tokens
                    self.collected_models.append(canonical)
                logger.info("  %s: discovered %d models", adapter.provider_id, len(models))
            except Exception as e:
                logger.warning("  %s: collection failed: %s", adapter.provider_id, e)
                self.state.errors.append(f"Provider {adapter.provider_id}: {e}")

        # Source health tracking
        self.source_health["provider_discovery"] = SourceHealth(
            source_id="provider_discovery",
            last_success_at=datetime.now(timezone.utc),
            consecutive_failures=0,
        )
        logger.info("Total: %d models from %d providers", len(all_models), len(adapters))

    def _init_adapters(self) -> list:
        """Initialize provider adapters based on config, passing API keys if available."""
        assert self.http is not None
        adapters = []
        adapter_map = {
            "openrouter": OpenRouterAdapter,
            "opencode_zen": OpenCodeZenAdapter,
            "zai": ZAIAdapter,
            "groq": GroqAdapter,
            "gemini": GeminiAdapter,
            "mistral": MistralAdapter,
        }
        for provider in self.settings.providers.providers:
            if not provider.enabled:
                continue
            adapter_cls = adapter_map.get(provider.provider_id)
            if adapter_cls:
                api_key = self.settings.get_provider_api_key(provider.provider_id)
                adapters.append(adapter_cls(self.http, api_key=api_key))
                logger.info("  Initialized adapter: %s (key=%s)", provider.provider_id, "yes" if api_key else "no")

        return adapters

    async def _discover_candidates(self) -> None:
        """Discover new candidates from Hugging Face and other sources."""
        assert self.http is not None
        logger.info("Discovering new model candidates...")

        try:
            hf = HuggingFaceCollector(self.http)
            hf_models = await hf.discover_coding_models(limit=30)
            discovered = []
            for m in hf_models:
                canonical = hf.hf_model_to_canonical(m)
                if canonical and canonical.canonical_model_id not in {x.canonical_model_id for x in self.collected_models}:
                    discovered.append({
                        "id": canonical.canonical_model_id,
                        "name": canonical.name,
                        "source": "hf",
                        "likes": m.get("likes", 0),
                    })
            self.discovered_candidates = discovered
            logger.info("  Hugging Face: %d new candidates", len(discovered))
        except Exception as e:
            logger.warning("  Candidate discovery failed: %s", e)

        self.source_health["candidate_discovery"] = SourceHealth(
            source_id="candidate_discovery",
            last_success_at=datetime.now(timezone.utc),
            consecutive_failures=0 if self.discovered_candidates else 1,
        )

    async def _collect_benchmarks(self) -> None:
        """Fetch benchmark data from Artificial Analysis."""
        assert self.http is not None
        logger.info("Collecting benchmarks from Artificial Analysis...")

        aa_key = self.settings.get_artificial_analysis_api_key()
        collector = ArtificialAnalysisCollector(self.http, aa_key)
        index_data = await collector.fetch_coding_agent_index()

        if not index_data:
            logger.warning("No AA index data available — ratings will have low confidence")
            self.source_health["artificial_analysis"] = SourceHealth(
                source_id="artificial_analysis",
                consecutive_failures=1,
                last_error="Empty index data",
            )
            return

        # If reference model is set, find its value for normalization
        ref_value: Optional[float] = None
        if self.settings.scoring.reference.artificial_analysis_model_id:
            for entry in index_data:
                eid = str(entry.get("model", entry.get("id", "")))
                if eid == self.settings.scoring.reference.artificial_analysis_model_id:
                    ref_value = entry.get("score", entry.get("coding_agent_index"))
                    break

        if ref_value is None and self.settings.scoring.reference.manual_reference_value:
            ref_value = self.settings.scoring.reference.manual_reference_value

        # Rate each model that we collected
        for model in self.collected_models:
            entry = collector._find_model_in_index(model.name, index_data)
            rating = await collector.rate_model(model, index_data, ref_value)
            self.ratings.append(rating)

        aa_source_info = collector.get_source_info()
        self.aa_attribution = f"Artificial Analysis ({aa_source_info.get('source', 'unknown')})"

        self.source_health["artificial_analysis"] = SourceHealth(
            source_id="artificial_analysis",
            last_success_at=datetime.now(timezone.utc),
            consecutive_failures=0,
        )
        logger.info("  AA: %d entries in index, %d models rated",
                     len(index_data), len(self.ratings))

    async def _verify_models(self) -> None:
        """Verify endpoints with actual API calls where keys are available."""
        assert self.http is not None
        logger.info("Verifying models with API calls...")

        adapters = self._init_adapters()
        adapter_by_id = {a.provider_id: a for a in adapters}

        for endpoint in self.collected_endpoints:
            provider_id = endpoint.provider_id
            api_key = self.settings.get_provider_api_key(provider_id)

            if not api_key:
                endpoint.runtime_check.checked = False
                endpoint.runtime_check.status_str = "not_tested"
                continue

            adapter = adapter_by_id.get(provider_id)
            if not adapter:
                continue

            try:
                # Create a ProviderModel from the endpoint for verification
                pm = ProviderModel(
                    provider_model_id=endpoint.provider_model_id,
                    api_base=endpoint.api_base,
                )
                result = await adapter.verify_model(pm, api_key)
                endpoint.runtime_check.checked = True
                endpoint.runtime_check.status = result.status
                endpoint.runtime_check.checked_at = datetime.now(timezone.utc)
                endpoint.runtime_check.latency_ms = result.latency_ms
                endpoint.runtime_check.http_status = result.http_status

                if result.status.value == "success":
                    endpoint.runtime_check.consecutive_failures = 0
                else:
                    endpoint.runtime_check.consecutive_failures += 1

                logger.debug("  %s/%s: %s (%dms)",
                             provider_id, endpoint.provider_model_id,
                             result.status.value, result.latency_ms or 0)
            except Exception as e:
                logger.warning("  %s/%s verification failed: %s",
                               provider_id, endpoint.provider_model_id, e)
                endpoint.runtime_check.checked = True
                endpoint.runtime_check.status_str = "provider_unavailable"

        self.source_health["api_verification"] = SourceHealth(
            source_id="api_verification",
            last_success_at=datetime.now(timezone.utc),
        )
        logger.info("  Verification complete")

    def _score_models(self) -> None:
        """Compute final scores for all models."""
        logger.info("Scoring models...")

        engine = ScoringEngine(self.settings.scoring)
        endpoints_map = {e.canonical_model_id: e for e in self.collected_endpoints}
        models_map = {m.canonical_model_id: m for m in self.collected_models}

        # If we don't have AA ratings, create empty ones
        if not self.ratings:
            for model in self.collected_models:
                self.ratings.append(ModelRating(canonical_model_id=model.canonical_model_id))
            logger.info("  No AA ratings — using default empty ratings")

        ratings_map = {r.canonical_model_id: r for r in self.ratings}

        # Rescore using the engine
        scored_ratings = []
        for model in self.collected_models:
            endpoint = endpoints_map.get(model.canonical_model_id)
            rating = ratings_map.get(model.canonical_model_id, ModelRating(canonical_model_id=model.canonical_model_id))
            si = ScoreInput(model=model, endpoint=endpoint, rating=rating)
            scored = engine.compute_score(si)
            scored_ratings.append(scored)

        self.ratings = scored_ratings
        logger.info("  Scored %d models", len(self.ratings))

    def _build_router(self) -> RouterOutput:
        """Build the router output with sorted endpoints."""
        logger.info("Building router output...")

        endpoints_map = {e.canonical_model_id: e for e in self.collected_endpoints}
        ratings_map = {r.canonical_model_id: r for r in self.ratings}

        # Pair endpoints with ratings
        paired = []
        for endpoint in self.collected_endpoints:
            rating = ratings_map.get(endpoint.canonical_model_id)
            if rating is None:
                continue
            # Only include free-status models
            if endpoint.free_status not in (
                FreeStatus.VERIFIED_FREE,
                FreeStatus.DOCUMENTED_FREE,
                FreeStatus.ACCOUNT_SPECIFIC_FREE,
                FreeStatus.TEMPORARY_FREE,
            ):
                continue
            paired.append((endpoint, rating))

        if not paired:
            logger.warning("No paired endpoints after filtering")
            return RouterOutput(scoring_mode=self.settings.scoring.scoring_mode)

        # Use scoring engine to check thresholds
        engine = ScoringEngine(self.settings.scoring)

        # Build fallback chain with provider diversity
        routed = build_fallback_chain(paired, self.settings.scoring)

        reference_name = self.settings.scoring.reference.name
        return RouterOutput(
            generated_at=datetime.now(timezone.utc),
            reference_scored_at=reference_name,
            endpoints=routed,
            fallback_chain=[r.endpoint_id for r in routed],
            scoring_mode=self.settings.scoring.scoring_mode,
        )

    def _detect_changes(
        self,
        current: RouterOutput,
        previous: Optional[RouterOutput],
    ) -> None:
        """Compare with previous run output and record changes."""
        if not previous:
            self.changes.append(ChangeRecord(
                change_type="initial_run",
                entity_id="pipeline",
                description="First pipeline run — baseline established",
            ))
            return

        current_ids = {r.endpoint_id for r in current.endpoints}
        previous_ids = {r.endpoint_id for r in previous.endpoints}

        new = current_ids - previous_ids
        removed = previous_ids - current_ids

        for eid in new:
            r = next((x for x in current.endpoints if x.endpoint_id == eid), None)
            self.changes.append(ChangeRecord(
                change_type="model_added",
                entity_id=eid,
                new_value=r.model_name if r else eid,
                description=f"Model added to route: {r.model_name if r else eid}",
            ))

        for eid in removed:
            self.changes.append(ChangeRecord(
                change_type="model_removed",
                entity_id=eid,
                description=f"Model removed from route: {eid}",
            ))

    def _generate_config(self, router_output: RouterOutput) -> None:
        """Generate LiteLLM config YAML."""
        logger.info("Generating LiteLLM config...")
        generate_litellm_config_file(
            router_output,
            self.collected_endpoints,
            str(self.settings.output_dir / "litellm-config-sample.yaml"),
        )

    def _generate_reports(
        self,
        router_output: RouterOutput,
        previous_output: Optional[RouterOutput],
    ) -> None:
        """Generate all reports."""
        logger.info("Generating reports...")
        write_reports(
            router_output=router_output,
            ratings=self.ratings,
            endpoints=self.collected_endpoints,
            source_health=self.source_health,
            changes=self.changes,
            previous_output=previous_output,
            discovered_candidates=self.discovered_candidates,
            reports_dir=self.settings.reports_dir,
            source_attribution=self.aa_attribution,
        )
