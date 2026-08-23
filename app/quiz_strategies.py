from __future__ import annotations

from dataclasses import dataclass
import random

from . import db
from .learning_engine import SkillStats, build_blended_plan, build_free_mode_plan, recommend_next_skills_soft
from .quiz_engine import Question
from .skill_graph import SKILL_ORDER, SKILL_PREREQUISITE_WEIGHTS


@dataclass(slots=True)
class StrategyResult:
    questions: list[Question]
    attempt_skill: str
    meta: str
    record_progress: bool = True


def build_historical_questions(panel) -> StrategyResult | None:
    rows = db.list_historical_questions(
        exam_type=panel.historical_exam_filter_var.get(),
        category=panel.historical_category_var.get(),
        limit=panel.num_var.get(),
    )
    if not rows:
        return None

    questions: list[Question] = []
    for row in rows:
        choices = [c for c in [row.choice_a, row.choice_b, row.choice_c, row.choice_d, row.choice_e] if c]
        questions.append(
            Question(
                skill=f"historical_{panel.historical_exam_filter_var.get()}_{row.category}",
                prompt=row.prompt,
                correct_answer=str(row.correct_answer or ""),
                explanation=row.explanation or "Historical item.",
                choices=choices if choices else None,
                visual=None,
                template_id=None,
                template_external_id=f"historical.q{row.id}",
                subskill=row.category,
                question_label=f"Historical {row.section}",
                mode="word",
            )
        )

    return StrategyResult(
        questions=questions,
        attempt_skill="historical_practice",
        meta=(
            f"Historical practice: exam={panel.historical_exam_filter_var.get()} "
            f"category={panel.historical_category_var.get()}"
        ),
        record_progress=False,
    )


def build_sat_psat_questions(
    panel,
    *,
    profile_id: int,
    skill_stats: dict[str, SkillStats],
    mode_acc_cache: dict[str, dict[str, float]],
    active_override: tuple[int, int, int] | None,
    seen_signatures: set[str],
) -> StrategyResult:
    sat_psat_pool = ("sat_math", "psat_math")
    questions: list[Question] = []
    last_family = ""

    for idx in range(panel.num_var.get()):
        q_type = panel.type_var.get()
        if q_type == "both":
            q_type = "mc" if idx % 2 == 0 else "typed"
        q_skill = sat_psat_pool[idx % len(sat_psat_pool)]
        mode_mix = panel._mode_mix_for_skill(
            profile_id,
            q_skill,
            skill_stats,
            mode_acc_cache,
            active_override,
            subskill=None,
        )
        preferred_mode = panel._pick_mode(mode_mix, q_skill, subskill=None)
        q = panel._generate_question_with_variation(
            seen_signatures,
            q_skill,
            panel.level_var.get(),
            q_type,
            subskill=None,
            preferred_mode=preferred_mode,
        )
        for _ in range(8):
            family = panel._template_family(q)
            if not family or family != last_family:
                break
            q = panel._generate_question_with_variation(
                seen_signatures,
                q_skill,
                panel.level_var.get(),
                q_type,
                subskill=None,
                preferred_mode=preferred_mode,
            )
        q.question_label = "SAT Unit" if q_skill == "sat_math" else "PSAT Unit"
        q = panel._apply_mode_preference(q, preferred_mode)
        questions.append(q)
        last_family = panel._template_family(q)

    return StrategyResult(
        questions=questions,
        attempt_skill="sat_math",
        meta="SAT/PSAT Unit: SAT+PSAT questions only",
    )


def build_free_mode_questions(
    panel,
    *,
    profile_id: int,
    selected_skill: str,
    chosen_subskill: str | None,
    skill_stats: dict[str, SkillStats],
    mode_acc_cache: dict[str, dict[str, float]],
    active_override: tuple[int, int, int] | None,
    seen_signatures: set[str],
) -> StrategyResult:
    target_skill = selected_skill
    if target_skill == "mixed":
        target_skill = (
            recommend_next_skills_soft(
                tuple(SKILL_ORDER),
                SKILL_PREREQUISITE_WEIGHTS,
                skill_stats,
                subskill_coverage=panel._subskill_coverage_by_skill(profile_id),
                limit=1,
            )[0]
            if SKILL_ORDER
            else "counting"
        )

    plan_items, policy = build_free_mode_plan(
        target_skill=target_skill,
        num_questions=panel.num_var.get(),
        skill_order=tuple(SKILL_ORDER),
        prerequisites=SKILL_PREREQUISITE_WEIGHTS,
        stats=skill_stats,
    )
    random.shuffle(plan_items)

    questions: list[Question] = []
    for idx, item in enumerate(plan_items):
        q_type = panel.type_var.get()
        if q_type == "both":
            q_type = "mc" if idx % 2 == 0 else "typed"
        q_level = panel.level_var.get() + 1 if item.label == "Preview" else panel.level_var.get()
        q_level = max(1, min(3, int(q_level)))
        subskill = chosen_subskill if (item.label == "Core" and item.skill == target_skill) else None
        mode_mix = panel._mode_mix_for_skill(
            profile_id,
            item.skill,
            skill_stats,
            mode_acc_cache,
            active_override,
            subskill=subskill,
        )
        preferred_mode = panel._pick_mode(mode_mix, item.skill, subskill=subskill)
        q = panel._generate_question_with_variation(
            seen_signatures,
            item.skill,
            q_level,
            q_type,
            subskill=subskill,
            preferred_mode=preferred_mode,
        )
        q.question_label = item.label
        q = panel._apply_mode_preference(q, preferred_mode)
        questions.append(q)

    mix_text = panel._mode_mix_label(
        panel._mode_mix_for_skill(
            profile_id,
            target_skill,
            skill_stats,
            mode_acc_cache,
            active_override,
            subskill=chosen_subskill,
        )
    )
    meta = (
        "Free Mode "
        f"{target_skill}: C/Pv/Pr/R {policy.core_pct}/{policy.preview_pct}/{policy.prereq_pct}/{policy.review_pct} "
        f"| Modes I/E/W: {mix_text}"
    )
    return StrategyResult(questions=questions, attempt_skill=target_skill, meta=meta)


def build_learning_blend_questions(
    panel,
    *,
    profile_id: int,
    selected_skill: str,
    chosen_subskill: str | None,
    skill_stats: dict[str, SkillStats],
    mode_acc_cache: dict[str, dict[str, float]],
    active_override: tuple[int, int, int] | None,
    seen_signatures: set[str],
) -> StrategyResult:
    plan_items, policy = build_blended_plan(
        target_skill=selected_skill,
        num_questions=panel.num_var.get(),
        skill_order=tuple(SKILL_ORDER),
        prerequisites=SKILL_PREREQUISITE_WEIGHTS,
        stats=skill_stats,
    )
    random.shuffle(plan_items)

    questions: list[Question] = []
    for idx, item in enumerate(plan_items):
        q_type = panel.type_var.get()
        if q_type == "both":
            q_type = "mc" if idx % 2 == 0 else "typed"
        subskill = chosen_subskill if item.label == "Core" else None
        mode_mix = panel._mode_mix_for_skill(
            profile_id,
            item.skill,
            skill_stats,
            mode_acc_cache,
            active_override,
            subskill=subskill,
        )
        preferred_mode = panel._pick_mode(mode_mix, item.skill, subskill=subskill)
        q = panel._generate_question_with_variation(
            seen_signatures,
            item.skill,
            panel.level_var.get(),
            q_type,
            subskill=subskill,
            preferred_mode=preferred_mode,
        )
        q.question_label = item.label
        q = panel._apply_mode_preference(q, preferred_mode)
        questions.append(q)

    mix_text = panel._mode_mix_label(
        panel._mode_mix_for_skill(
            profile_id,
            selected_skill,
            skill_stats,
            mode_acc_cache,
            active_override,
            subskill=chosen_subskill,
        )
    )
    meta = f"Blend: {policy.core_pct}/{policy.prereq_pct}/{policy.review_pct} | Modes I/E/W: {mix_text}"
    return StrategyResult(questions=questions, attempt_skill=selected_skill, meta=meta)


def build_focused_questions(
    panel,
    *,
    profile_id: int,
    selected_skill: str,
    chosen_subskill: str | None,
    skill_stats: dict[str, SkillStats],
    mode_acc_cache: dict[str, dict[str, float]],
    active_override: tuple[int, int, int] | None,
    seen_signatures: set[str],
) -> StrategyResult:
    questions: list[Question] = []
    mode_mix = panel._mode_mix_for_skill(
        profile_id,
        selected_skill,
        skill_stats,
        mode_acc_cache,
        active_override,
        subskill=chosen_subskill,
    )
    for idx in range(panel.num_var.get()):
        q_type = panel.type_var.get()
        if q_type == "both":
            q_type = "mc" if idx % 2 == 0 else "typed"
        preferred_mode = panel._pick_mode(mode_mix, selected_skill, subskill=chosen_subskill)
        q = panel._generate_question_with_variation(
            seen_signatures,
            selected_skill,
            panel.level_var.get(),
            q_type,
            subskill=chosen_subskill,
            preferred_mode=preferred_mode,
        )
        q.question_label = "Core"
        q = panel._apply_mode_preference(q, preferred_mode)
        questions.append(q)

    meta = f"Modes I/E/W: {panel._mode_mix_label(mode_mix)}"
    return StrategyResult(questions=questions, attempt_skill=selected_skill, meta=meta)
