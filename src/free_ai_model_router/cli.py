"""Command-line interface for Free AI Model Router."""

from __future__ import annotations

import asyncio
import logging
import sys
from pathlib import Path

import click

from free_ai_model_router.config_loader import Settings
from free_ai_model_router.models import ProviderConfig, VerificationStatus
from free_ai_model_router.pipeline.orchestrator import PipelineOrchestrator
from free_ai_model_router.storage.state import (
    load_json,
    load_latest_provider_access_records,
    load_latest_verification_records,
    load_normalized_data,
)

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


def _print_state_and_exit(state) -> None:
    if state.success:
        click.echo("[OK] Pipeline completed successfully")
        return
    if state.partial_success:
        click.echo("[WARN] Pipeline completed with errors:")
        for err in state.errors:
            click.echo(f"  - {err}")
        return

    click.echo("[FAIL] Pipeline failed:")
    for err in state.errors:
        click.echo(f"  - {err}")
    sys.exit(1)


def _get_provider_or_fail(settings: Settings, provider_id: str) -> ProviderConfig:
    provider = next(
        (item for item in settings.providers.providers if item.provider_id == provider_id),
        None,
    )
    if provider is None:
        known = ", ".join(p.provider_id for p in settings.providers.providers)
        raise click.ClickException(f"Unknown provider '{provider_id}'. Known providers: {known}")
    return provider


def _setup_stdout() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")


def _fmt_dt(value) -> str:
    if value is None:
        return "-"
    return value.strftime("%Y-%m-%d %H:%M:%S")


def _provider_errors_from_state(errors: list[str]) -> dict[str, str]:
    provider_errors: dict[str, str] = {}
    for error in errors:
        if not error.startswith("Provider ") or ": " not in error:
            continue
        provider_id, message = error.removeprefix("Provider ").split(": ", 1)
        provider_errors[provider_id] = message
    return provider_errors


def _provider_doctor_status(
    provider: ProviderConfig,
    *,
    key_present: bool,
    statuses: list[VerificationStatus],
    endpoint_count: int,
    provider_error: str | None = None,
    models_api_status: VerificationStatus | None = None,
) -> str:
    if not provider.enabled:
        return "отключен"
    if provider.api_key_required and not key_present:
        return "ключ не добавлен"
    if not provider.api_key_required:
        return "ключ не требуется"
    if provider_error:
        return "ошибка доступа/ключа"
    if models_api_status == VerificationStatus.AUTHENTICATION_FAILED:
        return "ошибка доступа/ключа"
    if models_api_status == VerificationStatus.RATE_LIMITED:
        return "подключен, но лимит"
    if VerificationStatus.SUCCESS in statuses:
        return "подключен и работает"
    if VerificationStatus.AUTHENTICATION_FAILED in statuses:
        return "ошибка доступа/ключа"
    if VerificationStatus.QUOTA_EXHAUSTED in statuses:
        return "требуется баланс/квота"
    if VerificationStatus.RATE_LIMITED in statuses:
        return "подключен, но лимит"
    if statuses:
        return "проверен, без успеха"
    if endpoint_count == 0:
        return "модели не найдены"
    return "не проверялось"


@click.group()
@click.option("--log-level", default="INFO", help="Logging level")
@click.option("--base-dir", default=None, help="Repository base directory")
@click.pass_context
def cli(ctx: click.Context, log_level: str, base_dir: str | None) -> None:
    """Free AI Model Router — daily ETL for free AI coding models."""
    _setup_stdout()
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
@click.option(
    "--max-probes",
    type=int,
    default=None,
    help="Maximum runtime probes to run; defaults to 2 when --provider is set",
)
@click.pass_context
def verify(ctx: click.Context, provider: str | None, max_probes: int | None) -> None:
    """Run API verification checks for configured providers."""
    settings: Settings = ctx.obj["settings"]
    base_dir: Path = ctx.obj["base_dir"]
    provider_ids = None
    if provider:
        provider_config = _get_provider_or_fail(settings, provider)
        if not provider_config.enabled:
            raise click.ClickException(f"Provider '{provider}' is disabled in config/providers.yaml")
        provider_ids = {provider}
        if max_probes is None:
            max_probes = 2

    orch = PipelineOrchestrator(settings, base_dir)
    state = asyncio.run(orch.run_all(
        no_runtime_checks=False,
        provider_ids=provider_ids,
        max_verification_probes=max_probes,
    ))
    _print_state_and_exit(state)


@cli.command("providers")
@click.pass_context
def providers_status(ctx: click.Context) -> None:
    """Show provider key and latest verification status without network calls."""
    settings: Settings = ctx.obj["settings"]
    _, endpoints = load_normalized_data(settings.normalized_dir)
    latest_records = load_latest_verification_records(settings.history_dir / "verification.jsonl")
    latest_provider_access = load_latest_provider_access_records(settings.history_dir / "provider-access.jsonl")
    pipeline_state = load_json(settings.data_dir / "pipeline-state.json") or {}
    provider_errors = _provider_errors_from_state(pipeline_state.get("errors", []))

    endpoints_by_provider: dict[str, list] = {}
    for endpoint in endpoints:
        endpoints_by_provider.setdefault(endpoint.provider_id, []).append(endpoint)

    records_by_provider: dict[str, list] = {}
    for record in latest_records.values():
        records_by_provider.setdefault(record.provider_id, []).append(record)

    click.echo("Provider status")
    click.echo("provider | status | key | models api | models | last success | last checked")
    click.echo("--- | --- | --- | --- | ---: | --- | ---")
    for provider in sorted(settings.providers.providers, key=lambda item: item.discovery_priority):
        provider_access = latest_provider_access.get(provider.provider_id)
        key_present = bool(settings.get_provider_api_key(provider.provider_id)) or (
            provider_access.api_key_present if provider_access else False
        )
        records = records_by_provider.get(provider.provider_id, [])
        statuses = [record.status for record in records]
        endpoint_count = max(
            len(endpoints_by_provider.get(provider.provider_id, [])),
            provider_access.models_found if provider_access else 0,
        )
        status = _provider_doctor_status(
            provider,
            key_present=key_present,
            statuses=statuses,
            endpoint_count=endpoint_count,
            provider_error=provider_errors.get(provider.provider_id),
            models_api_status=provider_access.models_api_status if provider_access else None,
        )
        key_state = "yes" if key_present else ("not required" if not provider.api_key_required else "missing")
        models_api = provider_access.models_api_status.value if provider_access else "-"
        success_dates = [
            record.checked_at for record in records
            if record.status == VerificationStatus.SUCCESS
        ]
        checked_dates = [record.checked_at for record in records]
        if provider_access:
            checked_dates.append(provider_access.checked_at)
        click.echo(
            f"{provider.provider_id} | {status} | {key_state} | {models_api} | {endpoint_count} | "
            f"{_fmt_dt(max(success_dates, default=None))} | {_fmt_dt(max(checked_dates, default=None))}"
        )


@cli.command()
@click.option("--output-dir", default=None, help="Output directory for generated config")
@click.pass_context
def generate(ctx: click.Context, output_dir: str | None) -> None:
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
    _print_state_and_exit(state)


if __name__ == "__main__":
    cli()
