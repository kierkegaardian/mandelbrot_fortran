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
    "calculus_1": "Calculus I",
    "calculus_2": "Calculus II",
    "calculus_3": "Calculus III",
    "calculus_slope": "Calculus I (Legacy)",
    "pre_algebra": "Pre-Algebra Foundations",
    "algebra_1": "Algebra 1",
    "algebra_2": "Algebra 2",
    "statistics": "Statistics",
    "sat_math": "SAT Math Focus",
    "psat_math": "PSAT Math Focus",
    "gre_quant": "GRE Quant Focus",
    "mixed": "Mixed Review",
}

SKILL_ORDER = list(SKILLS)

ARITHMETIC_SKILLS: tuple[str, ...] = (
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
    "integers",
    "order_of_operations",
    "algebra_linear",
    "geometry_area",
    "trig_right_triangle",
    "stats_percent",
    "stats_mean",
    "stats_probability",
    "calculus_1",
)

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
        "pre_algebra",
    ),
    "Algebra": (
        "algebra_linear",
        "algebra_1",
        "algebra_2",
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
        "statistics",
    ),
    "Calculus": (
        "calculus_1",
        "calculus_2",
        "calculus_3",
    ),
    "Test Prep": (
        "sat_math",
        "psat_math",
        "gre_quant",
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
    "Test Prep",
]

PREREQ_REQUIRED = "required_for_readiness"
PREREQ_HELPFUL = "helpful_background"

SKILL_PREREQUISITE_EDGES: dict[str, tuple[tuple[str, str, float], ...]] = {
    "counting": (),
    "add_subtract": (("counting", PREREQ_REQUIRED, 1.0),),
    "multiply": (("add_subtract", PREREQ_REQUIRED, 1.0),),
    "divide": (("add_subtract", PREREQ_REQUIRED, 1.0),),
    "ratios": (("divide", PREREQ_REQUIRED, 1.0), ("fractions", PREREQ_HELPFUL, 0.55)),
    "fractions": (("add_subtract", PREREQ_REQUIRED, 1.0), ("divide", PREREQ_REQUIRED, 1.0)),
    "long_addition": (("add_subtract", PREREQ_REQUIRED, 1.0),),
    "long_subtraction": (("add_subtract", PREREQ_REQUIRED, 1.0),),
    "long_multiplication": (("multiply", PREREQ_REQUIRED, 1.0),),
    "long_division": (("divide", PREREQ_REQUIRED, 1.0), ("long_subtraction", PREREQ_HELPFUL, 0.6)),
    "money": (("add_subtract", PREREQ_REQUIRED, 1.0),),
    "integers": (("add_subtract", PREREQ_REQUIRED, 1.0),),
    "order_of_operations": (("integers", PREREQ_REQUIRED, 1.0), ("multiply", PREREQ_HELPFUL, 0.6)),
    "algebra_linear": (("order_of_operations", PREREQ_REQUIRED, 1.0), ("integers", PREREQ_HELPFUL, 0.6)),
    "geometry_area": (("long_multiplication", PREREQ_REQUIRED, 1.0), ("fractions", PREREQ_HELPFUL, 0.5)),
    "trig_right_triangle": (("geometry_area", PREREQ_REQUIRED, 1.0), ("algebra_linear", PREREQ_HELPFUL, 0.45)),
    "stats_percent": (
        ("multiply", PREREQ_REQUIRED, 1.0),
        ("divide", PREREQ_REQUIRED, 1.0),
        ("fractions", PREREQ_HELPFUL, 0.7),
    ),
    "stats_mean": (("stats_percent", PREREQ_REQUIRED, 1.0),),
    "stats_probability": (("stats_percent", PREREQ_REQUIRED, 1.0), ("stats_mean", PREREQ_HELPFUL, 0.6)),
    "pre_algebra": (
        ("integers", PREREQ_REQUIRED, 1.0),
        ("order_of_operations", PREREQ_REQUIRED, 1.0),
        ("fractions", PREREQ_HELPFUL, 0.6),
    ),
    "algebra_1": (
        ("pre_algebra", PREREQ_REQUIRED, 1.0),
        ("algebra_linear", PREREQ_HELPFUL, 0.7),
    ),
    "algebra_2": (
        ("algebra_1", PREREQ_REQUIRED, 1.0),
        ("algebra_linear", PREREQ_HELPFUL, 0.65),
        ("geometry_area", PREREQ_HELPFUL, 0.4),
    ),
    "calculus_1": (
        ("algebra_2", PREREQ_REQUIRED, 1.0),
        ("trig_right_triangle", PREREQ_HELPFUL, 0.5),
        ("statistics", PREREQ_HELPFUL, 0.3),
    ),
    "calculus_2": (
        ("calculus_1", PREREQ_REQUIRED, 1.0),
        ("algebra_2", PREREQ_HELPFUL, 0.5),
    ),
    "calculus_3": (
        ("calculus_2", PREREQ_REQUIRED, 1.0),
        ("trig_right_triangle", PREREQ_HELPFUL, 0.55),
    ),
    "statistics": (
        ("stats_percent", PREREQ_REQUIRED, 1.0),
        ("stats_mean", PREREQ_REQUIRED, 1.0),
        ("stats_probability", PREREQ_HELPFUL, 0.7),
    ),
    "sat_math": (
        ("algebra_1", PREREQ_REQUIRED, 1.0),
        ("algebra_2", PREREQ_REQUIRED, 1.0),
        ("geometry_area", PREREQ_REQUIRED, 1.0),
        ("statistics", PREREQ_REQUIRED, 1.0),
    ),
    "psat_math": (
        ("algebra_1", PREREQ_REQUIRED, 1.0),
        ("geometry_area", PREREQ_REQUIRED, 1.0),
        ("statistics", PREREQ_REQUIRED, 1.0),
    ),
    "gre_quant": (
        ("algebra_2", PREREQ_REQUIRED, 1.0),
        ("statistics", PREREQ_REQUIRED, 1.0),
        ("geometry_area", PREREQ_HELPFUL, 0.6),
        ("ratios", PREREQ_HELPFUL, 0.45),
    ),
}

SKILL_PREREQUISITE_WEIGHTS: dict[str, tuple[tuple[str, float], ...]] = {
    skill: tuple((edge[0], float(edge[2])) for edge in edges) for skill, edges in SKILL_PREREQUISITE_EDGES.items()
}

SKILL_PREREQUISITES: dict[str, tuple[str, ...]] = {
    skill: tuple(edge[0] for edge in edges) for skill, edges in SKILL_PREREQUISITE_EDGES.items()
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
        "Average rate of change between points",
        "Slope from graph/table/equation",
        "Tangent slope as derivative at a point",
        "Estimating derivative from nearby values",
        "Derivative sign and behavior (increasing/decreasing)",
        "Linear approximation from tangent line",
    ),
    "pre_algebra": (
        "Integer and fraction fluency",
        "Order of operations",
        "Ratios and rates",
    ),
    "algebra_1": (
        "Linear equations and inequalities",
        "Slope/intercept interpretation",
        "Modeling with equations",
    ),
    "algebra_2": (
        "Factor quadratics (including common factors)",
        "Solve quadratics by factoring",
        "Solve quadratics with the quadratic formula",
        "Complete the square and vertex form",
        "Polynomial operations and structure",
        "Exponential growth/decay models",
        "Logarithmic functions and graph transformations",
        "Function transformations and composition",
    ),
    "statistics": (
        "Percent and proportion analysis",
        "Mean/center interpretation",
        "Probability model setup",
    ),
    "sat_math": (
        "Problem translation under time pressure",
        "Multi-step mixed-domain solving",
        "Answer checking and elimination",
    ),
    "psat_math": (
        "Algebra and geometry fundamentals",
        "Word-to-equation translation",
        "Calculator and no-calculator discipline",
    ),
    "gre_quant": (
        "Quantitative comparison logic",
        "Algebra + arithmetic integration",
        "Data/probability interpretation",
    ),
    "calculus_1": (
        "Limits and continuity intuition",
        "Average vs instantaneous rate of change",
        "Derivative rules and notation",
        "Derivative from graphs and tables",
        "Applications of derivatives (optimization and related rates)",
        "Basic antiderivatives and accumulation",
    ),
    "calculus_2": (
        "Definite integral as signed area",
        "Substitution and integration by parts",
        "Area between curves and volume setup",
        "Differential equations (separable first-order)",
        "Sequences and infinite series basics",
        "Convergence tests and power series intuition",
    ),
    "calculus_3": (
        "Vectors in 2D/3D and geometric meaning",
        "Partial derivatives and gradients",
        "Chain rule in multivariable settings",
        "Double and triple integral setup",
        "Coordinate changes (polar/cylindrical/spherical)",
        "Vector fields and flux/circulation concepts",
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
