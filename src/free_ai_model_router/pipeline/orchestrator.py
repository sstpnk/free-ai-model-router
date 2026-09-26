"""Pipeline orchestrator — coordinates collect → verify → generate → report flow."""

from __future__ import annotations

import asyncio
import logging
from collections import defaultdict
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from free_ai_model_router.config_loader import Settings
from free_ai_model_router.generation.catalog import generate_runtime_catalog_file
from free_ai_model_router.generation.litellm_config import generate_litellm_config_file
from free_ai_model_router.generation.reports import generate_and_write_reports
from free_ai_model_router.http_client.client import HttpClient
from free_ai_model_router.models import (
    ApiStyle,
    CanonicalModel,
    ChangeRecord,
    PipelineState,
    ProviderAccessRecord,
    ProviderEndpoint,
    RoutedEndpoint,
    RouterOutput,
    SourceHealth,
    VerificationStatus,
)
from free_ai_model_router.policy.free_candidates import annotate_free_candidate
from free_ai_model_router.providers.base import ProviderModel
from free_ai_model_router.providers.cerebras import CerebrasAdapter
from free_ai_model_router.providers.cloudflare import CloudflareAdapter
from free_ai_model_router.providers.deepinfra import DeepInfraAdapter
from free_ai_model_router.providers.gemini import GeminiAdapter
from free_ai_model_router.providers.groq import GroqAdapter
from free_ai_model_router.providers.mistral import MistralAdapter
from free_ai_model_router.providers.openai_compatible import GenericOpenAICompatibleAdapter
from free_ai_model_router.providers.opencode_zen import OpenCodeZenAdapter
from free_ai_model_router.providers.openrouter import OpenRouterAdapter
from free_ai_model_router.providers.zai import ZAIAdapter
from free_ai_model_router.storage.state import (
    append_provider_access_history,
    append_verification_history,
    load_latest_provider_access_records,
    load_latest_verification_records,
    load_previous_output,
    load_verification_stats,
    save_pipeline_state,
    save_router_output,
)
from free_ai_model_router.verification.status import (
    access_verdict_for_status,
    is_evidence_status,
    is_routable_status,
)

logger = logging.getLogger(__name__)

RECENT_SUCCESS_TTL = timedelta(hours=12)
DEFAULT_PROVIDER_VERIFY_CONCURRENCY = 1


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
        self.http: HttpClient | None = None
        self.collected_models: list[CanonicalModel] = []
        self.collected_endpoints: list[ProviderEndpoint] = []
        self.changes: list[ChangeRecord] = []
        self.source_health: dict[str, SourceHealth] = {}
        self.verification_stats = {}
        self.provider_errors: dict[str, str] = {}
        self.provider_access_records: list[ProviderAccessRecord] = []

    async def run_all(
        self,
        *,
        use_cache: bool = True,
        no_runtime_checks: bool = False,
        offline: bool = False,
        provider_ids: set[str] | None = None,
        max_verification_probes: int | None = None,
        free_candidates_only: bool = True,
    ) -> PipelineState:
        """Run the complete pipeline: collect → verify → generate → report."""
        logger.info("Starting full pipeline run")
        if provider_ids:
            logger.info("Provider filter active: %s", ", ".join(sorted(provider_ids)))
        self.state = PipelineState()

        try:
            # Initialize HTTP client with SSRF protection
            allowed_domains = [
                "openrouter.ai", "opencode.ai", "opencode.cloud", "z.ai",
                "api.groq.com", "generativelanguage.googleapis.com",
                "api.mistral.ai", "api.openai.com",
                "api.anthropic.com", "api.x.ai",
                "github.com", "raw.githubusercontent.com", "docs.litellm.ai",
                "models.inference.ai.azure.com",
                "api.cloudflare.com", "api.cerebras.ai",
                "api.sambanova.ai", "api.together.xyz",
                "api.fireworks.ai", "api.deepinfra.com",
                "api.siliconflow.cn", "api.studio.nebius.ai",
                "api.hyperbolic.xyz", "api.replicate.com",
                "api.cohere.com", "api.deepseek.com",
                "api.z.ai",
                "huggingface.co",
            ]
            self.http = HttpClient(
                cache_dir=self.settings.cache_dir,
                allowed_domains=allowed_domains,
            )

            # Step 1: Collect from providers
            if not offline:
                await self._collect_providers(provider_ids)
            else:
                logger.info("Offline mode: skipping provider collection")

            # Step 2: Verify models (if keys configured and checks not disabled)
            if not no_runtime_checks and not offline:
                await self._verify_models(
                    provider_ids,
                    max_verification_probes,
                    free_candidates_only=free_candidates_only,
                )
                evidence_count = sum(
                    1 for ep in self.collected_endpoints
                    if is_evidence_status(ep.runtime_check.status)
                )
                hard_fail_count = sum(
                    1 for ep in self.collected_endpoints
                    if ep.runtime_check.checked and not is_routable_status(ep.runtime_check.status)
                )
                logger.info(
                    "Verification evidence: %d endpoints; %d hard failures kept for reports",
                    evidence_count,
                    hard_fail_count,
                )
                history_count = append_verification_history(
                    endpoints=self.collected_endpoints,
                    run_id=self.state.run_id,
                    path=self.settings.history_dir / "verification.jsonl",
                    checked_after=self.state.started_at,
                )
                logger.info("Appended %d verification history records", history_count)

            access_history_count = append_provider_access_history(
                records=self.provider_access_records,
                path=self.settings.history_dir / "provider-access.jsonl",
            )
            logger.info("Appended %d provider access history records", access_history_count)

            self.verification_stats = load_verification_stats(self.settings.history_dir / "verification.jsonl")

            if provider_ids:
                self._generate_provider_status_reports()
                self._complete_state()
                return self.state

            # Step 3: Build router output
            router_output = self._build_router()

            # Step 4: Generate LiteLLM config
            self._generate_config(router_output)
            self._generate_runtime_catalog(router_output)

            # Step 5: Generate reports
            previous_output = load_previous_output(self.settings.output_dir / "latest.json")
            self._detect_changes(router_output, previous_output)
            self._generate_reports(router_output, previous_output)

            # Step 6: Save state
            save_router_output(router_output, self.settings.output_dir / "latest.json")

            self._complete_state()

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

    async def _collect_providers(self, provider_ids: set[str] | None = None) -> None:
        """Discover models from configured providers."""
        assert self.http is not None
        adapters = self._init_adapters(provider_ids)
        all_models: list[ProviderModel] = []
        logger.info("Collecting models from %d providers...", len(adapters))

        # Track seen canonical model IDs to avoid duplicates
        seen_canonical_ids = set()

        for adapter in adapters:
            try:
                collected_at = datetime.now(UTC)
                models = await adapter.discover_models()
                models_api_source_url = self._models_api_source_url(adapter.provider_id)
                self.provider_access_records.append(
                    ProviderAccessRecord(
                        run_id=self.state.run_id,
                        checked_at=collected_at,
                        provider_id=adapter.provider_id,
                        api_key_present=bool(self.settings.get_provider_api_key(adapter.provider_id)),
                        models_api_checked=True,
                        models_api_status=VerificationStatus.SUCCESS,
                        models_found=len(models),
                        models_api_source_url=models_api_source_url,
                    )
                )
                all_models.extend(models)
                for m in models:
                    ep = adapter.to_provider_endpoint(m)
                    annotate_free_candidate(ep)
                    ep.listed_in_models_api = True
                    ep.models_api_checked_at = collected_at
                    ep.models_api_source_url = (
                        ep.models_api_source_url
                        or ep.source_url
                        or models_api_source_url
                    )
                    self.collected_endpoints.append(ep)

                    # Build capabilities from provider model data
                    modalities_list = [mod.value for mod in m.modalities] if m.modalities else ["text"]

                    canonical = CanonicalModel(
                        canonical_model_id=ep.canonical_model_id,
                        name=m.name or m.provider_model_id,
                        creator=adapter.provider_id,
                        capabilities={
                            "tool_calling": m.tool_calling,
                            "modalities": modalities_list,
                            "context_tokens": m.context_tokens,
                        },
                    )

                    # Only add canonical model if we haven't seen this one before
                    if ep.canonical_model_id not in seen_canonical_ids:
                        self.collected_models.append(canonical)
                        seen_canonical_ids.add(ep.canonical_model_id)

                logger.info("  %s: discovered %d models",
                           adapter.provider_id, len(models))
            except Exception as e:
                logger.warning("  %s: collection failed: %s", adapter.provider_id, e)
                self.provider_errors[adapter.provider_id] = str(e)
                self.provider_access_records.append(
                    ProviderAccessRecord(
                        run_id=self.state.run_id,
                        checked_at=datetime.now(UTC),
                        provider_id=adapter.provider_id,
                        api_key_present=bool(self.settings.get_provider_api_key(adapter.provider_id)),
                        models_api_checked=True,
                        models_api_status=self._provider_access_status_for_error(str(e)),
                        models_found=0,
                        models_api_source_url=self._models_api_source_url(adapter.provider_id),
                        error_message=str(e),
                    )
                )
                self.state.errors.append(f"Provider {adapter.provider_id}: {e}")

        # Source health tracking
        self.source_health["provider_discovery"] = SourceHealth(
            source_id="provider_discovery",
                last_success_at=datetime.now(UTC),
            consecutive_failures=0,
        )
        logger.info("Total: %d endpoints from %d providers, %d unique canonical models",
                   len(self.collected_endpoints), len(adapters), len(seen_canonical_ids))

    def _models_api_source_url(self, provider_id: str) -> str | None:
        provider = next(
            (item for item in self.settings.providers.providers if item.provider_id == provider_id),
            None,
        )
        if provider is None:
            return None
        if provider.sources.models_api:
            return provider.sources.models_api
        if provider.api_base:
            return f"{provider.api_base.rstrip('/')}/models"
        return None

    def _provider_access_status_for_error(self, error_message: str) -> VerificationStatus:
        lower = error_message.lower()
        if "401" in lower or "403" in lower or "unauthorized" in lower or "forbidden" in lower:
            return VerificationStatus.AUTHENTICATION_FAILED
        if "429" in lower or "rate limit" in lower:
            return VerificationStatus.RATE_LIMITED
        if "404" in lower or "not found" in lower:
            return VerificationStatus.MODEL_NOT_FOUND
        if "timeout" in lower:
            return VerificationStatus.TIMEOUT
        return VerificationStatus.PROVIDER_UNAVAILABLE

    def _init_adapters(self, provider_ids: set[str] | None = None) -> list:
        """Initialize provider adapters based on config, passing API keys if available."""
        assert self.http is not None
        adapters = []
        adapter_map = {
            "openrouter": OpenRouterAdapter,
            "opencode_zen": OpenCodeZenAdapter,
            "zai": ZAIAdapter,
            "groq": GroqAdapter,
            "cerebras": CerebrasAdapter,
            "cloudflare": CloudflareAdapter,
            "deepinfra": DeepInfraAdapter,
            "gemini": GeminiAdapter,
            "mistral": MistralAdapter,
        }
        for provider in self.settings.providers.providers:
            if provider_ids and provider.provider_id not in provider_ids:
                continue
            if not provider.enabled:
                continue
            adapter_cls = adapter_map.get(provider.provider_id)
            if adapter_cls:
                api_key = self.settings.get_provider_api_key(provider.provider_id)
                adapters.append(adapter_cls(self.http, api_key=api_key))
                logger.info("  Initialized adapter: %s (key=%s)", provider.provider_id, "yes" if api_key else "no")
            elif provider.api_style == ApiStyle.OPENAI_COMPATIBLE:
                api_key = self.settings.get_provider_api_key(provider.provider_id)
                adapters.append(GenericOpenAICompatibleAdapter(self.http, provider, api_key=api_key))
                logger.info(
                    "  Initialized generic OpenAI-compatible adapter: %s (key=%s)",
                    provider.provider_id,
                    "yes" if api_key else "no",
                )

        return adapters



    async def _verify_models(
        self,
        provider_ids: set[str] | None = None,
        max_probes: int | None = None,
        *,
        free_candidates_only: bool = True,
    ) -> None:
        """Verify endpoints with actual API calls where keys are available."""
        assert self.http is not None
        logger.info("Verifying models with API calls...")

        adapters = self._init_adapters(provider_ids)
        adapter_by_id = {a.provider_id: a for a in adapters}
        latest_history = load_latest_verification_records(self.settings.history_dir / "verification.jsonl")
        now = datetime.now(UTC)
        skipped_recent = 0
        skipped_non_candidates = 0

        # Build list of (endpoint, adapter, api_key) triples to verify
        to_verify: list[tuple[ProviderEndpoint, Any, str]] = []
        for endpoint in self.collected_endpoints:
            provider_id = endpoint.provider_id
            if provider_ids and provider_id not in provider_ids:
                continue
            candidate = annotate_free_candidate(endpoint).free_candidate
            if free_candidates_only and not candidate.is_candidate:
                skipped_non_candidates += 1
                continue
            api_key = self.settings.get_provider_api_key(provider_id)

            if not api_key:
                endpoint.runtime_check.checked = False
                endpoint.runtime_check.status = VerificationStatus.NOT_TESTED
                continue

            historical = latest_history.get(endpoint.endpoint_id)
            if (
                historical
                and historical.status == VerificationStatus.SUCCESS
                and now - historical.checked_at <= RECENT_SUCCESS_TTL
            ):
                endpoint.runtime_check.checked = True
                endpoint.runtime_check.status = historical.status
                endpoint.runtime_check.access_verdict = historical.access_verdict
                endpoint.runtime_check.checked_at = historical.checked_at
                endpoint.runtime_check.latency_ms = historical.latency_ms
                endpoint.runtime_check.http_status = historical.http_status
                endpoint.runtime_check.retry_after_seconds = historical.retry_after_seconds
                endpoint.runtime_check.error_message = historical.error_message
                skipped_recent += 1
                continue

            adapter = adapter_by_id.get(provider_id)
            if not adapter:
                continue
            to_verify.append((endpoint, adapter, api_key))

        if max_probes is not None:
            to_verify = to_verify[:max_probes]

        provider_semaphores = defaultdict(lambda: asyncio.Semaphore(DEFAULT_PROVIDER_VERIFY_CONCURRENCY))
        provider_cooldowns: dict[str, datetime] = {}

        async def _verify_one(
            endpoint: ProviderEndpoint,
            adapter: Any,
            api_key: str,
        ) -> None:
            async with provider_semaphores[endpoint.provider_id]:
                cooldown_until = provider_cooldowns.get(endpoint.provider_id)
                if cooldown_until:
                    delay = (cooldown_until - datetime.now(UTC)).total_seconds()
                    if delay > 0:
                        logger.info("  %s: cooling down for %.1fs", endpoint.provider_id, delay)
                        await asyncio.sleep(delay)

                pm = ProviderModel(
                    provider_model_id=endpoint.provider_model_id,
                    api_base=endpoint.api_base,
                )
                try:
                    result = await asyncio.wait_for(adapter.verify_model(pm, api_key), timeout=20)
                    endpoint.runtime_check.checked = True
                    endpoint.runtime_check.status = result.status
                    endpoint.runtime_check.access_verdict = access_verdict_for_status(result.status)
                    endpoint.runtime_check.checked_at = datetime.now(UTC)
                    endpoint.runtime_check.latency_ms = result.latency_ms
                    endpoint.runtime_check.http_status = result.http_status
                    endpoint.runtime_check.retry_after_seconds = result.retry_after_seconds
                    endpoint.runtime_check.error_message = result.error_message
                    if result.retry_after_seconds and result.status in {
                        VerificationStatus.RATE_LIMITED,
                        VerificationStatus.QUOTA_EXHAUSTED,
                    }:
                        provider_cooldowns[endpoint.provider_id] = datetime.now(UTC) + timedelta(
                            seconds=result.retry_after_seconds
                        )
                    if is_evidence_status(result.status):
                        endpoint.runtime_check.consecutive_failures = 0
                    else:
                        endpoint.runtime_check.consecutive_failures += 1
                    logger.debug("  %s/%s: %s (%dms)",
                                 endpoint.provider_id, endpoint.provider_model_id,
                                 result.status.value, result.latency_ms or 0)
                except Exception as e:
                    logger.warning("  %s/%s verification failed: %s",
                                   endpoint.provider_id, endpoint.provider_model_id, e)
                    endpoint.runtime_check.checked = True
                    endpoint.runtime_check.status = VerificationStatus.PROVIDER_UNAVAILABLE
                    endpoint.runtime_check.access_verdict = access_verdict_for_status(
                        VerificationStatus.PROVIDER_UNAVAILABLE
                    )
                    endpoint.runtime_check.error_message = str(e)

        await asyncio.gather(*(_verify_one(ep, ad, ak) for ep, ad, ak in to_verify))

        self.source_health["api_verification"] = SourceHealth(
            source_id="api_verification",
            last_success_at=datetime.now(UTC),
        )
        logger.info(
            "  Verification complete: %d probed, %d reused from recent history, %d skipped as non-candidates",
            len(to_verify),
            skipped_recent,
            skipped_non_candidates,
        )



    def _build_router(self) -> RouterOutput:
        """Build the router output with verified :free endpoints."""
        logger.info("Building router output...")

        routed: list[RoutedEndpoint] = []
        for ep in self.collected_endpoints:
            candidate = annotate_free_candidate(ep).free_candidate
            if not candidate.route_eligible:
                continue
            if ep.runtime_check.checked and not is_routable_status(ep.runtime_check.status):
                continue
            # Look up capabilities from collected models
            tool_calling = False
            modalities = ["text"]
            for cm in self.collected_models:
                if cm.canonical_model_id == ep.canonical_model_id:
                    tool_calling = cm.capabilities.tool_calling
                    modalities = [m.value for m in cm.capabilities.modalities]
                    break

            routed.append(RoutedEndpoint(
                endpoint_id=ep.endpoint_id,
                provider_id=ep.provider_id,
                provider_name=ep.provider_id,
                canonical_model_id=ep.canonical_model_id,
                model_name=ep.provider_model_id,
                free_status=ep.free_status,
                free_candidate_reason=candidate.reason,
                free_candidate_source=candidate.source,
                runtime_status=ep.runtime_check.status,
                access_verdict=ep.runtime_check.access_verdict,
                latency_ms=ep.runtime_check.latency_ms,
                last_checked_at=ep.runtime_check.checked_at,
                tool_calling=tool_calling,
                modalities=modalities,
            ))

        return RouterOutput(
            generated_at=datetime.now(UTC),
            endpoints=routed,
            fallback_chain=[r.endpoint_id for r in routed],
        )

    def _detect_changes(
        self,
        current: RouterOutput,
        previous: RouterOutput | None,
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

        current_by_id = {r.endpoint_id: r for r in current.endpoints}
        previous_by_id = {r.endpoint_id: r for r in previous.endpoints}
        for eid in sorted(current_ids & previous_ids):
            current_endpoint = current_by_id[eid]
            previous_endpoint = previous_by_id[eid]
            current_state = f"{current_endpoint.runtime_status.value}/{current_endpoint.access_verdict.value}"
            previous_state = f"{previous_endpoint.runtime_status.value}/{previous_endpoint.access_verdict.value}"
            if current_state != previous_state:
                self.changes.append(ChangeRecord(
                    change_type="verification_status_changed",
                    entity_id=eid,
                    old_value=previous_state,
                    new_value=current_state,
                    description=f"Verification changed: {previous_state} -> {current_state}",
                ))

    def _generate_config(self, router_output: RouterOutput) -> None:
        """Generate LiteLLM config YAML."""
        logger.info("Generating LiteLLM config...")
        generate_litellm_config_file(
            router_output,
            self.collected_endpoints,
            str(self.settings.output_dir / "litellm-config-sample.yaml"),
        )

    def _generate_runtime_catalog(self, router_output: RouterOutput) -> None:
        """Generate machine-readable runtime catalog JSON."""
        logger.info("Generating runtime catalog...")
        generate_runtime_catalog_file(
            router_output,
            self.collected_endpoints,
            self.settings.output_dir / "free-router-catalog.json",
            self.verification_stats,
        )

    def _generate_reports(
        self,
        router_output: RouterOutput,
        previous_output: RouterOutput | None,
        *,
        write_routing_reports: bool = True,
    ) -> None:
        """Generate reports (models.md and changes.md)."""
        logger.info("Generating reports...")
        generate_and_write_reports(
            router_output=router_output,
            endpoints=self.collected_endpoints,
            changes=self.changes,
            previous_output=previous_output,
            reports_dir=self.settings.reports_dir,
            providers=self.settings.providers.providers,
            api_key_presence={
                provider.provider_id: bool(self.settings.get_provider_api_key(provider.provider_id))
                for provider in self.settings.providers.providers
            },
            verification_stats=self.verification_stats,
            provider_errors=self.provider_errors,
            provider_access_records=load_latest_provider_access_records(
                self.settings.history_dir / "provider-access.jsonl"
            ),
            provider_runtime_statuses=self._provider_runtime_statuses(),
            write_routing_reports=write_routing_reports,
        )

    def _generate_provider_status_reports(self) -> None:
        """Generate reports that are safe for provider-scoped verification."""
        logger.info("Generating provider status reports...")
        self._generate_reports(
            RouterOutput(),
            None,
            write_routing_reports=False,
        )

    def _provider_runtime_statuses(self) -> dict[str, list[VerificationStatus]]:
        latest_records = load_latest_verification_records(self.settings.history_dir / "verification.jsonl")
        statuses: dict[str, list[VerificationStatus]] = {}
        for record in latest_records.values():
            statuses.setdefault(record.provider_id, []).append(record.status)
        return statuses

    def _complete_state(self) -> None:
        self.state.success = not self.state.errors
        self.state.partial_success = bool(self.state.errors)
        self.state.completed_at = datetime.now(UTC)
        if self.state.success:
            logger.info("Pipeline run completed successfully")
        else:
            logger.warning("Pipeline run completed with %d errors", len(self.state.errors))
