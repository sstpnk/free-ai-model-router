"""TinyLLM dynamic routing config generation."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from free_ai_model_router.models import (
    ApiStyle,
    ProviderConfig,
    ProviderEndpoint,
    RoutedEndpoint,
    RouterOutput,
)


class _NoAliasDumper(yaml.SafeDumper):
    def ignore_aliases(self, data: Any) -> bool:
        return True


TINYLLM_ROUTING_DEFAULTS = {
    "cooldown_seconds": 300,
    "max_attempts": 6,
    "min_requests_for_trust": 20,
    "min_success_rate": 0.5,
    "max_empty_rate": 0.3,
    "min_score": 0.0,
}

TINYLLM_TIMEOUT_DEFAULTS = {
    "connect_seconds": 30,
    "response_seconds": 120,
    "stream_idle_seconds": 180,
}

TINYLLM_ROUTE_NAMES = (
    "agent-auto",
    "coding-auto",
    "agent-auto-pay",
    "coding-auto-pay",
)


def _tinyllm_provider_name(provider_id: str) -> str:
    aliases = {
        "opencode_zen": "opencode-zen",
        "zai": "z-ai",
    }
    return aliases.get(provider_id, provider_id.replace("_", "-"))


def _provider_headers(provider_name: str) -> dict[str, str]:
    if provider_name == "opencode-zen":
        return {"User-Agent": "OpenAI/JS 6.45.0"}
    if provider_name == "openrouter":
        return {
            "HTTP-Referer": "https://llm.stpnk.tech",
            "X-Title": "TinyLLM",
        }
    return {}


def _is_supported_openai_base(api_style: ApiStyle, api_base: str | None) -> bool:
    if api_style != ApiStyle.OPENAI_COMPATIBLE:
        return False
    if not api_base:
        return False
    return "{" not in api_base and "}" not in api_base


def _provider_config(endpoint: ProviderEndpoint) -> dict[str, Any] | None:
    if not _is_supported_openai_base(endpoint.api_style, endpoint.api_base):
        return None

    provider_name = _tinyllm_provider_name(endpoint.provider_id)
    config: dict[str, Any] = {
        "type": "openai-compatible",
        "base_url": endpoint.api_base.rstrip("/"),
        "api_key_env": f"{endpoint.provider_id.upper()}_API_KEY",
    }
    headers = _provider_headers(provider_name)
    if headers:
        config["headers"] = headers
    return config


def _fallback_endpoint(
    routed: RoutedEndpoint,
    providers_by_id: dict[str, ProviderConfig],
) -> ProviderEndpoint | None:
    provider = providers_by_id.get(routed.provider_id)
    if provider is None:
        return None
    if not _is_supported_openai_base(provider.api_style, provider.api_base):
        return None
    return ProviderEndpoint(
        endpoint_id=routed.endpoint_id,
        provider_id=routed.provider_id,
        canonical_model_id=routed.canonical_model_id,
        provider_model_id=routed.model_name,
        api_base=provider.api_base,
        api_style=provider.api_style,
        free_status=routed.free_status,
    )


def _route_step(endpoint: ProviderEndpoint) -> dict[str, str]:
    return {
        "provider": _tinyllm_provider_name(endpoint.provider_id),
        "model": endpoint.provider_model_id,
    }


def _dedupe_steps(steps: list[dict[str, str]]) -> list[dict[str, str]]:
    seen: set[tuple[str, str]] = set()
    unique: list[dict[str, str]] = []
    for step in steps:
        key = (step["provider"], step["model"])
        if key in seen:
            continue
        seen.add(key)
        unique.append(step)
    return unique


def _coding_deepseek_steps(steps: list[dict[str, str]]) -> list[dict[str, str]]:
    return [
        step for step in steps
        if "deepseek" in step["provider"].lower() or "deepseek" in step["model"].lower()
    ]


def generate_tinyllm_config(
    router_output: RouterOutput,
    endpoints_by_id: dict[str, ProviderEndpoint],
    *,
    provider_configs_by_id: dict[str, ProviderConfig] | None = None,
    max_route_steps: int = TINYLLM_ROUTING_DEFAULTS["max_attempts"],
) -> str:
    """Generate a TinyLLM-compatible YAML config fragment from routed endpoints."""
    provider_configs_by_id = provider_configs_by_id or {}
    selected_endpoints: list[ProviderEndpoint] = []
    for routed in router_output.endpoints:
        endpoint = endpoints_by_id.get(routed.endpoint_id) or _fallback_endpoint(
            routed,
            provider_configs_by_id,
        )
        if not endpoint:
            continue
        if not _is_supported_openai_base(endpoint.api_style, endpoint.api_base):
            continue
        selected_endpoints.append(endpoint)

    provider_configs: dict[str, dict[str, Any]] = {}
    steps: list[dict[str, str]] = []
    for endpoint in selected_endpoints:
        provider_name = _tinyllm_provider_name(endpoint.provider_id)
        provider_config = _provider_config(endpoint)
        if provider_config is None:
            continue
        provider_configs.setdefault(provider_name, provider_config)
        steps.append(_route_step(endpoint))

    steps = _dedupe_steps(steps)[:max_route_steps]
    agent_steps = _dedupe_steps(
        sorted(
            steps,
            key=lambda step: (
                not next(
                    (
                        routed.tool_calling for routed in router_output.endpoints
                        if _tinyllm_provider_name(routed.provider_id) == step["provider"]
                        and routed.model_name == step["model"]
                    ),
                    False,
                ),
                step["provider"],
                step["model"],
            ),
        )
    )[:max_route_steps]
    deepseek_steps = _coding_deepseek_steps(steps)[:max_route_steps]

    routes = {
        route_name: list(agent_steps if route_name.startswith("agent") else steps)
        for route_name in TINYLLM_ROUTE_NAMES
    }
    if deepseek_steps:
        routes["coding-deepseek"] = deepseek_steps

    payload: dict[str, Any] = {
        "metadata": {
            "schema_version": 1,
            "generated_by": "free-ai-model-router",
            "generated_at": router_output.generated_at.isoformat(),
            "source_output": "output/free-router-catalog.json",
            "route_count": len(steps),
            "secrets_policy": "api keys are referenced by env var name only",
        },
        "routing": dict(TINYLLM_ROUTING_DEFAULTS),
        "timeouts": dict(TINYLLM_TIMEOUT_DEFAULTS),
        "providers": provider_configs,
        "routes": routes,
    }
    return yaml.dump(payload, Dumper=_NoAliasDumper, sort_keys=False, allow_unicode=True)


def generate_tinyllm_config_file(
    router_output: RouterOutput,
    endpoints: list[ProviderEndpoint],
    path: Path,
    *,
    providers: list[ProviderConfig] | None = None,
) -> None:
    """Write TinyLLM YAML config fragment to disk."""
    path.parent.mkdir(parents=True, exist_ok=True)
    endpoints_by_id = {endpoint.endpoint_id: endpoint for endpoint in endpoints}
    provider_configs_by_id = {
        provider.provider_id: provider
        for provider in providers or []
    }
    path.write_text(
        generate_tinyllm_config(
            router_output,
            endpoints_by_id,
            provider_configs_by_id=provider_configs_by_id,
        ),
        encoding="utf-8",
    )
