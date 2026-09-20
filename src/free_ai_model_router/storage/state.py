"""Pipeline state persistence and loading."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from free_ai_model_router.models import (
    AccessVerdict,
    CanonicalModel,
    ChangeRecord,
    PipelineState,
    ProviderAccessRecord,
    ProviderEndpoint,
    RouterOutput,
    VerificationHistoryRecord,
    VerificationStats,
    VerificationStatus,
)
from free_ai_model_router.verification.status import normalize_verification_status


def save_json(data: Any, path: Path) -> None:
    """Save data as pretty-printed JSON."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, default=str, ensure_ascii=False), encoding="utf-8")


def load_json(path: Path) -> Optional[Any]:
    """Load JSON file, return None if missing."""
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def save_pipeline_state(state: PipelineState, path: Path) -> None:
    """Persist pipeline execution state."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(state.model_dump_json(indent=2), encoding="utf-8")


def save_normalized_data(
    models: list[CanonicalModel],
    endpoints: list[ProviderEndpoint],
    output_dir: Path,
) -> None:
    """Save normalized pipeline artifacts."""
    output_dir.mkdir(parents=True, exist_ok=True)
    save_json([m.model_dump() for m in models], output_dir / "models.json")
    save_json([e.model_dump() for e in endpoints], output_dir / "endpoints.json")


def load_normalized_data(
    output_dir: Path,
) -> tuple[list[CanonicalModel], list[ProviderEndpoint]]:
    """Load previously saved normalized data."""
    models_raw = load_json(output_dir / "models.json") or []
    endpoints_raw = load_json(output_dir / "endpoints.json") or []
    return (
        [CanonicalModel(**m) for m in models_raw],
        [ProviderEndpoint(**e) for e in endpoints_raw],
    )


def save_router_output(output: RouterOutput, path: Path) -> None:
    """Persist the routing output."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(output.model_dump_json(indent=2), encoding="utf-8")


def save_changes(changes: list[ChangeRecord], path: Path) -> None:
    """Persist detected changes."""
    path.parent.mkdir(parents=True, exist_ok=True)
    save_json([c.model_dump() for c in changes], path)


def append_verification_history(
    *,
    endpoints: list[ProviderEndpoint],
    run_id: str,
    path: Path,
    checked_after: datetime | None = None,
) -> int:
    """Append checked endpoint verification evidence as JSONL records."""
    path.parent.mkdir(parents=True, exist_ok=True)
    records: list[VerificationHistoryRecord] = []
    for endpoint in endpoints:
        check = endpoint.runtime_check
        if not check.checked or check.checked_at is None:
            continue
        if checked_after and check.checked_at < checked_after:
            continue
        records.append(
            VerificationHistoryRecord(
                run_id=run_id,
                checked_at=check.checked_at,
                endpoint_id=endpoint.endpoint_id,
                provider_id=endpoint.provider_id,
                canonical_model_id=endpoint.canonical_model_id,
                provider_model_id=endpoint.provider_model_id,
                listed_in_models_api=endpoint.listed_in_models_api,
                models_api_checked_at=endpoint.models_api_checked_at,
                models_api_source_url=endpoint.models_api_source_url,
                status=check.status,
                access_verdict=check.access_verdict,
                http_status=check.http_status,
                latency_ms=check.latency_ms,
                retry_after_seconds=check.retry_after_seconds,
                error_message=check.error_message,
            )
        )

    if not records:
        return 0

    with path.open("a", encoding="utf-8", newline="\n") as f:
        for record in records:
            f.write(record.model_dump_json())
            f.write("\n")
    return len(records)


def append_provider_access_history(
    *,
    records: list[ProviderAccessRecord],
    path: Path,
) -> int:
    """Append provider-level access evidence as JSONL records."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if not records:
        return 0

    with path.open("a", encoding="utf-8", newline="\n") as f:
        for record in records:
            f.write(record.model_dump_json())
            f.write("\n")
    return len(records)


def load_latest_provider_access_records(path: Path) -> dict[str, ProviderAccessRecord]:
    """Load latest provider access history record per provider from JSONL."""
    if not path.exists():
        return {}

    latest: dict[str, ProviderAccessRecord] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            record = ProviderAccessRecord(**json.loads(line))
        except (json.JSONDecodeError, ValueError):
            continue
        previous = latest.get(record.provider_id)
        if previous is None or record.checked_at > previous.checked_at:
            latest[record.provider_id] = record
    return latest


def load_latest_verification_records(path: Path) -> dict[str, VerificationHistoryRecord]:
    """Load latest verification history record per endpoint from JSONL."""
    if not path.exists():
        return {}

    latest: dict[str, VerificationHistoryRecord] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            record = VerificationHistoryRecord(**json.loads(line))
        except (json.JSONDecodeError, ValueError):
            continue
        record.status = normalize_verification_status(record.status, record.error_message)
        if record.status == VerificationStatus.CLIENT_RESTRICTED:
            record.access_verdict = AccessVerdict.NOT_ACCESSIBLE
        previous = latest.get(record.endpoint_id)
        if previous is None or record.checked_at > previous.checked_at:
            latest[record.endpoint_id] = record
    return latest


def _percentile(values: list[int], percentile: float) -> int | None:
    """Return nearest-rank percentile for a non-empty integer list."""
    if not values:
        return None
    sorted_values = sorted(values)
    index = round((len(sorted_values) - 1) * percentile)
    return sorted_values[index]


def load_verification_stats(path: Path) -> dict[str, VerificationStats]:
    """Aggregate verification history records by endpoint."""
    if not path.exists():
        return {}

    records_by_endpoint: dict[str, list[VerificationHistoryRecord]] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            record = VerificationHistoryRecord(**json.loads(line))
        except (json.JSONDecodeError, ValueError):
            continue
        record.status = normalize_verification_status(record.status, record.error_message)
        if record.status == VerificationStatus.CLIENT_RESTRICTED:
            record.access_verdict = AccessVerdict.NOT_ACCESSIBLE
        records_by_endpoint.setdefault(record.endpoint_id, []).append(record)

    stats: dict[str, VerificationStats] = {}
    for endpoint_id, records in records_by_endpoint.items():
        attempts = len(records)
        success_records = [record for record in records if record.status == VerificationStatus.SUCCESS]
        rate_limited = [record for record in records if record.status == VerificationStatus.RATE_LIMITED]
        quota_exhausted = [record for record in records if record.status == VerificationStatus.QUOTA_EXHAUSTED]
        hard_failures = [
            record for record in records
            if record.status not in {
                VerificationStatus.SUCCESS,
                VerificationStatus.RATE_LIMITED,
                VerificationStatus.QUOTA_EXHAUSTED,
                VerificationStatus.CLIENT_RESTRICTED,
                VerificationStatus.NOT_TESTED,
            }
        ]
        latencies = [record.latency_ms for record in records if record.latency_ms is not None]
        stats[endpoint_id] = VerificationStats(
            endpoint_id=endpoint_id,
            attempts=attempts,
            success_count=len(success_records),
            rate_limited_count=len(rate_limited),
            quota_exhausted_count=len(quota_exhausted),
            hard_failure_count=len(hard_failures),
            success_rate=round(len(success_records) / attempts, 4) if attempts else 0.0,
            last_checked_at=max((record.checked_at for record in records), default=None),
            last_success_at=max((record.checked_at for record in success_records), default=None),
            p50_latency_ms=_percentile(latencies, 0.50),
            p95_latency_ms=_percentile(latencies, 0.95),
        )
    return stats


def load_previous_output(path: Path) -> Optional[RouterOutput]:
    """Load the last run's routing output for diffing."""
    raw = load_json(path)
    if raw is None:
        return None
    return RouterOutput(**raw)
