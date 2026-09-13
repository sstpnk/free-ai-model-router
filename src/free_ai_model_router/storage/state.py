"""Pipeline state persistence and loading."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

from free_ai_model_router.models import (
    CanonicalModel,
    ChangeRecord,
    PipelineState,
    ProviderEndpoint,
    RouterOutput,
    VerificationHistoryRecord,
)


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
) -> int:
    """Append checked endpoint verification evidence as JSONL records."""
    path.parent.mkdir(parents=True, exist_ok=True)
    records: list[VerificationHistoryRecord] = []
    for endpoint in endpoints:
        check = endpoint.runtime_check
        if not check.checked or check.checked_at is None:
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


def load_previous_output(path: Path) -> Optional[RouterOutput]:
    """Load the last run's routing output for diffing."""
    raw = load_json(path)
    if raw is None:
        return None
    return RouterOutput(**raw)
