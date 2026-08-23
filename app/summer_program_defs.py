from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
import json

from .skill_graph import subskills_for

TASK_CYCLE: tuple[str, ...] = ("lesson", "practice_a", "practice_b", "mixed_review", "checkpoint")
TASK_KIND_LABELS: dict[str, str] = {
    "lesson": "Lesson",
    "practice_a": "Practice A",
    "practice_b": "Practice B",
    "mixed_review": "Mixed Review",
    "checkpoint": "Checkpoint",
    "remediation_review": "Remediation Review",
    "placement_assessment": "Placement",
    "midpoint_assessment": "Midpoint",
    "exit_assessment": "Exit",
}
TASK_TARGETS: dict[str, float | None] = {
    "lesson": None,
    "practice_a": None,
    "practice_b": None,
    "mixed_review": None,
    "remediation_review": None,
    "checkpoint": 80.0,
    "midpoint_assessment": 80.0,
    "exit_assessment": 85.0,
    "placement_assessment": None,
}


@dataclass(frozen=True)
class SummerUnitDefinition:
    code: str
    label: str
    skill: str
    subskill: str | None
    optional: bool = False


PREALGEBRA_FINISH_LANE = "prealgebra_finish"
FOUNDATION_BRIDGE_LANE = "foundation_bridge"
PLACEMENT_REVIEW_PENDING = "pending_review"
PLACEMENT_REVIEW_ACCEPTED = "accepted"
PLACEMENT_REVIEW_OVERRIDDEN = "overridden"
SUMMER_PROGRAM_LANES: tuple[str, ...] = (
    PREALGEBRA_FINISH_LANE,
    FOUNDATION_BRIDGE_LANE,
)

LANE_LABELS: dict[str, str] = {
    PREALGEBRA_FINISH_LANE: "Pre-Algebra Finish",
    FOUNDATION_BRIDGE_LANE: "Foundation Bridge",
}

LANE_UNITS: dict[str, tuple[SummerUnitDefinition, ...]] = {
    PREALGEBRA_FINISH_LANE: (
        SummerUnitDefinition("integer_fraction_fluency", "Integer and fraction fluency", "pre_algebra", "Integer and fraction fluency"),
        SummerUnitDefinition("order_of_operations", "Order of operations", "pre_algebra", "Order of operations"),
        SummerUnitDefinition("expressions_variables", "Expressions and variables", "pre_algebra", "Expressions and variables"),
        SummerUnitDefinition("one_step_equations", "One-step equations", "pre_algebra", "One-step equations"),
        SummerUnitDefinition(
            "two_step_equations_inequalities",
            "Two-step equations and inequalities",
            "pre_algebra",
            "Two-step equations and inequalities",
        ),
        SummerUnitDefinition(
            "ratios_rates_proportions",
            "Ratios/rates/proportions",
            "pre_algebra",
            "Ratios, rates, and proportional relationships",
        ),
        SummerUnitDefinition("percent_problems", "Percent problems", "pre_algebra", "Percent problems"),
        SummerUnitDefinition(
            "exponents_roots_scientific",
            "Exponents/roots/scientific notation",
            "pre_algebra",
            "Exponents, roots, and scientific notation",
        ),
        SummerUnitDefinition(
            "coordinate_plane_function_tables",
            "Coordinate plane/function tables",
            "pre_algebra",
            "Coordinate plane and function tables",
        ),
        SummerUnitDefinition("mixed_review_exit_prep", "Mixed review + exit prep", "pre_algebra", None),
        SummerUnitDefinition(
            "linear_relationships_preview",
            "Bonus preview: linear relationships",
            "algebra_linear",
            None,
            optional=True,
        ),
        SummerUnitDefinition(
            "functions_patterns_preview",
            "Bonus preview: functions and patterns",
            "algebra_1",
            None,
            optional=True,
        ),
        SummerUnitDefinition(
            "algebra_1_preview_capstone",
            "Bonus preview: Algebra 1 mixed readiness",
            "algebra_1",
            None,
            optional=True,
        ),
        SummerUnitDefinition(
            "geometry_measurement_preview",
            "Bonus preview: geometry and measurement",
            "geometry_area",
            None,
            optional=True,
        ),
        SummerUnitDefinition(
            "coordinate_geometry_preview",
            "Bonus preview: coordinate geometry",
            "geometry_area",
            None,
            optional=True,
        ),
        SummerUnitDefinition(
            "geometry_preview_capstone",
            "Bonus preview: Geometry mixed readiness",
            "geometry_area",
            None,
            optional=True,
        ),
    ),
    FOUNDATION_BRIDGE_LANE: (
        SummerUnitDefinition("place_value", "Place value", "place_value", None),
        SummerUnitDefinition("add_subtract_fluency", "Add/Subtract fluency", "add_subtract", None),
        SummerUnitDefinition("multiply_divide_fluency", "Multiply/Divide fluency", "multiply", None),
        SummerUnitDefinition("fractions_equivalence", "Fractions meaning + equivalence", "fractions", None),
        SummerUnitDefinition("money_measurement", "Money + measurement", "money", None),
        SummerUnitDefinition("ratio_language_patterning", "Ratio language + patterning", "ratios", None),
        SummerUnitDefinition("order_operations_intro", "Order of operations intro", "order_of_operations", None),
    ),
}

MIDPOINT_AFTER_UNIT: dict[str, str] = {
    PREALGEBRA_FINISH_LANE: "two_step_equations_inequalities",
    FOUNDATION_BRIDGE_LANE: "fractions_equivalence",
}

EXIT_AFTER_UNIT: dict[str, str] = {
    PREALGEBRA_FINISH_LANE: "mixed_review_exit_prep",
    FOUNDATION_BRIDGE_LANE: "order_operations_intro",
}

PLACEMENT_STRANDS: tuple[str, ...] = (
    "fractions",
    "integer_order_fluency",
    "variables_equations",
    "ratios_percent",
    "exponents_coordinates",
)

PREALGEBRA_GATE_SUBSKILLS: tuple[str, ...] = (
    "Expressions and variables",
    "One-step equations",
    "Two-step equations and inequalities",
    "Ratios, rates, and proportional relationships",
    "Percent problems",
)

FOUNDATION_PROFICIENT_SKILLS: tuple[str, ...] = ("fractions", "place_value", "order_of_operations")


def lane_units(lane: str) -> tuple[SummerUnitDefinition, ...]:
    return LANE_UNITS.get(lane, ())


def default_minutes_for_lane(lane: str) -> int:
    return 35 if lane == PREALGEBRA_FINISH_LANE else 20


def default_end_date(start_date: date | None = None) -> date:
    base = start_date or date.today()
    return date(base.year, 8, 31)


def task_schedule_dates(start_date: date, count: int, days_per_week: int) -> list[date]:
    days_per_week = max(1, min(7, int(days_per_week)))
    scheduled: list[date] = []
    cursor = start_date
    while len(scheduled) < count:
        day_index = (cursor - start_date).days % 7
        if day_index < days_per_week:
            scheduled.append(cursor)
        cursor += timedelta(days=1)
    return scheduled


def finish_definition_json(lane: str) -> str:
    if lane == PREALGEBRA_FINISH_LANE:
        payload = {
            "requires_all_prealgebra_subskills": "Proficient",
            "gate_subskills": list(PREALGEBRA_GATE_SUBSKILLS),
            "gate_status": "Mastered",
            "checkpoint_score_pct": 80,
            "exit_exam_score_pct": 85,
            "exit_strand_floor_pct": 70,
        }
    else:
        payload = {
            "requires_bridge_subskills": "Developing",
            "proficient_skills": list(FOUNDATION_PROFICIENT_SKILLS),
            "checkpoint_score_pct": 80,
            "exit_exam_score_pct": 80,
        }
    return json.dumps(payload, ensure_ascii=True, sort_keys=True)


def bridge_skill_set() -> tuple[str, ...]:
    return (
        "place_value",
        "add_subtract",
        "multiply",
        "divide",
        "fractions",
        "money",
        "measurement",
        "ratios",
        "order_of_operations",
    )


def lane_required_subskills(lane: str) -> dict[str, tuple[str, ...]]:
    if lane == PREALGEBRA_FINISH_LANE:
        return {"pre_algebra": subskills_for("pre_algebra")}
    required: dict[str, tuple[str, ...]] = {}
    for skill in bridge_skill_set():
        required[skill] = subskills_for(skill)
    return required


def lane_display_name(lane: str) -> str:
    return LANE_LABELS.get(lane, lane.replace("_", " ").title())


def unit_label(lane: str, unit_code: str) -> str:
    for unit in lane_units(lane):
        if unit.code == unit_code:
            return unit.label
    return unit_code.replace("_", " ").title()


def optional_unit_codes(lane: str) -> tuple[str, ...]:
    return tuple(unit.code for unit in lane_units(lane) if unit.optional)


def is_optional_unit(lane: str, unit_code: str) -> bool:
    return unit_code in optional_unit_codes(lane)


def task_kind_label(task_kind: str) -> str:
    return TASK_KIND_LABELS.get(task_kind, task_kind.replace("_", " ").title())
