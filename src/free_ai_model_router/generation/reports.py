"""Report generators — models.md, changes.md, sources-health.md, discovered-candidates.md."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from free_ai_model_router.models import (
    ChangeRecord,
    ModelRating,
    ProviderEndpoint,
    RouterOutput,
    SourceHealth,
)

logger = logging.getLogger(__name__)


def _fmt(val: object, default: str = "нет данных") -> str:
    """Format a value for display, using default if None."""
    if val is None:
        return default
    return str(val)


def _fmt_limits(endpoint: ProviderEndpoint) -> str:
    """Format limits as two-line string."""
    lines: list[str] = []
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
        lines.append(", ".join(parts))
    else:
        lines.append("нет данных")

    if endpoint.context_tokens:
        # Format context size nicely
        ctx = endpoint.context_tokens
        if ctx >= 1_000_000:
            lines.append(f"context {ctx // 1000}k")
        elif ctx >= 1_000:
            lines.append(f"context {ctx // 1000}k")
        else:
            lines.append(f"context {ctx}")

    return "\n".join(lines)


def generate_models_report(
    router_output: RouterOutput,
    ratings: list[ModelRating],
    endpoints: list[ProviderEndpoint],
    source_attribution: Optional[str] = None,
) -> str:
    """Generate models.md report."""
    lines = [
        "# Отчёт по моделям — Free AI Model Router",
        "",
        f"*Сгенерировано: {router_output.generated_at.strftime('%Y-%m-%d %H:%M:%S UTC')}*",
        "",
    ]

    if source_attribution:
        lines.append(f"*Источник рейтингов: {source_attribution}*")
        lines.append("")

    # Build a lookup
    ratings_map: dict[str, ModelRating] = {r.canonical_model_id: r for r in ratings}
    endpoints_map: dict[str, ProviderEndpoint] = {e.endpoint_id: e for e in endpoints}

    routed_ids = {r.endpoint_id for r in router_output.endpoints}

    lines.append("## Маршрут (включены в litellm-config-sample.yaml)")
    lines.append("")

    if router_output.endpoints:
        lines.append("| Место | Поставщик | Модель | Качество | Уверенность | Бесплатность | Лимиты | Статус API |")
        lines.append("|---|---:|---:|---:|:---:|:---:|---:|:---:|")
        for re in router_output.endpoints:
            ep = endpoints_map.get(re.endpoint_id)
            quality = f"{re.final_score:.1f}%" if re.final_score else re.quality_band.value
            confidence = ""
            free_status = re.free_status.value
            limits = _fmt_limits(ep) if ep else "—"
            api_status = (ep.runtime_check.status.value if ep and ep.runtime_check.checked else "not_tested") if ep else "—"
            lines.append(f"| {re.rank} | {re.provider_name} | {re.model_name} | {quality} | {confidence} | {free_status} | {limits} | {api_status} |")
    else:
        lines.append("_Маршрут пуст — ни одна модель не прошла порог._")

    lines.append("")

    # Ranked models table
    lines.append("## Все ранжированные модели")
    lines.append("")
    lines.append("| № | Модель | Качество (%) | Уверенность | Бесплатность | Штрафы | В маршруте |")
    lines.append("|---:|---|---:|:---:|:---:|:---:|:---:|")

    # Sort by quality
    sorted_ratings = sorted(
        ratings,
        key=lambda r: r.normalized_scores.final_router_score or r.normalized_scores.coding_quality_percent or 0,
        reverse=True,
    )

    for i, rating in enumerate(sorted_ratings, 1):
        quality = rating.normalized_scores.final_router_score or rating.normalized_scores.coding_quality_percent
        quality_str = f"{quality:.1f}" if quality is not None else "—"
        penalties = ", ".join(rating.normalized_scores.penalties_applied) or "—"
        in_route = "✓" if rating.canonical_model_id in {
            e.canonical_model_id for e in router_output.endpoints
        } else "—"
        lines.append(
            f"| {i} | {rating.canonical_model_id}"
            f" | {quality_str}"
            f" | {rating.ranking_confidence.value}"
            f" | —"
            f" | {penalties}"
            f" | {in_route} |"
        )

    lines.append("")
    lines.append("### Легенда")
    lines.append("")
    lines.append("- **Качество (%)**: итоговая оценка относительно ChatGPT-5.6 Sol High = 100%")
    lines.append("- **Уверенность**: high (есть прямой Coding Agent Index), medium (косвенные данные), low (нет данных)")
    lines.append("- **Штрафы**: применённые штрафы с указанием величины")
    lines.append("- **В маршруте**: модель включена в сгенерированный LiteLLM config")
    lines.append("")
    lines.append("---")
    lines.append("*AI-тестирование проведено через Artificial Analysis Coding Agent Index и дополнительные источники.*")

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
        lines.append(f"### Новые модели в маршруте ({len(new)})")
        for eid in sorted(new):
            r = next((r for r in current.endpoints if r.endpoint_id == eid), None)
            if r:
                lines.append(f"- {r.model_name} ({r.provider_name}) — рейтинг {r.final_score:.1f}%")
        lines.append("")

    if removed:
        lines.append(f"### Модели, покинувшие маршрут ({len(removed)})")
        for eid in sorted(removed):
            lines.append(f"- {eid}")
        lines.append("")

    # Per-change details
    lines.append("### Детальные изменения")
    lines.append("")
    for c in changes:
        lines.append(f"- **[{c.change_type}]** {c.entity_id}: {c.description}")

    return "\n".join(lines)


def generate_sources_health_report(
    source_health: dict[str, SourceHealth],
) -> str:
    """Generate sources-health.md report."""
    lines = [
        "# Состояние источников данных",
        "",
        f"*Сгенерировано: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}*",
        "",
        "| Источник | Последний успех | Сбои | Ошибка | Статус |",
        "|---|---:|---:|:---:|:---:|",
    ]

    for sid, health in sorted(source_health.items()):
        last = health.last_success_at.strftime("%Y-%m-%d %H:%M") if health.last_success_at else "никогда"
        fails = str(health.consecutive_failures)
        error = health.last_error or "—"
        status = "✓" if health.consecutive_failures == 0 else "✗" if health.consecutive_failures >= 3 else "⚠"
        lines.append(f"| {sid} | {last} | {fails} | {error} | {status} |")

    return "\n".join(lines)


def generate_discovered_candidates_report(candidates: list[dict]) -> str:
    """Generate discovered-candidates.md report."""
    lines = [
        "# Обнаруженные кандидаты",
        "",
        f"*Сгенерировано: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}*",
        "",
    ]

    if not candidates:
        lines.append("_Новых кандидатов не обнаружено._")
        return "\n".join(lines)

    lines.append("| Кандидат | Источник | Популярность | Статус |")
    lines.append("|---:|:---:|---:|:---:|")

    for c in candidates:
        name = c.get("id", c.get("modelId", c.get("name", "?")))
        source = c.get("source", "hf")
        likes = c.get("likes", c.get("downloads", "?"))
        lines.append(f"| {name} | {source} | {likes} | discovered |")

    return "\n".join(lines)


def write_reports(
    router_output: RouterOutput,
    ratings: list[ModelRating],
    endpoints: list[ProviderEndpoint],
    source_health: dict[str, SourceHealth],
    changes: list[ChangeRecord],
    previous_output: Optional[RouterOutput],
    discovered_candidates: list[dict],
    reports_dir: Path,
    source_attribution: Optional[str] = None,
) -> None:
    """Write all report files."""
    reports_dir.mkdir(parents=True, exist_ok=True)

    models_report = generate_models_report(router_output, ratings, endpoints, source_attribution)
    (reports_dir / "models.md").write_text(models_report, encoding="utf-8")

    changes_report = generate_changes_report(router_output, previous_output, changes)
    (reports_dir / "changes.md").write_text(changes_report, encoding="utf-8")

    health_report = generate_sources_health_report(source_health)
    (reports_dir / "sources-health.md").write_text(health_report, encoding="utf-8")

    candidates_report = generate_discovered_candidates_report(discovered_candidates)
    (reports_dir / "discovered-candidates.md").write_text(candidates_report, encoding="utf-8")

    logger.info("Reports written to %s", reports_dir)
