from __future__ import annotations

from collections.abc import Callable
import random

from .. import db
from ..quiz_engine import Question, generate_question
from ..ui_settings import load_ui_settings
from .generation import generate_depth_question
from .models import ContentStatus, QuestionRequest, ReasoningKind
from .registry import depth_spec_for
from .units import cumulative_mix


Target = tuple[str, str | None]
TargetResolver = Callable[[str, str, str | None, str], list[Target]]


def cumulative_targets_for_task(task, target_resolver: TargetResolver) -> list[Target]:
    targets: list[Target] = []
    seen_units: set[str] = set()
    for prior in db.list_summer_program_tasks(task.program_id):
        if prior.sequence_index > task.sequence_index or prior.unit_code in seen_units:
            continue
        if prior.task_kind in {"placement_assessment", "remediation_review"}:
            continue
        seen_units.add(prior.unit_code)
        for target in target_resolver(prior.unit_code, prior.skill, prior.subskill, prior.task_kind):
            if target not in targets:
                targets.append(target)
    return targets


def cumulative_target_schedule(
    current: list[Target], all_targets: list[Target], count: int
) -> list[tuple[Target, bool]]:
    mix = cumulative_mix(count)
    earlier = [target for target in all_targets if target not in current]
    current_count = mix.current + (mix.earlier if not earlier else 0)
    earlier_count = mix.earlier if earlier else 0
    schedule = [(_cycle(current, index), False) for index in range(current_count)]
    schedule.extend((_cycle(earlier, index), False) for index in range(earlier_count))
    application_pool = [*current, *earlier]
    schedule.extend((_cycle(application_pool, index), True) for index in range(mix.application))
    return schedule


def _cycle(targets: list[Target], index: int) -> Target:
    if not targets:
        raise ValueError("A cumulative schedule needs at least one target.")
    return targets[index % len(targets)]


def program_question(
    skill: str,
    subskill: str | None,
    level: int,
    used: dict[tuple[str, str], set[str]],
    *,
    application: bool,
) -> Question:
    spec = depth_spec_for(skill, subskill)
    if (
        not load_ui_settings().curriculum_depth_beta
        or spec is None
        or spec.content_status is not ContentStatus.READY
        or subskill is None
    ):
        return generate_question(skill, level, "typed", subskill=subskill)
    key = (skill, subskill)
    seen = used.setdefault(key, set())
    eligible = [item for item in spec.archetypes if item.reasoning_kind is not ReasoningKind.PROOF]
    desired = ReasoningKind.APPLICATION if application else None
    candidates = [
        item for item in eligible
        if item.archetype_id not in seen and (desired is None or item.reasoning_kind is desired)
    ]
    if not candidates:
        candidates = [item for item in eligible if item.archetype_id not in seen]
    if not candidates:
        seen.clear()
        candidates = [item for item in eligible if desired is None or item.reasoning_kind is desired] or eligible
    archetype = random.choice(candidates)
    seen.add(archetype.archetype_id)
    return generate_depth_question(
        QuestionRequest(skill, level, "typed", subskill, preferred_archetype_id=archetype.archetype_id)
    )
