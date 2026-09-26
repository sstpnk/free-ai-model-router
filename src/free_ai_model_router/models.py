"""Pydantic data models for Free AI Model Router."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field

# --- Enums ---


class FreeStatus(str, Enum):
    """Classification of a model's free access status."""

    VERIFIED_FREE = "verified_free"
    DOCUMENTED_FREE = "documented_free"
    ACCOUNT_SPECIFIC_FREE = "account_specific_free"
    TEMPORARY_FREE = "temporary_free"
    TRIAL_CREDIT = "trial_credit"
    UNKNOWN = "unknown"
    PAID = "paid"
    UNAVAILABLE = "unavailable"


class Availability(str, Enum):
    """API availability of a model endpoint."""

    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"
    DEPRECATED = "deprecated"
    REMOVED = "removed"


class ApiStyle(str, Enum):
    """Type of API protocol."""

    OPENAI_COMPATIBLE = "openai_compatible"
    GOOGLE_AI = "google_ai"
    ANTHROPIC = "anthropic"
    COHERE = "cohere"
    BEDROCK = "bedrock"
    CUSTOM = "custom"


class VerificationStatus(str, Enum):
    """Result of a runtime API check."""

    SUCCESS = "success"
    AUTHENTICATION_FAILED = "authentication_failed"
    RATE_LIMITED = "rate_limited"
    QUOTA_EXHAUSTED = "quota_exhausted"
    MODEL_NOT_FOUND = "model_not_found"
    REGION_BLOCKED = "region_blocked"
    CLIENT_RESTRICTED = "client_restricted"
    PROVIDER_UNAVAILABLE = "provider_unavailable"
    TIMEOUT = "timeout"
    INVALID_RESPONSE = "invalid_response"
    NOT_TESTED = "not_tested"


class AccessVerdict(str, Enum):
    """Human-facing interpretation of a runtime API check.

    A non-success generation probe can still prove that the endpoint exists.
    For example, HTTP 429 means the model is visible and access reached the
    provider, but the account/request is currently throttled.
    """

    USABLE_NOW = "usable_now"
    EXISTS_BUT_THROTTLED = "exists_but_throttled"
    QUOTA_EXHAUSTED_FOR_ACCOUNT = "quota_exhausted_for_account"
    NOT_ACCESSIBLE = "not_accessible"
    UNKNOWN = "unknown"


class Modality(str, Enum):
    """Content modality supported by a model."""

    TEXT = "text"
    IMAGE_ANALYSIS = "image_analysis"
    IMAGE_GENERATION = "image_generation"
    AUDIO_ANALYSIS = "audio_analysis"
    AUDIO_GENERATION = "audio_generation"
    VIDEO_ANALYSIS = "video_analysis"
    VIDEO_GENERATION = "video_generation"


class SourceType(str, Enum):
    """Trust level of a data source."""

    RUNTIME_VERIFIED = "runtime_verified"
    OFFICIAL_API = "official_api"
    OFFICIAL_DOCS = "official_docs"
    BENCHMARK_API = "benchmark_api"
    BENCHMARK_PAGE = "benchmark_page"
    AGGREGATOR = "aggregator"
    INFERRED = "inferred"
    MANUAL_OVERRIDE = "manual_override"


# --- Canonical Model ---


class Capabilities(BaseModel):
    """Capability flags for a canonical model."""

    tool_calling: bool = False
    structured_output: Optional[bool] = None
    modalities: list[Modality] = Field(default_factory=lambda: [Modality.TEXT])
    context_tokens: Optional[int] = None
    max_output_tokens: Optional[int] = None


class CanonicalModel(BaseModel):
    """A canonical model definition (developer's model, not provider-specific)."""

    canonical_model_id: str
    name: str
    creator: Optional[str] = None
    release_date: Optional[datetime] = None
    model_family: Optional[str] = None
    open_weights: bool = False
    capabilities: Capabilities = Field(default_factory=Capabilities)
    aliases: list[str] = Field(default_factory=list)


# --- Provider Endpoint ---


class Limits(BaseModel):
    """Rate and quota limits for an endpoint."""

    requests_per_minute: Optional[int] = None
    requests_per_day: Optional[int] = None
    tokens_per_minute: Optional[int] = None
    tokens_per_day: Optional[int] = None
    concurrent_requests: Optional[int] = None
    shared_quota_group: Optional[str] = None  # models sharing same daily quota


class RuntimeCheck(BaseModel):
    """Result of a single runtime API verification."""

    checked: bool = False
    status: VerificationStatus = VerificationStatus.NOT_TESTED
    access_verdict: AccessVerdict = AccessVerdict.UNKNOWN
    checked_at: Optional[datetime] = None
    latency_ms: Optional[int] = None
    http_status: Optional[int] = None
    retry_after_seconds: Optional[int] = None
    error_message: Optional[str] = None
    consecutive_failures: int = 0


class VerificationHistoryRecord(BaseModel):
    """Append-only evidence record for one runtime verification probe."""

    run_id: str
    checked_at: datetime
    endpoint_id: str
    provider_id: str
    canonical_model_id: str
    provider_model_id: str
    listed_in_models_api: bool = True
    status: VerificationStatus
    access_verdict: AccessVerdict
    http_status: Optional[int] = None
    latency_ms: Optional[int] = None
    retry_after_seconds: Optional[int] = None
    error_message: Optional[str] = None
    models_api_checked_at: Optional[datetime] = None
    models_api_source_url: Optional[str] = None


class ProviderAccessRecord(BaseModel):
    """Append-only evidence record for provider-level model listing access."""

    run_id: str
    checked_at: datetime
    provider_id: str
    api_key_present: bool
    models_api_checked: bool = False
    models_api_status: VerificationStatus = VerificationStatus.NOT_TESTED
    models_found: int = 0
    models_api_source_url: Optional[str] = None
    error_message: Optional[str] = None


class VerificationStats(BaseModel):
    """Aggregated verification history for one endpoint."""

    endpoint_id: str
    attempts: int = 0
    success_count: int = 0
    rate_limited_count: int = 0
    quota_exhausted_count: int = 0
    client_restricted_count: int = 0
    hard_failure_count: int = 0
    success_rate: float = 0.0
    last_checked_at: Optional[datetime] = None
    last_success_at: Optional[datetime] = None
    p50_latency_ms: Optional[int] = None
    p95_latency_ms: Optional[int] = None


class ProviderEndpoint(BaseModel):
    """A specific model endpoint at a provider."""

    endpoint_id: str
    provider_id: str
    canonical_model_id: str
    provider_model_id: str
    litellm_model: Optional[str] = None
    api_base: Optional[str] = None
    api_style: ApiStyle = ApiStyle.OPENAI_COMPATIBLE
    availability: Availability = Availability.AVAILABLE
    free_status: FreeStatus = FreeStatus.UNKNOWN
    limits: Limits = Field(default_factory=Limits)
    context_tokens: Optional[int] = None
    max_output_tokens: Optional[int] = None
    listed_in_models_api: bool = True
    models_api_checked_at: Optional[datetime] = None
    models_api_source_url: Optional[str] = None
    runtime_check: RuntimeCheck = Field(default_factory=RuntimeCheck)
    discovered_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    source_url: Optional[str] = None


# --- Provider Config ---


class ProviderSourceUrls(BaseModel):
    """Known URLs for a provider's data sources."""

    models_api: Optional[str] = None
    pricing_page: Optional[str] = None
    docs: Optional[str] = None
    changelog: Optional[str] = None
    status: Optional[str] = None
    models_page: Optional[str] = None


class ProviderConfig(BaseModel):
    """Configuration entry for a single provider."""

    provider_id: str
    name: str
    website: Optional[str] = None
    api_base: Optional[str] = None
    api_style: ApiStyle = ApiStyle.OPENAI_COMPATIBLE
    adapter: Optional[str] = None
    discovery_priority: int = 100
    enabled: bool = True
    api_key_required: bool = True
    sources: ProviderSourceUrls = Field(default_factory=ProviderSourceUrls)


class ProviderConfigList(BaseModel):
    """Root model for providers.yaml."""

    providers: list[ProviderConfig]


# --- Source Config ---


class SourceConfig(BaseModel):
    """Configuration entry for a data source."""

    source_id: str
    name: str
    type: str
    base_url: Optional[str] = None
    url: Optional[str] = None
    priority: int = 1
    cache_ttl_minutes: int = 360
    staleness_threshold_minutes: int = 1440
    auth_type: str = "none"
    endpoints: dict[str, str] = Field(default_factory=dict)


class SourceConfigList(BaseModel):
    """Root model for sources.yaml."""

    sources: list[SourceConfig]


# --- Manual Override ---


class ManualOverride(BaseModel):
    """A single manual override entry."""

    canonical_model_id: str
    field: str
    value: Any
    reason: str
    source: str
    added_at: str
    expires_at: Optional[str] = None


class ManualOverrideList(BaseModel):
    """Root model for manual-overrides.yaml."""

    overrides: list[ManualOverride] = Field(default_factory=list)


# --- Pipeline State ---


class SourceHealth(BaseModel):
    """Health state of a single data source."""

    source_id: str
    last_success_at: Optional[datetime] = None
    consecutive_failures: int = 0
    last_error: Optional[str] = None
    last_error_type: Optional[str] = None
    data_freshness: Optional[str] = None
    staleness_threshold_minutes: int = 1440


class PipelineState(BaseModel):
    """Full pipeline execution state."""

    run_id: str = Field(default_factory=lambda: uuid.uuid4().hex[:12])
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None
    success: bool = False
    partial_success: bool = False
    errors: list[str] = Field(default_factory=list)
    source_health: dict[str, SourceHealth] = Field(default_factory=dict)


# --- Aggregated Output ---


class RoutedEndpoint(BaseModel):
    """A model endpoint selected for the routing table.

    No score/rank - models pass through after :free filter + verification.
    """

    endpoint_id: str
    provider_id: str
    provider_name: str
    canonical_model_id: str
    model_name: str
    free_status: FreeStatus
    runtime_status: VerificationStatus = VerificationStatus.NOT_TESTED
    access_verdict: AccessVerdict = AccessVerdict.UNKNOWN
    latency_ms: Optional[int] = None
    last_checked_at: Optional[datetime] = None
    tool_calling: bool = False
    modalities: list[str] = Field(default_factory=list)


class RouterOutput(BaseModel):
    """Output of the router - sorted list of verified free endpoints."""

    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    endpoints: list[RoutedEndpoint] = Field(default_factory=list)
    fallback_chain: list[str] = Field(default_factory=list)


# --- Change Tracking ---


class ChangeRecord(BaseModel):
    """A single detected change between runs."""

    change_type: str  # provider_added, model_added, model_removed
    entity_id: str
    old_value: Optional[str] = None
    new_value: Optional[str] = None
    description: str
