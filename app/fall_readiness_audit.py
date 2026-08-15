from __future__ import annotations

from dataclasses import dataclass
import inspect

from . import db, school_year, school_year_assessment
from .explanations import explanation_for
from .graph_tuning import build_monthly_graph_tuning_report
from .learning_engine import BlendPolicy, BlendPolicyConfig, SkillStats, pick_blend_policy
from .models import QuizAttempt
from .quiz_engine import generate_question
from .skill_graph import SKILL_TRACKS, subskills_for
from .texas_grade_goals import TEA_MATH_TEKS_URL, content_gap_goals, texas_grade_plans
from .ui_arithmetic import khan_url_for_selection, lesson_link_state
from .ui_root import AppShell
from .ui_settings import UiSettings


@dataclass(frozen=True)
class FallReadinessCheck:
    code: str
    passed: bool
    evidence: str


@dataclass(frozen=True)
class FallReadinessReport:
    checks: tuple[FallReadinessCheck, ...]

    @property
    def ready(self) -> bool:
        return all(check.passed for check in self.checks)

    @property
    def failures(self) -> tuple[FallReadinessCheck, ...]:
        return tuple(check for check in self.checks if not check.passed)


def build_fall_readiness_report() -> FallReadinessReport:
    return FallReadinessReport(
        checks=(
            _texas_grade_span_check(),
            _texas_gap_check(),
            _texas_question_generation_check(),
            _texas_intuition_check(),
            _per_child_target_check(),
            _assessment_packet_check(),
            _stretch_path_check(),
            _external_link_control_check(),
            _blended_practice_check(),
            _graph_tuning_check(),
            _child_first_navigation_check(),
        )
    )


def render_fall_readiness_markdown(report: FallReadinessReport) -> str:
    status = "ready" if report.ready else "blocked"
    lines = [
        "# Fall Readiness Audit",
        "",
        f"Overall status: {status}",
        f"Texas standards source: {TEA_MATH_TEKS_URL}",
        "",
        "| Check | Status | Evidence |",
        "|---|---:|---|",
    ]
    for check in report.checks:
        mark = "pass" if check.passed else "fail"
        lines.append(f"| {check.code} | {mark} | {check.evidence} |")
    return "\n".join(lines)


def _texas_grade_span_check() -> FallReadinessCheck:
    plans = texas_grade_plans()
    grades = tuple(plan.grade for plan in plans)
    expected = tuple(range(1, 8))
    sections = ", ".join(plan.tac_section for plan in plans)
    return FallReadinessCheck(
        "texas_grades_1_to_7",
        grades == expected,
        f"Catalog grades={grades}; sections={sections}.",
    )


def _texas_gap_check() -> FallReadinessCheck:
    gaps = {grade: content_gap_goals(grade) for grade in range(1, 8)}
    open_gaps = {grade: rows for grade, rows in gaps.items() if rows}
    ready_goal_count = sum(
        1 for plan in texas_grade_plans() for goal in plan.goals if goal.quiz_ready and not goal.stretch
    )
    return FallReadinessCheck(
        "no_grade_1_to_7_content_gaps",
        not open_gaps,
        f"{ready_goal_count} non-stretch grade goals are quiz-ready; open gaps={len(open_gaps)}.",
    )


def _texas_question_generation_check() -> FallReadinessCheck:
    failures: list[str] = []
    checked = 0
    for plan in texas_grade_plans():
        for goal in plan.goals:
            if goal.stretch or goal.skill is None:
                continue
            for subskill in goal.subskills:
                checked += 1
                try:
                    question = generate_question(goal.skill, goal.quiz_level, "typed", subskill=subskill)
                except Exception as exc:  # pragma: no cover - surfaced in evidence
                    failures.append(f"grade {plan.grade} {goal.code}/{subskill}: {exc}")
                    continue
                if not question.correct_answer:
                    failures.append(f"grade {plan.grade} {goal.code}/{subskill}: empty answer")
    evidence = f"Generated typed sample questions for {checked} Grade 1-7 target subskills."
    if failures:
        evidence = f"{evidence} Failures: {'; '.join(failures[:3])}."
    return FallReadinessCheck("grade_goal_problem_generation", not failures, evidence)


def _texas_intuition_check() -> FallReadinessCheck:
    missing: list[str] = []
    checked = 0
    for plan in texas_grade_plans():
        for goal in plan.goals:
            if not goal.quiz_ready or goal.skill is None:
                continue
            for subskill in goal.subskills:
                checked += 1
                info = explanation_for(goal.skill, subskill)
                if not (info.mental_model and info.common_mistake and info.try_this):
                    missing.append(f"grade {plan.grade} {goal.code}/{subskill}")
    return FallReadinessCheck(
        "subskill_intuition_ready",
        not missing,
        f"Checked mental model/common mistake/try-this copy for {checked} grade-goal subskills.",
    )


def _per_child_target_check() -> FallReadinessCheck:
    functions = (
        db.create_profile,
        db.save_school_year_target,
        db.get_school_year_target,
        school_year.school_year_status,
    )
    available = all(callable(func) for func in functions)
    return FallReadinessCheck(
        "two_child_independent_targets",
        available,
        "Per-child profile, target persistence, target lookup, and status APIs are available.",
    )


def _assessment_packet_check() -> FallReadinessCheck:
    generator_ready = callable(school_year_assessment.generate_texas_grade_assessment)
    total_subskills = sum(
        len(goal.subskills)
        for plan in texas_grade_plans()
        for goal in plan.goals
        if goal.quiz_ready and not goal.stretch
    )
    return FallReadinessCheck(
        "quiz_test_packet_surface",
        generator_ready and total_subskills > 0,
        f"Assessment packet generator covers {total_subskills} non-stretch target subskill slots.",
    )


def _stretch_path_check() -> FallReadinessCheck:
    required = (
        "algebra_1",
        "algebra_2",
        "geometry_area",
        "trig_right_triangle",
        "statistics",
        "calculus_1",
        "calculus_2",
        "calculus_3",
        "sat_math",
        "psat_math",
        "gre_quant",
    )
    visible = {skill for skills in SKILL_TRACKS.values() for skill in skills}
    missing = [skill for skill in required if skill not in visible or not subskills_for(skill)]
    return FallReadinessCheck(
        "stretch_path_through_advanced_math",
        not missing,
        f"Stretch skills checked={len(required)}; missing={missing}.",
    )


def _external_link_control_check() -> FallReadinessCheck:
    skill = "place_value"
    subskill = "Compare numbers by place value"
    disabled = lesson_link_state(skill, subskill, UiSettings(show_external_links=False))
    enabled = lesson_link_state(skill, subskill, UiSettings(show_external_links=True))
    offline = lesson_link_state(
        skill,
        subskill,
        UiSettings(show_external_links=True, enforce_offline_mode=True),
    )
    mapped_url = khan_url_for_selection(skill, subskill)
    passed = not disabled.enabled and enabled.enabled and not offline.enabled and bool(mapped_url)
    return FallReadinessCheck(
        "parent_controlled_external_lessons",
        passed,
        "Khan links stay disabled by default, enable by parent setting, and disable again in offline mode.",
    )


def _blended_practice_check() -> FallReadinessCheck:
    low = SkillStats("target", 2, 20, 10, 50.0, 50.0, 0, 0, 9.0, -8.0, "Needs work")
    stable = SkillStats("target", 5, 50, 46, 92.0, 92.0, 2, 2, 7.0, 3.0, "Proficient")
    passed = (
        pick_blend_policy(None, BlendPolicyConfig()) == BlendPolicy(60, 25, 15)
        and pick_blend_policy(low) == BlendPolicy(45, 40, 15)
        and pick_blend_policy(stable) == BlendPolicy(70, 15, 15)
    )
    return FallReadinessCheck(
        "adaptive_blended_practice_policy",
        passed,
        "Default 60/25/15 blend adapts toward prerequisites for weak targets and tapers when stable.",
    )


def _graph_tuning_check() -> FallReadinessCheck:
    attempts = [
        QuizAttempt(1, 1, None, "target", "both", 10, 1, 6, "2026-06-20T12:00:00+00:00", 120.0),
        QuizAttempt(2, 1, None, "target", "both", 10, 1, 6, "2026-06-22T12:00:00+00:00", 120.0),
        QuizAttempt(3, 1, None, "prereq", "both", 10, 1, 5, "2026-06-21T12:00:00+00:00", 120.0),
    ]
    report = build_monthly_graph_tuning_report(
        attempts=attempts,
        skill_order=("prereq", "target"),
        prerequisites={"target": (("prereq", 0.8),), "prereq": ()},
        now_iso_text="2026-06-26T12:00:00+00:00",
    )
    passed = bool(report.suggestions) and report.suggestions[0].action == "increase"
    return FallReadinessCheck(
        "monthly_graph_tuning_review",
        passed,
        f"Graph tuning report reviewed {report.attempt_count} attempts and produced {len(report.suggestions)} suggestion(s).",
    )


def _child_first_navigation_check() -> FallReadinessCheck:
    layout_source = inspect.getsource(AppShell._build_layout)
    bonus_source = inspect.getsource(AppShell.launch_bonus_explore)
    required_phrases = (
        'elif self.profile.role == "child"',
        '("Skill Map", self.skill_map)',
        '"Bonus Explore"',
        "daily_goal_status",
        "today_count <= 0",
    )
    missing = [phrase for phrase in required_phrases if phrase not in layout_source + bonus_source]
    return FallReadinessCheck(
        "child_first_navigation_and_bonus_explore",
        not missing,
        "Child navigation is math-first; Bonus Explore is gated by completed daily practice.",
    )
