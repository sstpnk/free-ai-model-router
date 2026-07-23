"""Command-line interface for Free AI Model Router."""

from __future__ import annotations

import asyncio
import logging
import sys
from pathlib import Path
from typing import Optional

import click

from free_ai_model_router.config_loader import Settings
from free_ai_model_router.pipeline.orchestrator import PipelineOrchestrator

logger = logging.getLogger(__name__)


def _setup_logging(level: str = "INFO") -> None:
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def _get_base_dir() -> Path:
    """Determine the repository base directory."""
    # Look for config/ directory as marker
    cwd = Path.cwd()
    if (cwd / "config").exists():
        return cwd
    # Try parent directories
    for parent in cwd.parents:
        if (parent / "config").exists():
            return parent
    # Fallback — assume current dir is repo root
    return cwd


@click.group()
@click.option("--log-level", default="INFO", help="Logging level")
@click.option("--base-dir", default=None, help="Repository base directory")
@click.pass_context
def cli(ctx: click.Context, log_level: str, base_dir: Optional[str]) -> None:
    """Free AI Model Router — daily ETL for free AI coding models."""
    _setup_logging(log_level)
    base_path = Path(base_dir) if base_dir else _get_base_dir()
    settings = Settings.from_base_dir(base_path)
    ctx.ensure_object(dict)
    ctx.obj["settings"] = settings
    ctx.obj["base_dir"] = base_path


@cli.command()
@click.pass_context
def collect(ctx: click.Context) -> None:
    """Collect model data from all configured providers."""
    settings: Settings = ctx.obj["settings"]
    base_dir: Path = ctx.obj["base_dir"]
    orch = PipelineOrchestrator(settings, base_dir)
    asyncio.run(orch.run_all(no_runtime_checks=True))


@cli.command()
@click.option("--provider", default=None, help="Specific provider to verify")
@click.pass_context
def verify(ctx: click.Context, provider: Optional[str]) -> None:
    """Run API verification checks for configured providers."""
    settings: Settings = ctx.obj["settings"]
    base_dir: Path = ctx.obj["base_dir"]
    orch = PipelineOrchestrator(settings, base_dir)
    asyncio.run(orch.run_all(no_runtime_checks=False))


@cli.command()
@click.option("--output-dir", default=None, help="Output directory for generated config")
@click.pass_context
def generate(ctx: click.Context, output_dir: Optional[str]) -> None:
    """Generate LiteLLM config sample from current data."""
    settings: Settings = ctx.obj["settings"]
    base_dir: Path = ctx.obj["base_dir"]
    orch = PipelineOrchestrator(settings, base_dir)
    asyncio.run(orch.run_all(no_runtime_checks=True))


@cli.command()
@click.pass_context
def report(ctx: click.Context) -> None:
    """Generate reports from current data."""
    settings: Settings = ctx.obj["settings"]
    base_dir: Path = ctx.obj["base_dir"]
    orch = PipelineOrchestrator(settings, base_dir)
    asyncio.run(orch.run_all(no_runtime_checks=True))


@cli.command()
@click.option("--offline", is_flag=True, help="Skip all network requests")
@click.option("--no-runtime-checks", is_flag=True, help="Skip API verification checks")
@click.option("--use-cache", is_flag=True, default=True, help="Use cached data when possible")
@click.option("--fail-on-stale", is_flag=True, help="Fail if data sources are stale")
@click.pass_context
def run_all(
    ctx: click.Context,
    offline: bool,
    no_runtime_checks: bool,
    use_cache: bool,
    fail_on_stale: bool,
) -> None:
    """Run the complete pipeline end-to-end."""
    settings: Settings = ctx.obj["settings"]
    base_dir: Path = ctx.obj["base_dir"]

    orch = PipelineOrchestrator(settings, base_dir)
    state = asyncio.run(orch.run_all(
        use_cache=use_cache,
        no_runtime_checks=no_runtime_checks,
        offline=offline,
    ))

    if state.success:
        click.echo("[OK] Pipeline completed successfully")
    elif state.partial_success:
        click.echo("[WARN] Pipeline completed with errors:")
        for err in state.errors:
            click.echo(f"  - {err}")
    else:
        click.echo("[FAIL] Pipeline failed:")
        for err in state.errors:
            click.echo(f"  - {err}")
        sys.exit(1)


if __name__ == "__main__":
    cli()
