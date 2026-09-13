"""Report generators — models.md and changes.md."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from free_ai_model_router.models import (
    ChangeRecord,
    ProviderEndpoint,
    RouterOutput,
)
from free_ai_model_router.verification.status import is_routable_status

logger = logging.getLogger(__name__)


def _fmt(val: object, default: str = "—") -> str:
    """Format a value for display, using default if None."""
    if val is None:
        return default
    return str(val)


def _fmt_limits(endpoint: ProviderEndpoint) -> str:
    """Format limits as a string."""
    parts: list[str] = []
    if endpoint.limits.requests_per_day:
        parts.append(f"{endpoint.limits.requests_per_day} req/day")
    if endpoint.limits.requests_per_minute:
        parts.append(f"{endpoint.limits.requests_per_minute} req/min")
    if endpoint.limits.tokens_per_day:
        parts.append(f"{endpoint.limits.tokens_per_day} tok/day")
    if endpoint.limits.tokens_per_minute:
        parts.append(f"{endpoint.limits.tokens_per_minute} tok/min")
    if parts:
        return ", ".join(parts)
    return "—"


def _fmt_latency(endpoint: ProviderEndpoint | None) -> str:
    if not endpoint or endpoint.runtime_check.latency_ms is None:
        return "—"
    return f"{endpoint.runtime_check.latency_ms} ms"


def _fmt_retry_after(endpoint: ProviderEndpoint | None) -> str:
    if not endpoint or endpoint.runtime_check.retry_after_seconds is None:
        return "—"
    return f"{endpoint.runtime_check.retry_after_seconds}s"


def generate_models_report(
    router_output: RouterOutput,
    endpoints: list[ProviderEndpoint],
) -> str:
    """Generate models.md report with verified free models."""
    lines = [
        "# Отчёт по моделям — Free AI Model Router",
        "",
        f"*Сгенерировано: {router_output.generated_at.strftime('%Y-%m-%d %H:%M:%S UTC')}*",
        "",
    ]

    endpoints_map: dict[str, ProviderEndpoint] = {e.endpoint_id: e for e in endpoints}

    lines.append("## Маршрутизируемые бесплатные endpoints")
    lines.append("")

    if router_output.endpoints:
        lines.append("| # | Поставщик | Модель | Доступ | Probe | Latency | Retry | Инструменты | Лимиты |")
        lines.append("|---:|:---|:---|:---|:---|---:|:---|:---|:---|")
        for i, re in enumerate(router_output.endpoints, 1):
            ep = endpoints_map.get(re.endpoint_id)
            tools = "✓" if re.tool_calling else "✗"
            limits = _fmt_limits(ep) if ep else "—"
            probe = (ep.runtime_check.status.value if ep and ep.runtime_check.checked else "not_tested") if ep else "—"
            verdict = (ep.runtime_check.access_verdict.value if ep else re.access_verdict.value)
            lines.append(
                f"| {i} | {re.provider_name} | {re.model_name} | {verdict} | {probe} | "
                f"{_fmt_latency(ep)} | {_fmt_retry_after(ep)} | {tools} | {limits} |"
            )
    else:
        lines.append("_Нет моделей, прошедших проверку._")

    lines.append("")
    lines.append(f"Всего: {len(router_output.endpoints)} моделей")
    lines.append("")

    routed_ids = {r.endpoint_id for r in router_output.endpoints}
    excluded = [
        ep for ep in endpoints
        if ep.endpoint_id not in routed_ids
        and ep.runtime_check.checked
        and not is_routable_status(ep.runtime_check.status)
    ]
    if excluded:
        lines.append("## Не включены в routing output")
        lines.append("")
        lines.append("| Поставщик | Модель | Доступ | Probe | HTTP | Ошибка |")
        lines.append("|:---|:---|:---|:---|---:|:---|")
        for ep in excluded:
            error = _fmt(ep.runtime_check.error_message)
            lines.append(
                f"| {ep.provider_id} | {ep.provider_model_id} | "
                f"{ep.runtime_check.access_verdict.value} | {ep.runtime_check.status.value} | "
                f"{_fmt(ep.runtime_check.http_status)} | {error} |"
            )
        lines.append("")

    return "\n".join(lines)


def generate_changes_report(
    current: RouterOutput,
    previous: Optional[RouterOutput],
    changes: list[ChangeRecord],
) -> str:
    """Generate changes.md report showing diff from previous run."""
    lines = [
        "# Отчёт об изменениях",
        "",
        f"*Сгенерировано: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}*",
        "",
    ]

    if not changes:
        lines.append("_Изменений относительно предыдущего запуска не обнаружено._")
        return "\n".join(lines)

    current_ids = {r.endpoint_id for r in current.endpoints}
    previous_ids = {r.endpoint_id for r in previous.endpoints} if previous else set()

    new = current_ids - previous_ids
    removed = previous_ids - current_ids if previous else set()

    lines.append(f"**Всего изменений:** {len(changes)}")
    lines.append("")

    if new:
        for eid in sorted(new):
            r = next((x for x in current.endpoints if x.endpoint_id == eid), None)
            if r:
                lines.append(f"- {r.endpoint_id}")
        lines.append("")

    if removed:
        for eid in sorted(removed):
            lines.append(f"- {eid}")
        lines.append("")

    # Per-change details
    lines.append("### Детальные изменения")
    lines.append("")
    for c in changes:
        lines.append(f"- **[{c.change_type}]** {c.entity_id}: {c.description}")

    return "\n".join(lines)


def generate_and_write_reports(
    router_output: RouterOutput,
    endpoints: list[ProviderEndpoint],
    changes: list[ChangeRecord],
    previous_output: Optional[RouterOutput],
    reports_dir: Path,
) -> None:
    """Write models.md and changes.md report files."""
    reports_dir.mkdir(parents=True, exist_ok=True)

    models_report = generate_models_report(router_output, endpoints)
    (reports_dir / "models.md").write_text(models_report, encoding="utf-8")

    changes_report = generate_changes_report(router_output, previous_output, changes)
    (reports_dir / "changes.md").write_text(changes_report, encoding="utf-8")

    logger.info("Reports written to %s", reports_dir)
