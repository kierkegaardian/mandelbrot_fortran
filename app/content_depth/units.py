from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CumulativeMix:
    current: int
    earlier: int
    application: int


@dataclass(frozen=True)
class CumulativeCheck:
    code: str
    label: str
    target_codes: tuple[str, ...]
    question_count: int
    pass_score_pct: float = 80.0


@dataclass(frozen=True)
class AlgebraUnit:
    code: str
    label: str
    subskills: tuple[str, ...]


@dataclass(frozen=True)
class CompanionUnit:
    code: str
    label: str
    skill: str
    subskills: tuple[str, ...]


def cumulative_mix(question_count: int) -> CumulativeMix:
    total = max(1, int(question_count))
    current = int(total * 0.5 + 0.5)
    application = int(total * 0.2 + 0.5)
    earlier = total - current - application
    return CumulativeMix(current, earlier, application)


def texas_question_count(grade: int) -> int:
    if grade <= 2:
        return 8
    if grade <= 5:
        return 10
    return 12


def texas_cumulative_checks(grade: int) -> tuple[CumulativeCheck, ...]:
    from ..texas_grade_goals import texas_grade_plan

    goals = tuple(goal for goal in texas_grade_plan(grade).goals if not goal.stretch)
    checks: list[CumulativeCheck] = []
    for end in range(2, len(goals) + 1, 2):
        checks.append(_texas_check(grade, goals[:end], len(checks) + 1))
    if len(goals) % 2:
        checks.append(_texas_check(grade, goals, len(checks) + 1))
    return tuple(checks)


def texas_companion_units(grade: int) -> tuple[CompanionUnit, ...]:
    from ..texas_grade_goals import texas_grade_plan

    return tuple(
        CompanionUnit(goal.code, goal.label, str(goal.skill), goal.subskills)
        for goal in texas_grade_plan(grade).goals
        if not goal.stretch and goal.skill is not None
    )


def _texas_check(grade: int, goals: tuple[object, ...], number: int) -> CumulativeCheck:
    codes = tuple(str(getattr(goal, "code")) for goal in goals)
    return CumulativeCheck(
        code=f"texas_g{grade}_cumulative_{number}",
        label=f"Grade {grade} Cumulative Check {number}",
        target_codes=codes,
        question_count=texas_question_count(grade),
    )


ALGEBRA_1_UNITS: tuple[AlgebraUnit, ...] = (
    AlgebraUnit("a1_foundations", "Foundations and equation solving", (
        "Algebra foundations", "Solving equations & inequalities", "Working with units",
    )),
    AlgebraUnit("a1_linear", "Linear equations, forms, slope, and graphing", (
        "Linear equations & graphs", "Forms of linear equations", "Slope from points",
        "Slope-intercept form", "Graphing linear inequalities",
    )),
    AlgebraUnit("a1_systems", "Systems and systems of inequalities", (
        "Systems of equations", "Systems by substitution", "Systems by elimination",
        "Graphing systems and intersections", "Inequalities (systems & graphs)",
    )),
    AlgebraUnit("a1_functions", "Functions, sequences, absolute value, and transformations", (
        "Functions", "Sequences", "Absolute value & piecewise functions", "Function transformations",
    )),
    AlgebraUnit("a1_exponents", "Exponents, radicals, growth, and irrational numbers", (
        "Exponents & radicals", "Radicals and rational exponents", "Exponential growth & decay",
        "Irrational numbers",
    )),
    AlgebraUnit("a1_polynomials", "Polynomial arithmetic and factoring", (
        "Polynomial arithmetic", "Factoring basics", "Quadratics: Multiplying & factoring",
        "Quadratic factoring by grouping", "Difference of squares",
    )),
    AlgebraUnit("a1_quadratics", "Quadratic functions and solution methods", (
        "Quadratic functions & equations", "Completing the square", "Quadratic formula",
    )),
)
