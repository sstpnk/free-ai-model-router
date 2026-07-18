"""Local JSON cache with TTL, versioning, and staleness tracking."""

from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional


class DataCache:
    """Cache for normalized pipeline artifacts with versioning."""

    def __init__(self, base_dir: Path) -> None:
        self.base_dir = base_dir
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self._cache: dict[str, dict[str, Any]] = {}

    def _path_for(self, key: str) -> Path:
        sanitized = key.replace("/", "_").replace(":", "_").replace(" ", "_")
        return self.base_dir / f"{sanitized}.json"

    def get(self, key: str) -> Optional[dict[str, Any]]:
        """Get cached value. Returns None if missing."""
        path = self._path_for(key)
        if not path.exists():
            return None
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return None

    def set(self, key: str, data: dict[str, Any]) -> None:
        """Set cached value with timestamp."""
        record = {
            "_cached_at": datetime.now(timezone.utc).isoformat(),
            "_key": key,
            **data,
        }
        path = self._path_for(key)
        path.write_text(json.dumps(record, indent=2, default=str), encoding="utf-8")

    def get_or_fetch(
        self, key: str, ttl_seconds: int, fetcher: callable
    ) -> dict[str, Any]:
        """Get from cache or call fetcher, caching the result."""
        cached = self.get(key)
        if cached:
            cached_at = cached.get("_cached_at", "2000-01-01T00:00:00+00:00")
            age = (datetime.now(timezone.utc) - datetime.fromisoformat(cached_at)).total_seconds()
            if age < ttl_seconds:
                return cached
        data = fetcher()
        self.set(key, {"data": data})
        return {"data": data}

    def clear(self, key: Optional[str] = None) -> None:
        """Clear specific key or entire cache."""
        if key:
            path = self._path_for(key)
            if path.exists():
                path.unlink()
        else:
            shutil.rmtree(self.base_dir)
            self.base_dir.mkdir(parents=True, exist_ok=True)

    def list_keys(self) -> list[str]:
        """List all cached keys."""
        keys = []
        for f in self.base_dir.iterdir():
            if f.suffix == ".json":
                try:
                    data = json.loads(f.read_text(encoding="utf-8"))
                    if "_key" in data:
                        keys.append(data["_key"])
                except (json.JSONDecodeError, OSError):
                    continue
        return keys
