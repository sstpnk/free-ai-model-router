"""Tests for TinyLLM config generation."""

import yaml

from free_ai_model_router.generation.tinyllm_config import generate_tinyllm_config
from free_ai_model_router.models import (
    AccessVerdict,
    ApiStyle,
    FreeStatus,
    ProviderConfig,
    ProviderEndpoint,
    RoutedEndpoint,
    RouterOutput,
    VerificationStatus,
)
from free_ai_model_router.policy.free_candidates import annotate_free_candidate


def _endpoint(provider: str, model: str, api_base: str) -> ProviderEndpoint:
    return annotate_free_candidate(ProviderEndpoint(
        endpoint_id=f"{provider}/{model}",
        provider_id=provider,
        canonical_model_id=f"{provider}/{model}",
        provider_model_id=model,
        api_base=api_base,
        api_style=ApiStyle.OPENAI_COMPATIBLE,
        free_status=FreeStatus.VERIFIED_FREE,
    ))


def _routed(provider: str, model: str, *, tool_calling: bool = True) -> RoutedEndpoint:
    return RoutedEndpoint(
        endpoint_id=f"{provider}/{model}",
        provider_id=provider,
        provider_name=provider,
        canonical_model_id=f"{provider}/{model}",
        model_name=model,
        free_status=FreeStatus.VERIFIED_FREE,
        runtime_status=VerificationStatus.SUCCESS,
        access_verdict=AccessVerdict.USABLE_NOW,
        tool_calling=tool_calling,
        modalities=["text"],
    )


def test_generate_tinyllm_config_matches_current_tinyllm_sections() -> None:
    endpoints = {
        "opencode_zen/ling-3.0-flash-fin-free": _endpoint(
            "opencode_zen",
            "ling-3.0-flash-fin-free",
            "https://opencode.ai/zen/v1",
        ),
        "openrouter/poolside/laguna-s-2.1:free": _endpoint(
            "openrouter",
            "poolside/laguna-s-2.1:free",
            "https://openrouter.ai/api/v1",
        ),
    }
    router_output = RouterOutput(
        endpoints=[
            _routed("opencode_zen", "ling-3.0-flash-fin-free"),
            _routed("openrouter", "poolside/laguna-s-2.1:free"),
        ]
    )

    generated = yaml.safe_load(generate_tinyllm_config(router_output, endpoints))

    assert generated["routing"] == {
        "cooldown_seconds": 300,
        "max_attempts": 6,
        "min_requests_for_trust": 20,
        "min_success_rate": 0.5,
        "max_empty_rate": 0.3,
        "min_score": 0.0,
    }
    assert generated["timeouts"] == {
        "connect_seconds": 30,
        "response_seconds": 120,
        "stream_idle_seconds": 180,
    }
    assert generated["providers"]["opencode-zen"] == {
        "type": "openai-compatible",
        "base_url": "https://opencode.ai/zen/v1",
        "api_key_env": "OPENCODE_ZEN_API_KEY",
        "headers": {"User-Agent": "OpenAI/JS 6.45.0"},
    }
    assert generated["providers"]["openrouter"]["api_key_env"] == "OPENROUTER_API_KEY"
    assert generated["providers"]["openrouter"]["headers"] == {
        "HTTP-Referer": "https://llm.stpnk.tech",
        "X-Title": "TinyLLM",
    }
    assert generated["providers"]["deepseek2api"] == {
        "type": "openai-compatible",
        "base_url": "https://deepseek.stpnk.tech/v1",
        "api_key_env": "DEEPSEEK2API_API_KEY",
    }
    assert generated["routes"]["coding-auto"] == [
        {"provider": "opencode-zen", "model": "ling-3.0-flash-fin-free"},
        {"provider": "openrouter", "model": "poolside/laguna-s-2.1:free"},
        {"provider": "deepseek2api", "model": "deepseek-v4-flash"},
        {"provider": "deepseek2api", "model": "deepseek-v4-pro"},
    ]
    assert generated["routes"]["agent-auto"] == generated["routes"]["coding-auto"]


def test_generate_tinyllm_config_omits_secret_values() -> None:
    endpoint = _endpoint("zai", "glm-5.1", "https://api.z.ai/api/paas/v4")
    router_output = RouterOutput(endpoints=[_routed("zai", "glm-5.1")])

    config_text = generate_tinyllm_config(
        router_output,
        {"zai/glm-5.1": endpoint},
    )
    generated = yaml.safe_load(config_text)

    assert "api_key:" not in config_text
    assert "DEEPSEEK2API_API_KEY" in config_text
    assert generated["providers"]["z-ai"]["api_key_env"] == "ZAI_API_KEY"


def test_generate_tinyllm_config_limits_routes_to_max_attempts() -> None:
    endpoints = {}
    routed = []
    for index in range(8):
        model = f"model-{index}:free"
        endpoint_id = f"openrouter/{model}"
        endpoints[endpoint_id] = _endpoint("openrouter", model, "https://openrouter.ai/api/v1")
        routed.append(_routed("openrouter", model))
    router_output = RouterOutput(endpoints=routed)

    generated = yaml.safe_load(
        generate_tinyllm_config(router_output, endpoints, max_route_steps=6)
    )

    assert len(generated["routes"]["coding-auto"]) == 6
    assert generated["routes"]["coding-auto"][-2:] == [
        {"provider": "deepseek2api", "model": "deepseek-v4-flash"},
        {"provider": "deepseek2api", "model": "deepseek-v4-pro"},
    ]
    assert generated["routing"]["max_attempts"] == 6


def test_generate_tinyllm_config_falls_back_to_provider_registry() -> None:
    router_output = RouterOutput(
        endpoints=[_routed("openrouter", "poolside/laguna-s-2.1:free")]
    )
    provider = ProviderConfig(
        provider_id="openrouter",
        name="OpenRouter",
        api_base="https://openrouter.ai/api/v1",
        api_style=ApiStyle.OPENAI_COMPATIBLE,
    )

    generated = yaml.safe_load(
        generate_tinyllm_config(
            router_output,
            {},
            provider_configs_by_id={"openrouter": provider},
        )
    )

    assert generated["providers"]["openrouter"]["base_url"] == "https://openrouter.ai/api/v1"
    assert generated["routes"]["coding-auto"] == [
        {"provider": "openrouter", "model": "poolside/laguna-s-2.1:free"},
        {"provider": "deepseek2api", "model": "deepseek-v4-flash"},
        {"provider": "deepseek2api", "model": "deepseek-v4-pro"},
    ]
    assert generated["metadata"]["route_count"] == 3


def test_generate_tinyllm_config_skips_placeholder_provider_base_url() -> None:
    router_output = RouterOutput(endpoints=[_routed("cloudflare", "@cf/meta/llama-3.1-8b")])
    provider = ProviderConfig(
        provider_id="cloudflare",
        name="Cloudflare Workers AI",
        api_base="https://api.cloudflare.com/client/v4/accounts/{account_id}/ai/v1",
        api_style=ApiStyle.OPENAI_COMPATIBLE,
    )

    generated = yaml.safe_load(
        generate_tinyllm_config(
            router_output,
            {},
            provider_configs_by_id={"cloudflare": provider},
        )
    )

    assert generated["providers"] == {
        "deepseek2api": {
            "type": "openai-compatible",
            "base_url": "https://deepseek.stpnk.tech/v1",
            "api_key_env": "DEEPSEEK2API_API_KEY",
        }
    }
    assert generated["routes"]["coding-auto"] == [
        {"provider": "deepseek2api", "model": "deepseek-v4-flash"},
        {"provider": "deepseek2api", "model": "deepseek-v4-pro"},
    ]
    assert generated["metadata"]["route_count"] == 2


def test_generate_tinyllm_config_always_includes_static_deepseek2api_routes() -> None:
    generated = yaml.safe_load(generate_tinyllm_config(RouterOutput(), {}))

    assert generated["providers"]["deepseek2api"]["base_url"] == "https://deepseek.stpnk.tech/v1"
    assert generated["providers"]["deepseek2api"]["api_key_env"] == "DEEPSEEK2API_API_KEY"
    assert generated["routes"]["coding-auto"] == [
        {"provider": "deepseek2api", "model": "deepseek-v4-flash"},
        {"provider": "deepseek2api", "model": "deepseek-v4-pro"},
    ]
    assert generated["routes"]["coding-deepseek"] == generated["routes"]["coding-auto"]
