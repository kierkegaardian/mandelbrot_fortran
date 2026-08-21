from __future__ import annotations

from dataclasses import dataclass

from .quiz_engine import generate_question
from .summer_program_defs import lane_display_name, lane_units
from .summer_program_quiz import (
    PLACEMENT_BLUEPRINT,
    assessment_blueprint_for_lane,
    summer_unit_targets,
)
from .texas_grade_goals import (
    ELEMENTARY_TEKS_URL,
    MIDDLE_SCHOOL_TEKS_URL,
    TEA_MATH_TEKS_URL,
    TexasGoal,
    texas_grade_plans,
)


CORE_TEKS_ROOTS: dict[int, tuple[str, ...]] = {
    1: ("1.2", "1.3", "1.4", "1.5", "1.6", "1.7", "1.8", "1.9"),
    2: ("2.2", "2.3", "2.4", "2.5", "2.6", "2.7", "2.8", "2.9", "2.10", "2.11"),
    3: ("3.2", "3.3", "3.4", "3.5", "3.6", "3.7", "3.8", "3.9"),
    4: ("4.2", "4.3", "4.4", "4.5", "4.6", "4.7", "4.8", "4.9", "4.10"),
    5: ("5.2", "5.3", "5.4", "5.5", "5.6", "5.7", "5.8", "5.9", "5.10"),
    6: ("6.2", "6.3", "6.4", "6.5", "6.6", "6.7", "6.8", "6.9", "6.10", "6.11", "6.12", "6.13", "6.14"),
    7: ("7.2", "7.3", "7.4", "7.5", "7.6", "7.7", "7.8", "7.9", "7.10", "7.11", "7.12", "7.13"),
}

SUMMER_LANES: tuple[str, ...] = ("foundation_bridge", "prealgebra_finish")


@dataclass(frozen=True)
class TexasCoverageRow:
    grade: int
    teks_refs: tuple[str, ...]
    goal_code: str
    goal_label: str
    skill: str | None
    subskills: tuple[str, ...]
    curriculum_status: str
    summer_units: tuple[str, ...]
    quiz_surfaces: tuple[str, ...]
    coverage_status: str
    notes: tuple[str, ...]

    @property
    def teks_display(self) -> str:
        return ", ".join(self.teks_refs)

    @property
    def target_display(self) -> str:
        if self.skill is None:
            return "content gap"
        return f"{self.skill}: {'; '.join(self.subskills)}"


@dataclass(frozen=True)
class TexasCoverageReport:
    rows: tuple[TexasCoverageRow, ...]

    @property
    def missing_rows(self) -> tuple[TexasCoverageRow, ...]:
        return tuple(row for row in self.rows if row.coverage_status == "missing")

    @property
    def weak_rows(self) -> tuple[TexasCoverageRow, ...]:
        return tuple(row for row in self.rows if row.coverage_status.startswith("weak"))

    @property
    def diagnostic_only_rows(self) -> tuple[TexasCoverageRow, ...]:
        return tuple(row for row in self.rows if row.coverage_status == "diagnostic-only")

    @property
    def covered_roots_by_grade(self) -> dict[int, tuple[str, ...]]:
        covered: dict[int, set[str]] = {grade: set() for grade in CORE_TEKS_ROOTS}
        for row in self.rows:
            if row.curriculum_status != "gap":
                covered[row.grade].update(_root(ref) for ref in row.teks_refs)
        return {grade: tuple(sorted(roots, key=_root_sort_key)) for grade, roots in covered.items()}


def build_texas_coverage_report() -> TexasCoverageReport:
    unit_map = _summer_unit_map()
    assessment_map = _assessment_map()
    rows: list[TexasCoverageRow] = []
    for plan in texas_grade_plans():
        for goal in plan.goals:
            if goal.stretch:
                continue
            target_keys = _goal_target_keys(goal)
            unit_hits = _hits_for_keys(target_keys, unit_map)
            assessment_hits = _hits_for_keys(target_keys, assessment_map)
            quiz_hits = _quiz_surfaces(goal, assessment_hits)
            status, notes = _status_and_notes(goal, unit_hits, assessment_hits)
            rows.append(
                TexasCoverageRow(
                    grade=plan.grade,
                    teks_refs=goal.standard_refs,
                    goal_code=goal.code,
                    goal_label=goal.label,
                    skill=goal.skill,
                    subskills=goal.subskills,
                    curriculum_status="quiz-ready" if goal.quiz_ready else "gap",
                    summer_units=unit_hits,
                    quiz_surfaces=quiz_hits,
                    coverage_status=status,
                    notes=notes,
                )
            )
    return TexasCoverageReport(tuple(rows))


def render_texas_coverage_markdown(report: TexasCoverageReport | None = None) -> str:
    report = report or build_texas_coverage_report()
    lines = [
        "# Texas TEKS Coverage Matrix, Grades 1-7",
        "",
        f"Source: {TEA_MATH_TEKS_URL}",
        f"Elementary source PDF: {ELEMENTARY_TEKS_URL}",
        f"Middle-school source PDF: {MIDDLE_SCHOOL_TEKS_URL}",
        "",
        "## Summary",
        "",
        f"- Non-stretch Grade 1-7 goal rows: {len(report.rows)}",
        f"- Missing curriculum/quiz rows: {len(report.missing_rows)}",
        f"- Weak summer-program rows: {len(report.weak_rows)}",
        f"- Diagnostic-only summer rows: {len(report.diagnostic_only_rows)}",
        "",
        "## Core TEKS Roots",
        "",
        "| Grade | Expected core roots | Quiz-ready roots |",
        "|---:|---|---|",
    ]
    covered = report.covered_roots_by_grade
    for grade, expected in CORE_TEKS_ROOTS.items():
        lines.append(f"| {grade} | {', '.join(expected)} | {', '.join(covered[grade])} |")
    lines.extend(
        [
            "",
            "## Matrix",
            "",
            "| Grade | TEKS | Goal | Curriculum target | Summer units | Quiz/assessment coverage | Status | Notes |",
            "|---:|---|---|---|---|---|---|---|",
        ]
    )
    for row in report.rows:
        lines.append(
            "| "
            f"{row.grade} | "
            f"{_cell(row.teks_display)} | "
            f"{_cell(row.goal_label)} | "
            f"{_cell(row.target_display)} | "
            f"{_cell(_joined(row.summer_units))} | "
            f"{_cell(_joined(row.quiz_surfaces))} | "
            f"{_cell(row.coverage_status)} | "
            f"{_cell(_joined(row.notes))} |"
        )
    return "\n".join(lines) + "\n"


def _summer_unit_map() -> dict[tuple[str, str], tuple[str, ...]]:
    hits: dict[tuple[str, str], list[str]] = {}
    for lane in SUMMER_LANES:
        for unit in lane_units(lane):
            unit_type = "bonus" if unit.optional else "core"
            label = f"{lane_display_name(lane)} {unit_type}: {unit.label}"
            for skill, subskill in summer_unit_targets(unit.code, unit.skill, unit.subskill):
                if subskill is not None:
                    hits.setdefault((skill, subskill), []).append(label)
    return _dedupe_map(hits)


def _assessment_map() -> dict[tuple[str, str], tuple[str, ...]]:
    hits: dict[tuple[str, str], list[str]] = {}
    for strand, skill, subskill in PLACEMENT_BLUEPRINT:
        hits.setdefault((skill, subskill), []).append(f"Summer placement: {strand}")
    for lane in SUMMER_LANES:
        lane_name = lane_display_name(lane)
        for strand, skill, subskill in assessment_blueprint_for_lane(lane):
            hits.setdefault((skill, subskill), []).append(f"{lane_name} midpoint/exit: {strand}")
    return _dedupe_map(hits)


def _quiz_surfaces(goal: TexasGoal, assessment_hits: tuple[str, ...]) -> tuple[str, ...]:
    if not goal.quiz_ready or goal.skill is None:
        return ()
    surfaces = ["Texas grade assessment packet", "manual subskill practice"]
    for subskill in goal.subskills:
        try:
            generate_question(goal.skill, goal.quiz_level, "typed", subskill=subskill)
        except Exception as exc:  # pragma: no cover - surfaced in report text
            surfaces.append(f"generation failure: {subskill}: {exc}")
    surfaces.extend(assessment_hits)
    return tuple(surfaces)


def _status_and_notes(
    goal: TexasGoal,
    unit_hits: tuple[str, ...],
    assessment_hits: tuple[str, ...],
) -> tuple[str, tuple[str, ...]]:
    if not goal.quiz_ready:
        return "missing", ("No quiz-ready curriculum target.",)
    notes: list[str] = []
    if not unit_hits:
        notes.append("No explicit summer unit; covered through school-year goal flow.")
    if not assessment_hits:
        notes.append("No summer placement/midpoint/exit diagnostic item.")
    if unit_hits and assessment_hits:
        return "covered", ("Summer unit and assessment coverage exist.",)
    if assessment_hits:
        return "diagnostic-only", tuple(notes)
    return "weak-summer", tuple(notes)


def _goal_target_keys(goal: TexasGoal) -> tuple[tuple[str, str], ...]:
    if goal.skill is None:
        return ()
    return tuple((goal.skill, subskill) for subskill in goal.subskills)


def _hits_for_keys(
    keys: tuple[tuple[str, str], ...],
    mapping: dict[tuple[str, str], tuple[str, ...]],
) -> tuple[str, ...]:
    hits: list[str] = []
    for key in keys:
        hits.extend(mapping.get(key, ()))
    return _dedupe_tuple(tuple(hits))


def _dedupe_map(raw: dict[tuple[str, str], list[str]]) -> dict[tuple[str, str], tuple[str, ...]]:
    return {key: _dedupe_tuple(tuple(value)) for key, value in raw.items()}


def _dedupe_tuple(values: tuple[str, ...]) -> tuple[str, ...]:
    seen: set[str] = set()
    out: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            out.append(value)
    return tuple(out)


def _root(ref: str) -> str:
    return ref.split()[0].split("-")[0].rstrip("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz")


def _root_sort_key(root: str) -> tuple[int, int]:
    left, right = root.split(".")
    return int(left), int(right)


def _joined(values: tuple[str, ...]) -> str:
    return "<br>".join(values) if values else "none"


def _cell(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ")
