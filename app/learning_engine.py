from __future__ import annotations

from dataclasses import dataclass
from collections import defaultdict
from typing import Iterable

from .models import QuizAttempt


MASTERY_LEVEL = {
    "Needs work": 0.0,
    "Developing": 1.0,
    "Proficient": 2.0,
    "Mastered": 3.0,
    "Not started": 0.0,
}


@dataclass(frozen=True)
class SkillStats:
    skill: str
    attempts: int
    total_questions: int
    correct_questions: int
    weighted_accuracy: float
    recent_accuracy: float
    perfect_attempts: int
    perfect_streak: int
    avg_seconds_per_question: float | None
    recent_trend: float
    mastery: str


@dataclass(frozen=True)
class PlanItem:
    skill: str
    label: str


@dataclass(frozen=True)
class BlendPolicy:
    core_pct: int
    prereq_pct: int
    review_pct: int


@dataclass(frozen=True)
class FreeModePolicy:
    core_pct: int
    preview_pct: int
    prereq_pct: int
    review_pct: int


@dataclass(frozen=True)
class ModeMix:
    intuition: int
    expression: int
    word: int


def build_skill_stats(attempts: list[QuizAttempt], skill_order: tuple[str, ...], recent_window: int = 5) -> dict[str, SkillStats]:
    grouped: dict[str, list[QuizAttempt]] = defaultdict(list)
    for attempt in attempts:
        grouped[attempt.skill].append(attempt)

    stats: dict[str, SkillStats] = {}
    for skill in skill_order:
        skill_attempts = grouped.get(skill, [])
        stats[skill] = _stats_for_skill(skill, skill_attempts, recent_window)
    return stats


def recommend_next_skills_soft(
    skill_order: tuple[str, ...],
    prerequisites: dict[str, tuple[object, ...]],
    stats: dict[str, SkillStats],
    subskill_coverage: dict[str, float] | None = None,
    limit: int = 3,
) -> list[str]:
    limit = max(1, int(limit))
    retake_required = [
        skill
        for skill in skill_order
        if (stats.get(skill) is not None and stats[skill].attempts > 0 and stats[skill].perfect_attempts == 0)
    ]
    if retake_required:
        retake_required.sort(
            key=lambda s: (
                _mastery_rank(stats.get(s)),
                stats[s].weighted_accuracy,
                skill_order.index(s),
            )
        )
        return retake_required[:limit]

    candidates: list[tuple[float, str]] = []
    for idx, skill in enumerate(skill_order):
        item = stats.get(skill)
        if item is None:
            continue
        if item.mastery == "Mastered":
            continue

        status_score = {
            "Needs work": 90.0,
            "Developing": 70.0,
            "Not started": 65.0,
            "Proficient": 35.0,
            "Mastered": 0.0,
        }.get(item.mastery, 50.0)

        prereq_weight = _prereq_readiness(skill, prerequisites, stats)
        coverage_score = _coverage_gap_bonus(skill, subskill_coverage)
        recent_performance = max(0.0, 85.0 - item.recent_accuracy) * 0.25
        downward_trend = max(0.0, -item.recent_trend) * 0.35
        # Soft graph: all skills stay eligible; prereq readiness nudges score.
        score = status_score + prereq_weight + coverage_score + recent_performance + downward_trend - (idx * 0.2)
        candidates.append((score, skill))

    if not candidates:
        return list(skill_order[:limit])

    candidates.sort(key=lambda row: (-row[0], skill_order.index(row[1])))
    return [skill for _score, skill in candidates[:limit]]


def pick_blend_policy(target_stats: SkillStats | None) -> BlendPolicy:
    if target_stats is None or target_stats.attempts == 0:
        return BlendPolicy(core_pct=60, prereq_pct=25, review_pct=15)
    if target_stats.perfect_attempts == 0:
        return BlendPolicy(core_pct=80, prereq_pct=15, review_pct=5)

    target_recent = target_stats.recent_accuracy
    if target_recent < 60:
        return BlendPolicy(core_pct=45, prereq_pct=40, review_pct=15)
    if target_recent < 75:
        return BlendPolicy(core_pct=55, prereq_pct=30, review_pct=15)
    if target_recent > 85:
        return BlendPolicy(core_pct=70, prereq_pct=15, review_pct=15)
    return BlendPolicy(core_pct=60, prereq_pct=25, review_pct=15)


def default_mode_mix_for_stage(target_stats: SkillStats | None) -> ModeMix:
    if target_stats is None or target_stats.attempts == 0:
        return ModeMix(intuition=45, expression=40, word=15)
    if target_stats.mastery in {"Needs work", "Developing", "Not started"}:
        return ModeMix(intuition=30, expression=45, word=25)
    return ModeMix(intuition=20, expression=40, word=40)


def apply_word_gap_boost(base: ModeMix, expression_acc: float | None, word_acc: float | None) -> ModeMix:
    if expression_acc is None or word_acc is None:
        return base
    gap = expression_acc - word_acc
    if gap < 8.0:
        return base
    boost = 10 if gap < 15.0 else 20
    moved_from = "intuition" if base.intuition >= base.expression else "expression"
    intuition = base.intuition
    expression = base.expression
    word = base.word
    if moved_from == "intuition":
        delta = min(boost, intuition)
        intuition -= delta
        word += delta
    else:
        delta = min(boost, expression)
        expression -= delta
        word += delta
    return normalize_mode_mix(intuition, expression, word)


def normalize_mode_mix(intuition: int | None, expression: int | None, word: int | None) -> ModeMix:
    values = [intuition, expression, word]
    if any(v is None for v in values):
        raise ValueError("mode mix values cannot be None")
    ints = [max(0, int(v)) for v in values]
    total = sum(ints)
    if total <= 0:
        return ModeMix(intuition=30, expression=45, word=25)
    if total == 100:
        return ModeMix(intuition=ints[0], expression=ints[1], word=ints[2])
    scaled = [round((float(v) / float(total)) * 100.0) for v in ints]
    drift = 100 - sum(scaled)
    # Apply rounding drift to expression first, then intuition, then word.
    order = [1, 0, 2]
    idx = 0
    while drift != 0:
        target = order[idx % len(order)]
        if drift > 0:
            scaled[target] += 1
            drift -= 1
        elif scaled[target] > 0:
            scaled[target] -= 1
            drift += 1
        idx += 1
    return ModeMix(intuition=scaled[0], expression=scaled[1], word=scaled[2])


def build_blended_plan(
    *,
    target_skill: str,
    num_questions: int,
    skill_order: tuple[str, ...],
    prerequisites: dict[str, tuple[object, ...]],
    stats: dict[str, SkillStats],
) -> tuple[list[PlanItem], BlendPolicy]:
    total = max(1, int(num_questions))
    policy = pick_blend_policy(stats.get(target_skill))

    core_count = round(total * (policy.core_pct / 100.0))
    prereq_count = round(total * (policy.prereq_pct / 100.0))
    review_count = max(0, total - core_count - prereq_count)

    prereq_pool = [edge[0] for edge in _prereq_edges(target_skill, prerequisites)]
    prereq_pool.sort(key=lambda s: (_mastery_rank(stats.get(s)), skill_order.index(s)))

    review_pool = [
        skill
        for skill in skill_order
        if skill != target_skill and stats.get(skill, _empty_skill_stats(skill)).attempts > 0
    ]
    review_pool.sort(key=lambda s: (_mastery_rank(stats.get(s)), skill_order.index(s)))

    if total >= 6 and review_pool and review_count <= 0:
        review_count = 1
        if core_count >= prereq_count and core_count > 0:
            core_count -= 1
        elif prereq_count > 0:
            prereq_count -= 1

    items: list[PlanItem] = [PlanItem(target_skill, "Core") for _ in range(core_count)]

    if prereq_pool:
        for i in range(prereq_count):
            items.append(PlanItem(prereq_pool[i % len(prereq_pool)], "Prereq"))
    else:
        items.extend(PlanItem(target_skill, "Core") for _ in range(prereq_count))

    if review_pool:
        for i in range(review_count):
            items.append(PlanItem(review_pool[i % len(review_pool)], "Review"))
    else:
        items.extend(PlanItem(target_skill, "Core") for _ in range(review_count))

    return items[:total], policy


def pick_free_mode_policy(target_stats: SkillStats | None) -> FreeModePolicy:
    if target_stats is None or target_stats.attempts == 0:
        return FreeModePolicy(core_pct=45, preview_pct=25, prereq_pct=20, review_pct=10)
    recent = target_stats.recent_accuracy
    if recent < 60:
        return FreeModePolicy(core_pct=55, preview_pct=15, prereq_pct=20, review_pct=10)
    if recent < 75:
        return FreeModePolicy(core_pct=45, preview_pct=20, prereq_pct=20, review_pct=15)
    if recent > 85:
        return FreeModePolicy(core_pct=30, preview_pct=30, prereq_pct=15, review_pct=25)
    return FreeModePolicy(core_pct=40, preview_pct=25, prereq_pct=20, review_pct=15)


def build_free_mode_plan(
    *,
    target_skill: str,
    num_questions: int,
    skill_order: tuple[str, ...],
    prerequisites: dict[str, tuple[object, ...]],
    stats: dict[str, SkillStats],
) -> tuple[list[PlanItem], FreeModePolicy]:
    total = max(1, int(num_questions))
    policy = pick_free_mode_policy(stats.get(target_skill))

    core_count = round(total * (policy.core_pct / 100.0))
    preview_count = round(total * (policy.preview_pct / 100.0))
    prereq_count = round(total * (policy.prereq_pct / 100.0))
    # Keep first pass from over-allocating before review count is computed.
    while (core_count + preview_count + prereq_count) > total:
        if core_count >= prereq_count and core_count >= preview_count and core_count > 0:
            core_count -= 1
        elif prereq_count >= preview_count and prereq_count > 0:
            prereq_count -= 1
        elif preview_count > 0:
            preview_count -= 1
        else:
            break
    review_count = max(0, total - core_count - preview_count - prereq_count)

    preview_skill = _next_preview_skill(target_skill, skill_order, stats)
    prereq_pool = [edge[0] for edge in _prereq_edges(target_skill, prerequisites)]
    prereq_pool.sort(key=lambda s: (_mastery_rank(stats.get(s)), skill_order.index(s)))

    maintenance_pool = [
        skill
        for skill in skill_order
        if skill not in {target_skill, preview_skill}
        and stats.get(skill, _empty_skill_stats(skill)).attempts > 0
    ]
    maintenance_pool.sort(
        key=lambda s: (
            0 if stats.get(s, _empty_skill_stats(s)).mastery in {"Proficient", "Mastered"} else 1,
            _mastery_rank(stats.get(s)),
            skill_order.index(s),
        )
    )

    if total >= 6 and preview_skill is not None and preview_count <= 0:
        preview_count = 1
        if core_count > 0:
            core_count -= 1
        elif prereq_count > 0:
            prereq_count -= 1
    if total >= 6 and maintenance_pool and review_count <= 0:
        review_count = 1
        if core_count > 0:
            core_count -= 1
        elif prereq_count > 0:
            prereq_count -= 1
        elif preview_count > 0:
            preview_count -= 1

    items: list[PlanItem] = [PlanItem(target_skill, "Core") for _ in range(max(0, core_count))]
    if preview_skill is not None:
        items.extend(PlanItem(preview_skill, "Preview") for _ in range(max(0, preview_count)))
    else:
        items.extend(PlanItem(target_skill, "Core") for _ in range(max(0, preview_count)))

    if prereq_pool:
        for i in range(max(0, prereq_count)):
            items.append(PlanItem(prereq_pool[i % len(prereq_pool)], "Prereq"))
    else:
        items.extend(PlanItem(target_skill, "Core") for _ in range(max(0, prereq_count)))

    if maintenance_pool:
        for i in range(max(0, review_count)):
            items.append(PlanItem(maintenance_pool[i % len(maintenance_pool)], "Review"))
    else:
        items.extend(PlanItem(target_skill, "Core") for _ in range(max(0, review_count)))

    return items[:total], policy


def _stats_for_skill(skill: str, attempts: list[QuizAttempt], recent_window: int) -> SkillStats:
    if not attempts:
        return _empty_skill_stats(skill)

    chronological = sorted(attempts, key=lambda a: a.created_at)
    pcts: list[float] = []
    total_questions = 0
    correct_questions = 0
    perfect_attempts = 0
    perfect_streak = 0
    timed_questions = 0
    timed_seconds = 0.0
    for attempt in chronological:
        total = max(1, int(attempt.num_questions))
        pct = (float(attempt.score) / float(total)) * 100.0
        pcts.append(pct)
        total_questions += total
        correct_questions += int(attempt.score)
        if int(attempt.score) == total:
            perfect_attempts += 1
    for attempt in reversed(chronological):
        total = max(1, int(attempt.num_questions))
        if int(attempt.score) != total:
            break
        perfect_streak += 1
    for attempt in chronological:
        if attempt.elapsed_seconds is None:
            continue
        elapsed = max(0.0, float(attempt.elapsed_seconds))
        if elapsed <= 0.0:
            continue
        timed_seconds += elapsed
        timed_questions += max(1, int(attempt.num_questions))

    weighted = _ewma(pcts, alpha=0.25)
    window = max(1, int(recent_window))
    recent_slice = pcts[-window:]
    recent = sum(recent_slice) / float(len(recent_slice))
    trend = _recent_trend(pcts)
    avg_seconds_per_question = (timed_seconds / float(timed_questions)) if timed_questions > 0 else None
    mastery = mastery_label(len(chronological), weighted, recent, perfect_attempts)

    return SkillStats(
        skill=skill,
        attempts=len(chronological),
        total_questions=total_questions,
        correct_questions=correct_questions,
        weighted_accuracy=weighted,
        recent_accuracy=recent,
        perfect_attempts=perfect_attempts,
        perfect_streak=perfect_streak,
        avg_seconds_per_question=avg_seconds_per_question,
        recent_trend=trend,
        mastery=mastery,
    )


def mastery_label(attempts: int, weighted_accuracy: float, recent_accuracy: float, perfect_attempts: int) -> str:
    if attempts <= 0:
        return "Not started"

    blended = (weighted_accuracy * 0.7) + (recent_accuracy * 0.3)
    if blended >= 95 and perfect_attempts >= 1:
        return "Mastered"
    if blended >= 85:
        return "Proficient"
    if blended >= 65:
        return "Developing"
    return "Needs work"


def _ewma(values: list[float], alpha: float) -> float:
    if not values:
        return 0.0
    score = float(values[0])
    for value in values[1:]:
        score = (alpha * float(value)) + ((1.0 - alpha) * score)
    return score


def _prereq_readiness(skill: str, prerequisites: dict[str, tuple[object, ...]], stats: dict[str, SkillStats]) -> float:
    prereqs = _prereq_edges(skill, prerequisites)
    if not prereqs:
        return 20.0
    values: list[float] = []
    total_weight = 0.0
    for prereq, weight in prereqs:
        stat = stats.get(prereq)
        if stat is None:
            values.append(0.0)
            total_weight += weight
            continue
        values.append((MASTERY_LEVEL.get(stat.mastery, 0.0) / 3.0) * weight)
        total_weight += weight
    if total_weight <= 0:
        return 0.0
    return (sum(values) / float(total_weight)) * 30.0


def _mastery_rank(stat: SkillStats | None) -> int:
    if stat is None:
        return 0
    rank = {
        "Needs work": 0,
        "Developing": 1,
        "Not started": 2,
        "Proficient": 3,
        "Mastered": 4,
    }
    return rank.get(stat.mastery, 1)


def _recent_trend(pcts: list[float]) -> float:
    if len(pcts) < 2:
        return 0.0
    window = pcts[-min(len(pcts), 6):]
    mid = len(window) // 2
    if mid <= 0:
        return 0.0
    early = window[:mid]
    late = window[-mid:]
    if not early or not late:
        return 0.0
    return (sum(late) / float(len(late))) - (sum(early) / float(len(early)))


def _prereq_edges(skill: str, prerequisites: dict[str, tuple[object, ...]]) -> list[tuple[str, float]]:
    raw: Iterable[object] = prerequisites.get(skill, ())
    edges: list[tuple[str, float]] = []
    for item in raw:
        if isinstance(item, tuple):
            if not item:
                continue
            prereq = str(item[0])
            if len(item) >= 2:
                weight = max(0.0, float(item[1]))
            else:
                weight = 1.0
        else:
            prereq = str(item)
            weight = 1.0
        edges.append((prereq, weight))
    return edges


def _coverage_gap_bonus(skill: str, coverage: dict[str, float] | None) -> float:
    if coverage is None:
        return 0.0
    value = coverage.get(skill)
    if value is None:
        return 8.0
    normalized = min(1.0, max(0.0, float(value)))
    return (1.0 - normalized) * 15.0


def _empty_skill_stats(skill: str) -> SkillStats:
    return SkillStats(
        skill=skill,
        attempts=0,
        total_questions=0,
        correct_questions=0,
        weighted_accuracy=0.0,
        recent_accuracy=0.0,
        perfect_attempts=0,
        perfect_streak=0,
        avg_seconds_per_question=None,
        recent_trend=0.0,
        mastery="Not started",
    )


def _next_preview_skill(target_skill: str, skill_order: tuple[str, ...], stats: dict[str, SkillStats]) -> str | None:
    if target_skill not in skill_order:
        for skill in skill_order:
            if skill != target_skill:
                return skill
        return None
    idx = skill_order.index(target_skill)
    forward = skill_order[idx + 1 :]
    for skill in forward:
        if stats.get(skill, _empty_skill_stats(skill)).mastery != "Mastered":
            return skill
    for skill in forward:
        if skill != target_skill:
            return skill
    for skill in skill_order:
        if skill != target_skill and stats.get(skill, _empty_skill_stats(skill)).mastery != "Mastered":
            return skill
    for skill in skill_order:
        if skill != target_skill:
            return skill
    return None
