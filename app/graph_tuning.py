from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from .learning_engine import SkillStats, build_skill_stats
from .models import QuizAttempt


@dataclass(frozen=True)
class GraphTuningSuggestion:
    target_skill: str
    prerequisite_skill: str
    action: str
    suggested_delta: float
    evidence: str


@dataclass(frozen=True)
class MonthlyGraphTuningReport:
    window_days: int
    generated_at: str
    attempt_count: int
    suggestions: tuple[GraphTuningSuggestion, ...]


def build_monthly_graph_tuning_report(
    *,
    attempts: list[QuizAttempt],
    skill_order: tuple[str, ...],
    prerequisites: dict[str, tuple[object, ...]],
    now_iso_text: str,
    window_days: int = 31,
    min_target_attempts: int = 2,
) -> MonthlyGraphTuningReport:
    window_days = max(1, int(window_days))
    cutoff = _parse_iso(now_iso_text) - timedelta(days=window_days)
    recent_attempts = [attempt for attempt in attempts if _parse_iso(attempt.created_at) >= cutoff]
    stats = build_skill_stats(recent_attempts, skill_order)
    suggestions: list[GraphTuningSuggestion] = []

    for target in skill_order:
        target_stats = stats.get(target)
        if target_stats is None or target_stats.attempts < min_target_attempts:
            continue
        for prereq, current_weight in _prereq_edges(target, prerequisites):
            prereq_stats = stats.get(prereq)
            suggestion = _suggestion_for_edge(target, prereq, current_weight, target_stats, prereq_stats)
            if suggestion is not None:
                suggestions.append(suggestion)

    suggestions.sort(key=lambda item: (item.target_skill, item.prerequisite_skill, item.action))
    return MonthlyGraphTuningReport(
        window_days=window_days,
        generated_at=now_iso_text,
        attempt_count=len(recent_attempts),
        suggestions=tuple(suggestions),
    )


def render_monthly_graph_tuning_markdown(report: MonthlyGraphTuningReport) -> str:
    lines = [
        "# Monthly Graph Tuning Review",
        "",
        f"Generated: {report.generated_at}",
        f"Window: {report.window_days} days",
        f"Recent attempts reviewed: {report.attempt_count}",
        "",
    ]
    if not report.suggestions:
        lines.append("No graph tuning suggestions from the current evidence window.")
        return "\n".join(lines)
    lines.append("| Target | Prerequisite | Action | Delta | Evidence |")
    lines.append("|---|---|---:|---:|---|")
    for item in report.suggestions:
        lines.append(
            f"| {item.target_skill} | {item.prerequisite_skill} | {item.action} | "
            f"{item.suggested_delta:+.2f} | {item.evidence} |"
        )
    return "\n".join(lines)


def _suggestion_for_edge(
    target: str,
    prereq: str,
    current_weight: float,
    target_stats: SkillStats,
    prereq_stats: SkillStats | None,
) -> GraphTuningSuggestion | None:
    prereq_accuracy = 0.0 if prereq_stats is None else prereq_stats.recent_accuracy
    prereq_attempts = 0 if prereq_stats is None else prereq_stats.attempts
    prereq_mastery = "Not started" if prereq_stats is None else prereq_stats.mastery

    if target_stats.recent_accuracy < 70.0 and prereq_accuracy < 75.0:
        return GraphTuningSuggestion(
            target,
            prereq,
            "increase",
            0.10,
            (
                f"{target} recent accuracy {target_stats.recent_accuracy:.0f}% over {target_stats.attempts} attempts; "
                f"{prereq} {prereq_mastery.lower()} at {prereq_accuracy:.0f}% over {prereq_attempts} attempts."
            ),
        )
    if target_stats.recent_accuracy >= 88.0 and prereq_accuracy >= 88.0 and current_weight > 0.35:
        return GraphTuningSuggestion(
            target,
            prereq,
            "taper",
            -0.05,
            (
                f"{target} stable at {target_stats.recent_accuracy:.0f}% and "
                f"{prereq} stable at {prereq_accuracy:.0f}%."
            ),
        )
    if target_stats.recent_accuracy < 75.0 and prereq_mastery in {"Needs work", "Developing", "Not started"}:
        return GraphTuningSuggestion(
            target,
            prereq,
            "monitor",
            0.00,
            f"{target} is below 75% while {prereq} is {prereq_mastery.lower()}.",
        )
    return None


def _prereq_edges(skill: str, prerequisites: dict[str, tuple[object, ...]]) -> list[tuple[str, float]]:
    edges: list[tuple[str, float]] = []
    for item in prerequisites.get(skill, ()):
        if not isinstance(item, tuple) or not item:
            continue
        prereq = str(item[0])
        weight = float(item[2] if len(item) >= 3 else item[1] if len(item) >= 2 else 1.0)
        edges.append((prereq, max(0.0, weight)))
    return edges


def _parse_iso(value: str) -> datetime:
    cleaned = value.replace("Z", "+00:00")
    parsed = datetime.fromisoformat(cleaned)
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)
