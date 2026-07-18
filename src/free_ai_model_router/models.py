"""Pydantic data models for Free AI Model Router."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


# ─── Enums ──────────────────────────────────────────────────────────────────


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
    PROVIDER_UNAVAILABLE = "provider_unavailable"
    TIMEOUT = "timeout"
    INVALID_RESPONSE = "invalid_response"
    NOT_TESTED = "not_tested"


class ConfidenceLevel(str, Enum):
    """Confidence in a rating or data point."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class QualityBand(str, Enum):
    """Quality classification band."""

    EXCELLENT = "excellent"
    GOOD = "good"
    BELOW_THRESHOLD = "below_threshold"
    UNRATED = "unrated"


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


class ScoringMode(str, Enum):
    """Scoring engine computation mode."""

    COMPOSITE_PRIMARY = "composite_primary"
    COMPONENT_WEIGHTED = "component_weighted"


# ─── Typed value wrappers ───────────────────────────────────────────────────


class SourcedValue(BaseModel):
    """A scalar value with provenance metadata."""

    value: Any
    source_url: Optional[str] = None
    source_type: SourceType = SourceType.AGGREGATOR
    observed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM


# ─── Canonical Model ────────────────────────────────────────────────────────


class Capabilities(BaseModel):
    """Capability flags for a canonical model."""

    coding: bool = False
    reasoning: bool = False
    tool_calling: bool = False
    structured_output: Optional[bool] = None
    vision: bool = False
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


# ─── Provider Endpoint ──────────────────────────────────────────────────────


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
    checked_at: Optional[datetime] = None
    latency_ms: Optional[int] = None
    http_status: Optional[int] = None
    consecutive_failures: int = 0


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
    runtime_check: RuntimeCheck = Field(default_factory=RuntimeCheck)
    discovered_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    source_url: Optional[str] = None


# ─── Rating / Benchmark ─────────────────────────────────────────────────────


class BenchmarkScores(BaseModel):
    """Raw benchmark scores for a canonical model."""

    artificial_analysis_coding_agent_index: Optional[float] = None
    artificial_analysis_coding_index: Optional[float] = None
    terminal_bench_v2: Optional[float] = None
    deep_swe: Optional[float] = None
    swe_atlas_qna: Optional[float] = None
    intelligence_index: Optional[float] = None
    agentic_index: Optional[float] = None
    agent_harness: Optional[str] = None
    reasoning_setting: Optional[str] = None
    evaluated_at: Optional[datetime] = None
    source_url: Optional[str] = None


class NormalizedScores(BaseModel):
    """Normalized / computed scores."""

    coding_quality_percent: Optional[float] = None
    reliability_percent: Optional[float] = None
    final_router_score: Optional[float] = None
    penalties_applied: list[str] = Field(default_factory=list)


class ModelRating(BaseModel):
    """Aggregated rating for a canonical model."""

    canonical_model_id: str
    benchmark: BenchmarkScores = Field(default_factory=BenchmarkScores)
    normalized_scores: NormalizedScores = Field(default_factory=NormalizedScores)
    quality_band: QualityBand = QualityBand.UNRATED
    ranking_confidence: ConfidenceLevel = ConfidenceLevel.LOW


# ─── Provider Config ────────────────────────────────────────────────────────


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
    sources: ProviderSourceUrls = Field(default_factory=ProviderSourceUrls)


class ProviderConfigList(BaseModel):
    """Root model for providers.yaml."""

    providers: list[ProviderConfig]


# ─── Source Config ──────────────────────────────────────────────────────────


class SourceEndpoint(BaseModel):
    """Named API endpoint for a source."""

    path: str
    method: str = "GET"


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


# ─── Scoring Config ─────────────────────────────────────────────────────────


class ReferenceConfig(BaseModel):
    """Reference model for 100% score normalization."""

    name: str = "ChatGPT-5.6 Sol High"
    score_percent: float = 100.0
    artificial_analysis_model_id: Optional[str] = None
    manual_reference_value: Optional[float] = None


class RoutingConfig(BaseModel):
    """Routing preferences."""

    prefer_provider_diversity: bool = True
    disallow_shared_quota_as_independent_fallback: bool = True
    include_temporary_free: bool = True
    include_account_specific_free: bool = True


class WeightsConfig(BaseModel):
    """Weighting for scoring components."""

    coding_agent_index: float = 0.50
    coding_model_index: float = 0.20
    terminal_bench: float = 0.10
    repository_understanding: float = 0.08
    tool_calling: float = 0.05
    context_utility: float = 0.03
    endpoint_reliability: float = 0.03
    latency_and_speed: float = 0.01


class PenaltiesConfig(BaseModel):
    """Score penalties for various deficiencies."""

    no_tool_calling: float = -5.0
    unstable_structured_output: float = -3.0
    context_below_minimum: float = -8.0
    temporary_free: float = -2.0
    opaque_quota: float = -3.0
    two_consecutive_failures: float = -10.0
    low_match_confidence: float = -4.0
    trial_credit_only: float = -15.0
    unsupported_litellm_adapter: float = -5.0


class ScoringConfig(BaseModel):
    """Root model for scoring.yaml."""

    quality_threshold_percent: float = 70.0
    excellent_threshold_percent: float = 85.0
    low_confidence_threshold_percent: float = 75.0
    minimum_context_tokens: int = 128000
    reference: ReferenceConfig = Field(default_factory=ReferenceConfig)
    routing: RoutingConfig = Field(default_factory=RoutingConfig)
    scoring_mode: ScoringMode = ScoringMode.COMPOSITE_PRIMARY
    weights: WeightsConfig = Field(default_factory=WeightsConfig)
    penalties: PenaltiesConfig = Field(default_factory=PenaltiesConfig)


# ─── Manual Override ────────────────────────────────────────────────────────


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


# ─── Pipeline State ─────────────────────────────────────────────────────────


class SourceHealth(BaseModel):
    """Health state of a single data source."""

    source_id: str
    last_success_at: Optional[datetime] = None
    consecutive_failures: int = 0
    last_error: Optional[str] = None
    last_error_type: Optional[str] = None
    data_freshness: Optional[str] = None  # stale / fresh / unknown
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


# ─── Aggregated Output ─────────────────────────────────────────────────────


class RoutedEndpoint(BaseModel):
    """A model endpoint selected for the routing table."""

    endpoint_id: str
    provider_id: str
    provider_name: str
    canonical_model_id: str
    model_name: str
    final_score: float
    quality_band: QualityBand
    free_status: FreeStatus
    rank: int
    is_primary: bool = False


class RouterOutput(BaseModel):
    """Output of the routing engine — the final sorted route."""

    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    reference_scored_at: Optional[str] = None
    endpoints: list[RoutedEndpoint] = Field(default_factory=list)
    fallback_chain: list[str] = Field(default_factory=list)
    scoring_mode: ScoringMode = ScoringMode.COMPOSITE_PRIMARY


# ─── Change Tracking ────────────────────────────────────────────────────────


class ChangeRecord(BaseModel):
    """A single detected change between runs."""

    change_type: str  # new_provider, new_model, free_status_changed, rating_changed, etc.
    entity_id: str
    old_value: Optional[str] = None
    new_value: Optional[str] = None
    description: str
