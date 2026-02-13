from __future__ import annotations

from dataclasses import dataclass

from .quiz_engine import SKILLS


SKILL_LABELS = {
    "counting": "Counting",
    "add_subtract": "Add/Subtract",
    "multiply": "Multiply",
    "divide": "Divide",
    "ratios": "Ratios",
    "fractions": "Fractions",
    "long_addition": "Long Addition",
    "long_subtraction": "Long Subtraction",
    "long_multiplication": "Long Multiplication",
    "long_division": "Long Division",
    "money": "Money",
    "integers": "Integers",
    "order_of_operations": "Order of Operations",
    "algebra_linear": "Linear Equations",
    "geometry_area": "Area/Geometry",
    "trig_right_triangle": "Right-Triangle Trig",
    "stats_percent": "Percent",
    "stats_mean": "Mean",
    "stats_probability": "Probability",
    "calculus_slope": "Slope",
    "mixed": "Mixed Review",
}

SKILL_ORDER = list(SKILLS)

SKILL_TRACKS: dict[str, tuple[str, ...]] = {
    "Arithmetic": (
        "counting",
        "add_subtract",
        "multiply",
        "divide",
        "ratios",
        "fractions",
        "long_addition",
        "long_subtraction",
        "long_multiplication",
        "long_division",
        "money",
    ),
    "Pre-Algebra": (
        "integers",
        "order_of_operations",
    ),
    "Algebra": (
        "algebra_linear",
    ),
    "Geometry": (
        "geometry_area",
    ),
    "Pre-Calculus & Trig": (
        "trig_right_triangle",
    ),
    "Statistics / Probability": (
        "stats_percent",
        "stats_mean",
        "stats_probability",
    ),
    "Calculus": (
        "calculus_slope",
    ),
}

SKILL_TRACK_ORDER = [
    "Arithmetic",
    "Pre-Algebra",
    "Algebra",
    "Geometry",
    "Pre-Calculus & Trig",
    "Statistics / Probability",
    "Calculus",
]

SKILL_PREREQUISITES: dict[str, tuple[str, ...]] = {
    "counting": (),
    "add_subtract": ("counting",),
    "multiply": ("add_subtract",),
    "divide": ("add_subtract",),
    "ratios": ("divide",),
    "fractions": ("add_subtract", "divide"),
    "long_addition": ("add_subtract",),
    "long_subtraction": ("add_subtract",),
    "long_multiplication": ("multiply",),
    "long_division": ("divide",),
    "money": ("add_subtract",),
    "integers": ("add_subtract",),
    "order_of_operations": ("integers",),
    "algebra_linear": ("order_of_operations",),
    "geometry_area": ("long_multiplication",),
    "trig_right_triangle": ("geometry_area",),
    "stats_percent": ("multiply", "divide"),
    "stats_mean": ("stats_percent",),
    "stats_probability": ("stats_percent", "stats_mean"),
    "calculus_slope": ("order_of_operations", "algebra_linear"),
}

SKILL_SUBSKILLS: dict[str, tuple[str, ...]] = {
    "counting": (
        "Number recognition",
        "Skip-counting",
        "Count-to-number matching",
    ),
    "add_subtract": (
        "Single-digit addition",
        "Single-digit subtraction",
        "Borrowing and carrying basics",
        "Word problems",
    ),
    "multiply": (
        "Repeated addition",
        "Times tables",
        "Array and grid models",
        "Simple product facts",
    ),
    "divide": (
        "Equal sharing",
        "Division as repeated subtraction",
        "Remainders",
        "Inverse thinking",
    ),
    "ratios": (
        "Ratio language (to:of)",
        "Equivalent ratios",
        "Fractional comparison",
    ),
    "fractions": (
        "Unit fractions",
        "Equivalent fractions",
        "Shaded region meaning",
        "Fraction to decimal",
    ),
    "long_addition": (
        "Column alignment",
        "Carry handling",
        "Multi-digit accuracy",
        "Place-value structure",
    ),
    "long_subtraction": (
        "Borrowing",
        "Column alignment",
        "Crossing zero safely",
    ),
    "long_multiplication": (
        "Partial products",
        "Place-value breakdown",
        "Two-digit multiplies",
    ),
    "long_division": (
        "Division layout",
        "Quotient estimation",
        "Remainder handling",
    ),
    "money": (
        "Dollar-coin values",
        "Making change",
        "Budget-style totals",
        "Place-value in currency",
    ),
    "integers": (
        "Signed numbers",
        "Negative arithmetic",
        "Order-dependent operations",
    ),
    "order_of_operations": (
        "Parentheses first",
        "Multiplication vs addition/subtraction",
        "Expression grouping",
    ),
    "algebra_linear": (
        "Isolating variable terms",
        "Inverse operations",
        "One-step equations",
        "Two-step equations",
    ),
    "geometry_area": (
        "Unit-square interpretation",
        "Rectangle area",
        "Square properties",
        "Triangle area logic",
    ),
    "trig_right_triangle": (
        "Opposite/adjacent/hypotenuse labels",
        "sin cos tan setup",
        "Right-triangle ratio setup",
    ),
    "stats_percent": (
        "Percent of a whole",
        "Percent conversion",
        "Decimal and percent link",
    ),
    "stats_mean": (
        "Summing values",
        "Divide by count",
        "Simple average checks",
    ),
    "stats_probability": (
        "Outcome counts",
        "Favorable vs total",
        "Fraction and decimal reduction",
    ),
    "calculus_slope": (
        "Rise over run",
        "Point-to-point comparison",
        "Positive vs negative slope",
    ),
}


@dataclass(frozen=True)
class SkillNode:
    skill: str
    prerequisites: tuple[str, ...]
    subskills: tuple[str, ...]


SKILL_GRAPH: dict[str, SkillNode] = {
    skill: SkillNode(
        skill,
        SKILL_PREREQUISITES.get(skill, ()),
        SKILL_SUBSKILLS.get(skill, ()),
    )
    for skill in SKILL_ORDER
}

SUBSKILL_STREAK_TO_MASTER = 3


MASTERED_STATUSES = {"Proficient", "Mastered"}

MASTERY_PRIORITY = {
    "Needs work": 0,
    "Developing": 1,
    "Proficient": 2,
    "Mastered": 3,
    "Not started": 4,
}


def is_mastered(status: str | None) -> bool:
    return status in MASTERED_STATUSES


def prerequisites_for(skill: str) -> tuple[str, ...]:
    return SKILL_GRAPH.get(skill, SkillNode(skill, (), ())).prerequisites


def subskills_for(skill: str) -> tuple[str, ...]:
    return SKILL_GRAPH.get(skill, SkillNode(skill, (), ())).subskills


def track_names() -> tuple[str, ...]:
    return tuple(SKILL_TRACK_ORDER)


def skills_in_track(track: str) -> tuple[str, ...]:
    if track == "All":
        return tuple(SKILL_ORDER)
    return SKILL_TRACKS.get(track, tuple())


def recommend_next_skills(mastery_map: dict[str, str], limit: int = 3) -> list[str]:
    limit = max(1, int(limit))
    mastered = {skill for skill in SKILL_ORDER if is_mastered(mastery_map.get(skill))}
    if not mastery_map:
        # New user: begin with the first few skills in canonical order.
        return SKILL_ORDER[:limit]

    ready = [skill for skill in SKILL_ORDER if skill not in mastered and _prerequisites_met(skill, mastered)]
    if not ready:
        # If no node has all dependencies unlocked, fall back to any unmastered skill
        # in canonical order to avoid blocking progress indefinitely.
        ready = [skill for skill in SKILL_ORDER if skill not in mastered]

    ready.sort(key=lambda s: (_status_priority(s, mastery_map), SKILL_ORDER.index(s)))
    return ready[:limit]


def _prerequisites_met(skill: str, mastered: set[str]) -> bool:
    for prerequisite in prerequisites_for(skill):
        if prerequisite not in mastered:
            return False
    return True


def _status_priority(skill: str, mastery_map: dict[str, str]) -> int:
    return MASTERY_PRIORITY.get(mastery_map.get(skill, "Not started"), 4)
