"""Base ProviderAdapter protocol and shared types."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Protocol

from free_ai_model_router.models import (
    ApiStyle,
    FreeStatus,
    Limits,
    Modality,
    ProviderEndpoint,
    RuntimeCheck,
    VerificationStatus,
)


@dataclass
class ProviderModel:
    """Raw model discovered from a provider."""

    provider_model_id: str
    name: Optional[str] = None
    litellm_model: Optional[str] = None
    api_base: Optional[str] = None
    api_style: ApiStyle = ApiStyle.OPENAI_COMPATIBLE
    context_tokens: Optional[int] = None
    max_output_tokens: Optional[int] = None
    free_status: FreeStatus = FreeStatus.UNKNOWN
    limits: Limits = field(default_factory=Limits)
    tool_calling: bool = False
    modalities: Optional[list[Modality]] = None
    raw_data: Optional[dict] = None


@dataclass
class PricingRecord:
    """Pricing information for a model."""

    provider_model_id: str
    input_price_per_million: Optional[float] = None
    output_price_per_million: Optional[float] = None
    cache_input_price_per_million: Optional[float] = None
    free_input: bool = False
    free_output: bool = False
    requires_subscription: bool = False
    requires_credit_card: bool = False
    trial_credit: bool = False
    promotion_end_date: Optional[str] = None
    source_url: Optional[str] = None


@dataclass
class LimitRecord:
    """Rate/quota limit information."""

    provider_model_id: str
    requests_per_minute: Optional[int] = None
    requests_per_day: Optional[int] = None
    tokens_per_minute: Optional[int] = None
    tokens_per_day: Optional[int] = None
    concurrent_requests: Optional[int] = None
    shared_quota_group: Optional[str] = None
    source_url: Optional[str] = None


@dataclass
class VerificationResult:
    """Result of a model verification call."""

    provider_model_id: str
    status: VerificationStatus
    latency_ms: Optional[int] = None
    http_status: Optional[int] = None
    error_message: Optional[str] = None
    tool_calling_verified: bool = False


class ProviderAdapter(Protocol):
    """Protocol that all provider adapters must implement."""

    provider_id: str

    async def discover_models(self) -> list[ProviderModel]:
        """Fetch available models from this provider."""
        ...

    async def fetch_pricing(self) -> list[PricingRecord]:
        """Fetch pricing information."""
        ...

    async def fetch_limits(self) -> list[LimitRecord]:
        """Fetch rate/usage limits."""
        ...

    async def verify_model(self, model: ProviderModel, api_key: str) -> VerificationResult:
        """Verify a model is accessible and working."""
        ...

    def to_provider_endpoint(self, model: ProviderModel) -> ProviderEndpoint:
        """Convert discovered model to a full ProviderEndpoint."""
        ...

    def to_litellm_model_string(self, model: ProviderModel) -> str:
        """Convert to LiteLLM-compatible model string."""
        ...
