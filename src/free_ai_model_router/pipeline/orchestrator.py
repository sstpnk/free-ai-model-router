"""Pipeline orchestrator — coordinates collect → verify → generate → report flow."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from free_ai_model_router.config_loader import Settings
from free_ai_model_router.generation.litellm_config import generate_litellm_config_file
from free_ai_model_router.generation.reports import generate_and_write_reports
from free_ai_model_router.http_client.client import HttpClient
from free_ai_model_router.models import (
    CanonicalModel,
    ChangeRecord,
    PipelineState,
    ProviderEndpoint,
    RouterOutput,
    RoutedEndpoint,
    SourceHealth,
    FreeStatus,
    VerificationStatus,
)
from free_ai_model_router.providers.base import ProviderModel
from free_ai_model_router.providers.cerebras import CerebrasAdapter
from free_ai_model_router.providers.gemini import GeminiAdapter
from free_ai_model_router.providers.groq import GroqAdapter
from free_ai_model_router.providers.mistral import MistralAdapter
from free_ai_model_router.providers.opencode_zen import OpenCodeZenAdapter
from free_ai_model_router.providers.openrouter import OpenRouterAdapter
from free_ai_model_router.providers.zai import ZAIAdapter
from free_ai_model_router.storage.state import (
    load_previous_output,
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
        self.changes: list[ChangeRecord] = []
        self.source_health: dict[str, SourceHealth] = {}

    async def run_all(
        self,
        *,
        use_cache: bool = True,
        no_runtime_checks: bool = False,
        offline: bool = False,
    ) -> PipelineState:
        """Run the complete pipeline: collect → verify → generate → report."""
        logger.info("Starting full pipeline run")
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

            # Step 2: Verify models (if keys configured and checks not disabled)
            if not no_runtime_checks and not offline:
                await self._verify_models()
                # Strip failed models
                before = len(self.collected_endpoints)
                self.collected_endpoints = [
                    ep for ep in self.collected_endpoints
                    if ep.runtime_check.status == VerificationStatus.SUCCESS
                ]
                dropped = before - len(self.collected_endpoints)
                if dropped:
                    logger.info("Dropped %d endpoints that failed verification", dropped)

            # Step 3: Build router output
            router_output = self._build_router()

            # Step 4: Generate LiteLLM config
            self._generate_config(router_output)

            # Step 5: Generate reports
            previous_output = load_previous_output(self.settings.output_dir / "latest.json")
            self._detect_changes(router_output, previous_output)
            self._generate_reports(router_output, previous_output)

            # Step 6: Save state
            save_router_output(router_output, self.settings.output_dir / "latest.json")

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
        """Discover models from configured providers, keep only :free models."""
        assert self.http is not None
        adapters = self._init_adapters()
        all_models: list[ProviderModel] = []
        logger.info("Collecting models from %d providers...", len(adapters))

        # Track seen canonical model IDs to avoid duplicates
        seen_canonical_ids = set()

        for adapter in adapters:
            try:
                models = await adapter.discover_models()
                all_models.extend(models)
                for m in models:
                    # Keep only :free suffix models
                    if ":free" not in m.provider_model_id:
                        continue

                    ep = adapter.to_provider_endpoint(m)
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
                        
                logger.info("  %s: discovered %d models (%d with :free suffix)", 
                           adapter.provider_id, len(models), 
                           sum(1 for m in models if ":free" in m.provider_model_id))
            except Exception as e:
                logger.warning("  %s: collection failed: %s", adapter.provider_id, e)
                self.state.errors.append(f"Provider {adapter.provider_id}: {e}")

        # Source health tracking
        self.source_health["provider_discovery"] = SourceHealth(
            source_id="provider_discovery",
            last_success_at=datetime.now(timezone.utc),
            consecutive_failures=0,
        )
        logger.info("Total: %d :free endpoints from %d providers, %d unique canonical models", 
                   len(self.collected_endpoints), len(adapters), len(seen_canonical_ids))

    def _init_adapters(self) -> list:
        """Initialize provider adapters based on config, passing API keys if available."""
        assert self.http is not None
        adapters = []
        adapter_map = {
            "openrouter": OpenRouterAdapter,
            "opencode_zen": OpenCodeZenAdapter,
            "zai": ZAIAdapter,
            "groq": GroqAdapter,
            "cerebras": CerebrasAdapter,
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



    async def _verify_models(self) -> None:
        """Verify endpoints with actual API calls where keys are available."""
        assert self.http is not None
        logger.info("Verifying models with API calls...")

        adapters = self._init_adapters()
        adapter_by_id = {a.provider_id: a for a in adapters}

        # Build list of (endpoint, adapter, api_key) triples to verify
        to_verify: list[tuple[ProviderEndpoint, Any, str]] = []
        for endpoint in self.collected_endpoints:
            provider_id = endpoint.provider_id
            api_key = self.settings.get_provider_api_key(provider_id)

            if not api_key:
                endpoint.runtime_check.checked = False
                endpoint.runtime_check.status = VerificationStatus.NOT_TESTED
                continue

            adapter = adapter_by_id.get(provider_id)
            if not adapter:
                continue
            to_verify.append((endpoint, adapter, api_key))

        # Verify in parallel with concurrency limit
        sem = asyncio.Semaphore(10)

        async def _verify_one(
            endpoint: ProviderEndpoint,
            adapter: Any,
            api_key: str,
        ) -> None:
            async with sem:
                pm = ProviderModel(
                    provider_model_id=endpoint.provider_model_id,
                    api_base=endpoint.api_base,
                )
                try:
                    result = await asyncio.wait_for(adapter.verify_model(pm, api_key), timeout=20)
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
                                 endpoint.provider_id, endpoint.provider_model_id,
                                 result.status.value, result.latency_ms or 0)
                except Exception as e:
                    logger.warning("  %s/%s verification failed: %s",
                                   endpoint.provider_id, endpoint.provider_model_id, e)
                    endpoint.runtime_check.checked = True
                    endpoint.runtime_check.status = VerificationStatus.PROVIDER_UNAVAILABLE

        await asyncio.gather(*(_verify_one(ep, ad, ak) for ep, ad, ak in to_verify))

        self.source_health["api_verification"] = SourceHealth(
            source_id="api_verification",
            last_success_at=datetime.now(timezone.utc),
        )
        logger.info("  Verification complete")



    def _build_router(self) -> RouterOutput:
        """Build the router output with verified :free endpoints."""
        logger.info("Building router output...")

        FREE_STATUSES = {
            FreeStatus.VERIFIED_FREE,
            FreeStatus.DOCUMENTED_FREE,
            FreeStatus.ACCOUNT_SPECIFIC_FREE,
            FreeStatus.TEMPORARY_FREE,
        }

        routed: list[RoutedEndpoint] = []
        for ep in self.collected_endpoints:
            if ep.free_status not in FREE_STATUSES:
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
                tool_calling=tool_calling,
                modalities=modalities,
            ))

        return RouterOutput(
            generated_at=datetime.now(timezone.utc),
            endpoints=routed,
            fallback_chain=[r.endpoint_id for r in routed],
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
        """Generate reports (models.md and changes.md)."""
        logger.info("Generating reports...")
        generate_and_write_reports(
            router_output=router_output,
            endpoints=self.collected_endpoints,
            changes=self.changes,
            previous_output=previous_output,
            reports_dir=self.settings.reports_dir,
        )
