"""Pipeline state persistence and loading."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from free_ai_model_router.models import (
    CanonicalModel,
    ChangeRecord,
    ModelRating,
    PipelineState,
    ProviderEndpoint,
    RouterOutput,
    SourceHealth,
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
    ratings: list[ModelRating],
    output_dir: Path,
) -> None:
    """Save normalized pipeline artifacts."""
    output_dir.mkdir(parents=True, exist_ok=True)
    save_json([m.model_dump() for m in models], output_dir / "models.json")
    save_json([e.model_dump() for e in endpoints], output_dir / "endpoints.json")
    save_json([r.model_dump() for r in ratings], output_dir / "benchmarks.json")


def load_normalized_data(
    output_dir: Path,
) -> tuple[list[CanonicalModel], list[ProviderEndpoint], list[ModelRating]]:
    """Load previously saved normalized data."""
    models_raw = load_json(output_dir / "models.json") or []
    endpoints_raw = load_json(output_dir / "endpoints.json") or []
    ratings_raw = load_json(output_dir / "benchmarks.json") or []
    return (
        [CanonicalModel(**m) for m in models_raw],
        [ProviderEndpoint(**e) for e in endpoints_raw],
        [ModelRating(**r) for r in ratings_raw],
    )


def save_router_output(output: RouterOutput, path: Path) -> None:
    """Persist the routing output."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(output.model_dump_json(indent=2), encoding="utf-8")


def save_changes(changes: list[ChangeRecord], path: Path) -> None:
    """Persist detected changes."""
    path.parent.mkdir(parents=True, exist_ok=True)
    save_json([c.model_dump() for c in changes], path)


def load_previous_output(path: Path) -> Optional[RouterOutput]:
    """Load the last run's routing output for diffing."""
    raw = load_json(path)
    if raw is None:
        return None
    return RouterOutput(**raw)
