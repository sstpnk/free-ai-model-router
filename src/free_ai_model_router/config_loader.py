"""Configuration loader — reads YAML configs with Pydantic validation."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

import yaml

from free_ai_model_router.models import (
    ManualOverrideList,
    ProviderConfigList,
)


def _load_yaml(path: Path) -> dict[str, Any]:
    """Load and parse a YAML file, returning empty dict for None/empty."""
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")
    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data if isinstance(data, dict) else {}


def load_providers(path: Path) -> ProviderConfigList:
    """Load provider registry from providers.yaml."""
    data = _load_yaml(path)
    return ProviderConfigList(**data)


def load_overrides(path: Path) -> ManualOverrideList:
    """Load manual overrides from manual-overrides.yaml."""
    data = _load_yaml(path) if path.exists() else {}
    overrides = data.get("overrides") or []
    return ManualOverrideList(overrides=overrides)


class Settings:
    """Aggregated runtime settings."""

    def __init__(self, config_dir: Path, data_dir: Path, output_dir: Path, reports_dir: Path) -> None:
        self.config_dir = config_dir
        self.data_dir = data_dir
        self.output_dir = output_dir
        self.reports_dir = reports_dir
        self.raw_dir = data_dir / "raw"
        self.normalized_dir = data_dir / "normalized"
        self.history_dir = data_dir / "history"
        self.cache_dir = data_dir / "cache"

        # Ensure directories exist
        for d in [self.raw_dir, self.normalized_dir, self.history_dir, self.cache_dir, self.output_dir, self.reports_dir]:
            d.mkdir(parents=True, exist_ok=True)

        # Load configs
        self.providers = load_providers(config_dir / "providers.yaml")
        self.overrides = load_overrides(config_dir / "manual-overrides.yaml")

    @classmethod
    def from_base_dir(cls, base_dir: Path) -> "Settings":
        """Create Settings from repository base directory."""
        return cls(
            config_dir=base_dir / "config",
            data_dir=base_dir / "data",
            output_dir=base_dir / "output",
            reports_dir=base_dir / "reports",
        )

    def get_provider_api_key(self, provider_id: str) -> Optional[str]:
        """Get a provider's API key from environment."""
        import os
        env_var = f"{provider_id.upper()}_API_KEY"
        return os.environ.get(env_var)
