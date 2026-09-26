"""Report generators — models.md and changes.md."""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from pathlib import Path

from free_ai_model_router.models import (
    ChangeRecord,
    FreeStatus,
    ProviderAccessRecord,
    ProviderConfig,
    ProviderEndpoint,
    RouterOutput,
    VerificationHistoryRecord,
    VerificationStats,
    VerificationStatus,
)
from free_ai_model_router.verification.status import is_routable_status

logger = logging.getLogger(__name__)


def _fmt(val: object, default: str = "—") -> str:
    """Format a value for display, using default if None."""
    if val is None:
        return default
    return str(val)


_KNOWN_FREE_STATUSES = {
    FreeStatus.VERIFIED_FREE,
    FreeStatus.DOCUMENTED_FREE,
    FreeStatus.ACCOUNT_SPECIFIC_FREE,
    FreeStatus.TEMPORARY_FREE,
    FreeStatus.TRIAL_CREDIT,
}


def _fmt_report_error(value: str | None, *, max_length: int = 120) -> str:
    if not value:
        return "—"
    collapsed = " ".join(value.split())
    if len(collapsed) <= max_length:
        return collapsed
    return f"{collapsed[: max_length - 1]}…"


def _free_status_for_report(endpoint: ProviderEndpoint | None, provider_model_id: str) -> str:
    if endpoint:
        if endpoint.free_status != FreeStatus.UNKNOWN:
            return endpoint.free_status.value
        model_id = endpoint.provider_model_id
    else:
        model_id = provider_model_id

    normalized_model_id = model_id.lower()
    if ":free" in normalized_model_id or normalized_model_id.endswith("-free"):
        return "inferred_free_name"
    return FreeStatus.UNKNOWN.value


def _is_free_for_report(endpoint: ProviderEndpoint | None, provider_model_id: str) -> bool:
    if endpoint and endpoint.free_status in _KNOWN_FREE_STATUSES:
        return True
    return _free_status_for_report(endpoint, provider_model_id) == "inferred_free_name"


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


def _fmt_models_api(endpoint: ProviderEndpoint | None) -> str:
    if not endpoint:
        return "—"
    if not endpoint.listed_in_models_api:
        return "no"
    if endpoint.models_api_checked_at:
        return "yes"
    return "assumed"


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
        lines.append("| # | Поставщик | Модель | Listed | Доступ | Probe | Latency | Retry | Инструменты | Лимиты |")
        lines.append("|---:|:---|:---|:---|:---|:---|---:|:---|:---|:---|")
        for i, re in enumerate(router_output.endpoints, 1):
            ep = endpoints_map.get(re.endpoint_id)
            tools = "✓" if re.tool_calling else "✗"
            limits = _fmt_limits(ep) if ep else "—"
            probe = (ep.runtime_check.status.value if ep and ep.runtime_check.checked else "not_tested") if ep else "—"
            verdict = (ep.runtime_check.access_verdict.value if ep else re.access_verdict.value)
            lines.append(
                f"| {i} | {re.provider_name} | {re.model_name} | {_fmt_models_api(ep)} | {verdict} | {probe} | "
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
        lines.append("| Поставщик | Модель | Listed | Доступ | Probe | HTTP | Ошибка |")
        lines.append("|:---|:---|:---|:---|:---|---:|:---|")
        for ep in excluded:
            error = _fmt(ep.runtime_check.error_message)
            lines.append(
                f"| {ep.provider_id} | {ep.provider_model_id} | {_fmt_models_api(ep)} | "
                f"{ep.runtime_check.access_verdict.value} | {ep.runtime_check.status.value} | "
                f"{_fmt(ep.runtime_check.http_status)} | {error} |"
            )
        lines.append("")

    return "\n".join(lines)


def generate_changes_report(
    current: RouterOutput,
    previous: RouterOutput | None,
    changes: list[ChangeRecord],
) -> str:
    """Generate changes.md report showing diff from previous run."""
    lines = [
        "# Отчёт об изменениях",
        "",
        f"*Сгенерировано: {datetime.now(UTC).strftime('%Y-%m-%d %H:%M:%S UTC')}*",
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


def generate_provider_health_report(endpoints: list[ProviderEndpoint]) -> str:
    """Generate provider-level verification status summary."""
    lines = [
        "# Provider Health",
        "",
        f"*Generated: {datetime.now(UTC).strftime('%Y-%m-%d %H:%M:%S UTC')}*",
        "",
    ]

    by_provider: dict[str, list[ProviderEndpoint]] = {}
    for endpoint in endpoints:
        by_provider.setdefault(endpoint.provider_id, []).append(endpoint)

    if not by_provider:
        lines.append("_No provider data._")
        return "\n".join(lines)

    lines.append("| Provider | Total | Checked | Usable | Throttled | Quota | Not tested | Hard fail | Avg latency |")
    lines.append("|:---|---:|---:|---:|---:|---:|---:|---:|---:|")
    for provider_id in sorted(by_provider):
        provider_endpoints = by_provider[provider_id]
        checked = [ep for ep in provider_endpoints if ep.runtime_check.checked]
        usable = [ep for ep in checked if ep.runtime_check.status == VerificationStatus.SUCCESS]
        throttled = [ep for ep in checked if ep.runtime_check.status == VerificationStatus.RATE_LIMITED]
        quota = [ep for ep in checked if ep.runtime_check.status == VerificationStatus.QUOTA_EXHAUSTED]
        not_tested = [
            ep for ep in provider_endpoints
            if not ep.runtime_check.checked or ep.runtime_check.status == VerificationStatus.NOT_TESTED
        ]
        hard_fail = [
            ep for ep in checked
            if ep.runtime_check.status not in {
                VerificationStatus.SUCCESS,
                VerificationStatus.RATE_LIMITED,
                VerificationStatus.QUOTA_EXHAUSTED,
                VerificationStatus.CLIENT_RESTRICTED,
                VerificationStatus.NOT_TESTED,
            }
        ]
        latencies = [ep.runtime_check.latency_ms for ep in checked if ep.runtime_check.latency_ms is not None]
        avg_latency = f"{round(sum(latencies) / len(latencies))} ms" if latencies else "—"
        lines.append(
            f"| {provider_id} | {len(provider_endpoints)} | {len(checked)} | {len(usable)} | "
            f"{len(throttled)} | {len(quota)} | {len(not_tested)} | {len(hard_fail)} | {avg_latency} |"
        )

    return "\n".join(lines)


def generate_throttled_report(endpoints: list[ProviderEndpoint]) -> str:
    """Generate report for endpoints blocked by rate limits or quota."""
    lines = [
        "# Throttled Endpoints",
        "",
        f"*Generated: {datetime.now(UTC).strftime('%Y-%m-%d %H:%M:%S UTC')}*",
        "",
    ]
    throttled_statuses = {
        VerificationStatus.RATE_LIMITED,
        VerificationStatus.QUOTA_EXHAUSTED,
    }
    throttled = [
        ep for ep in endpoints
        if ep.runtime_check.checked and ep.runtime_check.status in throttled_statuses
    ]

    if not throttled:
        lines.append("_No throttled endpoints._")
        return "\n".join(lines)

    lines.append("| Provider | Model | Verdict | Probe | HTTP | Retry | Last checked |")
    lines.append("|:---|:---|:---|:---|---:|:---|:---|")
    for ep in sorted(throttled, key=lambda item: (item.provider_id, item.provider_model_id)):
        checked_at = (
            ep.runtime_check.checked_at.strftime("%Y-%m-%d %H:%M:%S UTC")
            if ep.runtime_check.checked_at
            else "—"
        )
        lines.append(
            f"| {ep.provider_id} | {ep.provider_model_id} | {ep.runtime_check.access_verdict.value} | "
            f"{ep.runtime_check.status.value} | {_fmt(ep.runtime_check.http_status)} | "
            f"{_fmt_retry_after(ep)} | {checked_at} |"
        )

    return "\n".join(lines)


def _provider_access_status(
    *,
    provider: ProviderConfig,
    endpoints: list[ProviderEndpoint],
    api_key_present: bool,
    provider_error: str | None = None,
    provider_access_record: ProviderAccessRecord | None = None,
    runtime_statuses: list[VerificationStatus] | None = None,
) -> tuple[str, str]:
    """Classify provider connection/key status for humans."""
    if not provider.enabled:
        return "отключен", "Провайдер отключен в config/providers.yaml."
    if not provider.api_key_required:
        return "ключ не требуется", "В конфиге указано, что API ключ не требуется."
    if not api_key_present:
        return "ключ не добавлен", "API ключ пока не настроен в окружении."
    if provider_error:
        return "ошибка доступа/ключа", provider_error
    if provider_access_record and provider_access_record.models_api_status == VerificationStatus.AUTHENTICATION_FAILED:
        return "ошибка доступа/ключа", provider_access_record.error_message or "/models вернул ошибку доступа."
    if provider_access_record and provider_access_record.models_api_status == VerificationStatus.RATE_LIMITED:
        return "подключен, но лимит", provider_access_record.error_message or "/models уперся в rate limit."

    checked = [ep for ep in endpoints if ep.runtime_check.checked]
    statuses = runtime_statuses or [ep.runtime_check.status for ep in checked]
    if VerificationStatus.SUCCESS in statuses:
        return "подключен и работает", "Хотя бы один endpoint успешно ответил на generation probe."
    if VerificationStatus.CLIENT_RESTRICTED in statuses and VerificationStatus.QUOTA_EXHAUSTED in statuses:
        return (
            "часть моделей только из клиента, часть требует баланс",
            "Free-tier модели достижимы, но runtime разрешен только из официального клиента провайдера; "
            "остальные требуют баланс или пакет.",
        )
    if VerificationStatus.CLIENT_RESTRICTED in statuses:
        return (
            "только через клиент провайдера",
            "Runtime probe дошел до модели, но провайдер ограничивает free-tier официальным клиентом.",
        )
    if VerificationStatus.QUOTA_EXHAUSTED in statuses:
        return (
            "требуется баланс/квота",
            "Провайдер достижим, но генерация требует баланс, квоту или ресурсный пакет.",
        )
    if VerificationStatus.RATE_LIMITED in statuses:
        return "подключен, но лимит", "Провайдер достижим, но генерация уперлась в rate limit."
    if VerificationStatus.AUTHENTICATION_FAILED in statuses:
        return "ошибка доступа/ключа", "Runtime probe получил ошибку аутентификации."
    if statuses:
        return "проверен, без успеха", "Runtime probes выполнялись, но не дали usable/throttled evidence."
    if endpoints:
        return "не проверялось", "Модели найдены, но runtime probes не запускались."
    if provider_access_record and provider_access_record.models_api_status == VerificationStatus.SUCCESS:
        return "не проверялось", f"/models доступен, найдено моделей: {provider_access_record.models_found}."
    if provider_access_record and provider_access_record.models_api_checked:
        return "проверен, без успеха", provider_access_record.error_message or "/models не вернул usable evidence."
    return "модели не найдены", "Для провайдера не найдено моделей."


def generate_provider_access_report(
    *,
    providers: list[ProviderConfig],
    endpoints: list[ProviderEndpoint],
    api_key_presence: dict[str, bool],
    provider_errors: dict[str, str] | None = None,
    provider_access_records: dict[str, ProviderAccessRecord] | None = None,
    provider_runtime_statuses: dict[str, list[VerificationStatus]] | None = None,
) -> str:
    """Generate provider/key readiness report for all configured providers."""
    provider_errors = provider_errors or {}
    provider_access_records = provider_access_records or {}
    provider_runtime_statuses = provider_runtime_statuses or {}
    lines = [
        "# Provider Access",
        "",
        f"*Generated: {datetime.now(UTC).strftime('%Y-%m-%d %H:%M:%S UTC')}*",
        "",
        "| Provider | Name | Status | Key | Models API | Checked | Success | Auth errors | Limited | "
        "Client restricted | Env var | Notes |",
        "|:---|:---|:---|:---|:---|---:|---:|---:|---:|---:|:---|:---|",
    ]

    endpoints_by_provider: dict[str, list[ProviderEndpoint]] = {}
    for endpoint in endpoints:
        endpoints_by_provider.setdefault(endpoint.provider_id, []).append(endpoint)

    for provider in sorted(providers, key=lambda item: item.discovery_priority):
        provider_endpoints = endpoints_by_provider.get(provider.provider_id, [])
        checked = [ep for ep in provider_endpoints if ep.runtime_check.checked]
        historical_statuses = provider_runtime_statuses.get(provider.provider_id, [])
        statuses = [ep.runtime_check.status for ep in checked] or historical_statuses
        success_count = statuses.count(VerificationStatus.SUCCESS)
        auth_error_count = statuses.count(VerificationStatus.AUTHENTICATION_FAILED)
        limited_count = sum(
            1 for status in statuses
            if status in {VerificationStatus.RATE_LIMITED, VerificationStatus.QUOTA_EXHAUSTED}
        )
        client_restricted_count = statuses.count(VerificationStatus.CLIENT_RESTRICTED)
        provider_access_record = provider_access_records.get(provider.provider_id)
        key_present = api_key_presence.get(provider.provider_id, False) or (
            provider_access_record.api_key_present if provider_access_record else False
        )
        status, notes = _provider_access_status(
            provider=provider,
            endpoints=provider_endpoints,
            api_key_present=key_present,
            provider_error=provider_errors.get(provider.provider_id),
            provider_access_record=provider_access_record,
            runtime_statuses=statuses,
        )
        models_api = (
            f"{provider_access_record.models_api_status.value} ({provider_access_record.models_found})"
            if provider_access_record
            else "—"
        )
        if not provider.enabled:
            key_state = "отключен"
        elif not provider.api_key_required:
            key_state = "не требуется"
        elif key_present:
            key_state = "добавлен"
        else:
            key_state = "не добавлен"
        env_var = f"{provider.provider_id.upper()}_API_KEY"
        lines.append(
            f"| {provider.provider_id} | {provider.name} | {status} | {key_state} | "
            f"{models_api} | {len(statuses)} | {success_count} | {auth_error_count} | {limited_count} | "
            f"{client_restricted_count} | {env_var} | {notes} |"
        )

    return "\n".join(lines)


def _fmt_datetime(value: datetime | None) -> str:
    if value is None:
        return "—"
    return value.strftime("%Y-%m-%d %H:%M:%S UTC")


def generate_history_summary_report(
    *,
    endpoints: list[ProviderEndpoint],
    verification_stats: dict[str, VerificationStats],
) -> str:
    """Generate endpoint reliability summary from verification history."""
    lines = [
        "# Verification History Summary",
        "",
        f"*Generated: {datetime.now(UTC).strftime('%Y-%m-%d %H:%M:%S UTC')}*",
        "",
    ]
    if not verification_stats:
        lines.append("_No verification history yet._")
        return "\n".join(lines)

    endpoint_lookup = {endpoint.endpoint_id: endpoint for endpoint in endpoints}
    lines.append(
        "| Provider | Model | Attempts | Success rate | Last success | Last checked | "
        "Rate limits | Quota | Client restricted | Hard failures | p50 | p95 |"
    )
    lines.append("|:---|:---|---:|---:|:---|:---|---:|---:|---:|---:|---:|---:|")
    for endpoint_id in sorted(verification_stats):
        stats = verification_stats[endpoint_id]
        endpoint = endpoint_lookup.get(endpoint_id)
        provider_id = endpoint.provider_id if endpoint else endpoint_id.split("/", 1)[0]
        model = endpoint.provider_model_id if endpoint else endpoint_id
        lines.append(
            f"| {provider_id} | {model} | {stats.attempts} | {stats.success_rate:.0%} | "
            f"{_fmt_datetime(stats.last_success_at)} | {_fmt_datetime(stats.last_checked_at)} | "
            f"{stats.rate_limited_count} | {stats.quota_exhausted_count} | "
            f"{stats.client_restricted_count} | {stats.hard_failure_count} | "
            f"{_fmt(stats.p50_latency_ms)} | {_fmt(stats.p95_latency_ms)} |"
        )

    return "\n".join(lines)


def generate_model_verdicts_report(
    *,
    endpoints: list[ProviderEndpoint],
    latest_records: dict[str, VerificationHistoryRecord],
    provider_id: str | None = None,
    status: VerificationStatus | None = None,
    free_only: bool = False,
) -> str:
    """Generate latest model-level verification verdicts from local history."""
    lines = [
        "# Model Verification Verdicts",
        "",
        f"*Generated: {datetime.now(UTC).strftime('%Y-%m-%d %H:%M:%S UTC')}*",
        "",
    ]

    endpoint_lookup = {endpoint.endpoint_id: endpoint for endpoint in endpoints}
    records = sorted(
        latest_records.values(),
        key=lambda record: (record.provider_id, record.provider_model_id),
    )

    rows: list[tuple[VerificationHistoryRecord, ProviderEndpoint | None]] = []
    for record in records:
        endpoint = endpoint_lookup.get(record.endpoint_id)
        if provider_id and record.provider_id != provider_id:
            continue
        if status and record.status != status:
            continue
        if free_only and not _is_free_for_report(endpoint, record.provider_model_id):
            continue
        rows.append((record, endpoint))

    if provider_id:
        lines.append(f"Provider filter: `{provider_id}`")
    if status:
        lines.append(f"Status filter: `{status.value}`")
    if free_only:
        lines.append("Free filter: known free/trial/account-specific endpoints only")
    if len(lines) > 4:
        lines.append("")

    if not rows:
        lines.append("_No matching verification records in local history._")
        return "\n".join(lines)

    lines.append("| Provider | Model | Free status | Verdict | Probe | HTTP | Last checked | Error |")
    lines.append("|:---|:---|:---|:---|:---|---:|:---|:---|")
    for record, endpoint in rows:
        free_status = _free_status_for_report(endpoint, record.provider_model_id)
        http_status = _fmt(record.http_status)
        checked_at = record.checked_at.strftime("%Y-%m-%d %H:%M:%S UTC")
        lines.append(
            f"| {record.provider_id} | {record.provider_model_id} | {free_status} | "
            f"{record.access_verdict.value} | {record.status.value} | {http_status} | "
            f"{checked_at} | {_fmt_report_error(record.error_message)} |"
        )

    return "\n".join(lines)


def generate_and_write_reports(
    router_output: RouterOutput,
    endpoints: list[ProviderEndpoint],
    changes: list[ChangeRecord],
    previous_output: RouterOutput | None,
    reports_dir: Path,
    providers: list[ProviderConfig] | None = None,
    api_key_presence: dict[str, bool] | None = None,
    verification_stats: dict[str, VerificationStats] | None = None,
    provider_errors: dict[str, str] | None = None,
    provider_access_records: dict[str, ProviderAccessRecord] | None = None,
    provider_runtime_statuses: dict[str, list[VerificationStatus]] | None = None,
    write_routing_reports: bool = True,
) -> None:
    """Write markdown report files."""
    reports_dir.mkdir(parents=True, exist_ok=True)

    if write_routing_reports:
        models_report = generate_models_report(router_output, endpoints)
        (reports_dir / "models.md").write_text(models_report, encoding="utf-8")

        changes_report = generate_changes_report(router_output, previous_output, changes)
        (reports_dir / "changes.md").write_text(changes_report, encoding="utf-8")

    provider_health_report = generate_provider_health_report(endpoints)
    (reports_dir / "provider-health.md").write_text(provider_health_report, encoding="utf-8")

    throttled_report = generate_throttled_report(endpoints)
    (reports_dir / "throttled.md").write_text(throttled_report, encoding="utf-8")

    if providers is not None:
        provider_access_report = generate_provider_access_report(
            providers=providers,
            endpoints=endpoints,
            api_key_presence=api_key_presence or {},
            provider_errors=provider_errors,
            provider_access_records=provider_access_records,
            provider_runtime_statuses=provider_runtime_statuses,
        )
        (reports_dir / "provider-access.md").write_text(provider_access_report, encoding="utf-8")

    if verification_stats is not None:
        history_summary = generate_history_summary_report(
            endpoints=endpoints,
            verification_stats=verification_stats,
        )
        (reports_dir / "history-summary.md").write_text(history_summary, encoding="utf-8")

    logger.info("Reports written to %s", reports_dir)
