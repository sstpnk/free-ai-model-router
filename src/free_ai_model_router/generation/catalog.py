"""Machine-readable runtime catalog generation."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from free_ai_model_router.models import ProviderEndpoint, RouterOutput, VerificationStats


def generate_runtime_catalog(
    router_output: RouterOutput,
    endpoints_by_id: dict[str, ProviderEndpoint],
    verification_stats: dict[str, VerificationStats] | None = None,
) -> dict[str, Any]:
    """Build a compact catalog for local OpenAI-compatible routers."""
    verification_stats = verification_stats or {}
    catalog_endpoints: list[dict[str, Any]] = []
    for routed in router_output.endpoints:
        endpoint = endpoints_by_id.get(routed.endpoint_id)
        stats = verification_stats.get(routed.endpoint_id)
        catalog_endpoints.append(
            {
                "endpoint_id": routed.endpoint_id,
                "provider_id": routed.provider_id,
                "canonical_model_id": routed.canonical_model_id,
                "model": routed.model_name,
                "litellm_model": endpoint.litellm_model if endpoint else None,
                "api_base": endpoint.api_base if endpoint else None,
                "api_style": endpoint.api_style.value if endpoint else None,
                "free_status": routed.free_status.value,
                "runtime_status": routed.runtime_status.value,
                "access_verdict": routed.access_verdict.value,
                "latency_ms": routed.latency_ms,
                "last_checked_at": routed.last_checked_at.isoformat() if routed.last_checked_at else None,
                "retry_after_seconds": (
                    endpoint.runtime_check.retry_after_seconds
                    if endpoint
                    else None
                ),
                "limits": endpoint.limits.model_dump() if endpoint else {},
                "reliability": stats.model_dump(mode="json") if stats else None,
                "tool_calling": routed.tool_calling,
                "modalities": routed.modalities,
            }
        )
    return {
        "schema_version": 1,
        "generated_at": router_output.generated_at.isoformat(),
        "endpoint_count": len(catalog_endpoints),
        "fallback_chain": router_output.fallback_chain,
        "endpoints": catalog_endpoints,
    }


def generate_runtime_catalog_file(
    router_output: RouterOutput,
    endpoints: list[ProviderEndpoint],
    path: Path,
    verification_stats: dict[str, VerificationStats] | None = None,
) -> None:
    """Write runtime catalog JSON to disk."""
    path.parent.mkdir(parents=True, exist_ok=True)
    endpoints_by_id = {endpoint.endpoint_id: endpoint for endpoint in endpoints}
    catalog = generate_runtime_catalog(router_output, endpoints_by_id, verification_stats)
    path.write_text(json.dumps(catalog, indent=2, ensure_ascii=False), encoding="utf-8")
