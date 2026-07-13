from __future__ import annotations

from dataclasses import dataclass

from .calculus_catalog import CALCULUS_1_SUBSKILLS, CALCULUS_2_SUBSKILLS, CALCULUS_3_SUBSKILLS
from .data_analysis import DATA_ANALYSIS_SUBSKILLS
from .early_math_catalog import EARLY_MATH_SKILLS, early_math_subskills_by_skill
from .financial_literacy import FINANCIAL_LITERACY_SUBSKILLS
from .quiz_engine import SKILLS
from .statistics_catalog import STATISTICS_SUBSKILLS


SKILL_LABELS = {
    "counting": "🖐 Counting",
    "place_value": "📊 Place Value",
    "add_subtract": "➕ Add/Subtract",
    "multiply": "✖️ Multiply",
    "divide": "➗ Divide",
    "ratios": "🔗 Ratios",
    "fractions": "🍰 Fractions",
    "long_addition": "📝 Long Addition",
    "long_subtraction": "➖ Long Subtraction",
    "long_multiplication": "✖️ Long Mult",
    "long_division": "➗ Long Div",
    "money": "💵 Money",
    "financial_literacy": "💵 Financial Literacy",
    "measurement": "📏 Measurement",
    "geometry_shapes": "🔷 Shapes",
    "data_displays": "📊 Data Displays",
    "data_analysis": "📊 Data Analysis",
    "integers": "❄️ Integers",
    "order_of_operations": "⚙️ Order of Ops",
    "algebra_linear": "📈 Linear Eq",
    "geometry_area": "📐 Geometry",
    "trig_right_triangle": "📐 Precalc & Trig",
    "stats_percent": "💯 Percent",
    "stats_mean": "📉 Mean",
    "stats_probability": "🎲 Probability",
    "calculus_1": "∫ Calculus I",
    "calculus_2": "∫ Calculus II",
    "calculus_3": "∇ Calculus III",
    "calculus_slope": "📈 Calculus I",
    "pre_algebra": "🧱 Pre-Algebra",
    "algebra_1": "𝑥 Algebra 1",
    "algebra_2": "𝑦 Algebra 2",
    "statistics": "📊 Statistics",
    "sat_math": "📝 SAT Math",
    "psat_math": "📝 PSAT Math",
    "gre_quant": "📝 GRE Quant",
    "mixed": "🔀 Mixed Review",
}

SKILL_ORDER = list(SKILLS)

ARITHMETIC_SKILLS: tuple[str, ...] = (
    "counting",
    "place_value",
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
    "measurement",
    "geometry_shapes",
    "data_displays",
    "integers",
    "order_of_operations",
    "pre_algebra",
    "algebra_linear",
    "algebra_1",
    "algebra_2",
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
        "place_value",
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
        "measurement",
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
        "geometry_shapes",
        "geometry_area",
        "trig_right_triangle",
    ),
    "Pre-Calculus & Trig": (
        "trig_right_triangle",
    ),
    "Statistics / Probability": (
        "data_displays",
        "data_analysis",
        "stats_percent",
        "stats_mean",
        "stats_probability",
        "statistics",
        "financial_literacy",
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
    "place_value": (("counting", PREREQ_REQUIRED, 1.0),),
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
    "financial_literacy": (
        ("add_subtract", PREREQ_REQUIRED, 1.0),
        ("stats_percent", PREREQ_HELPFUL, 0.55),
    ),
    "measurement": (("add_subtract", PREREQ_REQUIRED, 1.0), ("multiply", PREREQ_HELPFUL, 0.5)),
    "geometry_shapes": (("counting", PREREQ_REQUIRED, 1.0),),
    "data_displays": (("counting", PREREQ_REQUIRED, 1.0), ("add_subtract", PREREQ_HELPFUL, 0.5)),
    "data_analysis": (("data_displays", PREREQ_REQUIRED, 1.0),),
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

EARLY_MATH_SUBSKILLS = early_math_subskills_by_skill()

SKILL_SUBSKILLS: dict[str, tuple[str, ...]] = {
    **{skill: EARLY_MATH_SUBSKILLS[skill] for skill in EARLY_MATH_SKILLS},
    "algebra_linear": (
        "One-step equations",
        "Two-step equations",
        "Variables on both sides",
        "Distributive property equations",
        "Fraction and decimal equations",
        "Linear inequalities",
        "Slope from points",
        "Slope-intercept interpretation",
        "Systems of linear equations",
        "Direct variation",
        "Rate and unit-rate modeling",
        "Word problems with linear models",
    ),
    "geometry_area": (
        "Area of rectangles and squares",
        "Area of triangles and parallelograms",
        "Area of trapezoids and composite figures",
        "Perimeter and missing sides",
        "Circumference and area of circles",
        "Surface area and volume",
        "Pythagorean theorem",
        "Coordinate geometry distance and midpoint",
        "Angles in lines and triangles",
        "Triangle congruence criteria",
        "Transformations and congruence",
        "Similarity and scale factor",
        "Analytic geometry and coordinate proofs",
    ),
    "trig_right_triangle": (
        "Right-triangle trig ratios",
        "Unit circle trig values",
        "Trig functions and graphs",
        "Trig identities",
        "Inverse trig",
        "Vectors",
        "Matrices and linear transformations",
        "Polar coordinates",
    ),
    "stats_percent": (
        "Percent change",
        "Reverse percent change",
        "Percent word problems",
    ),
    "stats_mean": (
        "Mean",
        "Mean from display",
    ),
    "stats_probability": (
        "Probability models",
    ),
    "financial_literacy": FINANCIAL_LITERACY_SUBSKILLS,
    "data_analysis": DATA_ANALYSIS_SUBSKILLS,
    "calculus_slope": (
        "Average rate of change between two points",
    ),
    "algebra_1": (
        "Algebra foundations",
        "Solving equations & inequalities",
        "Working with units",
        "Linear equations & graphs",
        "Forms of linear equations",
        "Slope from points",
        "Slope-intercept form",
        "Graphing linear inequalities",
        "Systems of equations",
        "Systems by substitution",
        "Systems by elimination",
        "Graphing systems and intersections",
        "Inequalities (systems & graphs)",
        "Functions",
        "Sequences",
        "Absolute value & piecewise functions",
        "Function transformations",
        "Exponents & radicals",
        "Radicals and rational exponents",
        "Exponential growth & decay",
        "Polynomial arithmetic",
        "Factoring basics",
        "Quadratics: Multiplying & factoring",
        "Quadratic factoring by grouping",
        "Difference of squares",
        "Quadratic functions & equations",
        "Completing the square",
        "Quadratic formula",
        "Irrational numbers",
    ),
    "algebra_2": (
        "Polynomial arithmetic",
        "Complex numbers",
        "Polynomial factorization",
        "Polynomial division",
        "Polynomial graphs",
        "Domain and range",
        "Inverse and composition",
        "Rational exponents and radicals",
        "Exponential models",
        "Logarithms",
        "Transformations of functions",
        "Equations",
        "Trigonometry",
        "Modeling",
        "Rational expressions",
        "Rational functions",
        "Sequences and series",
    ),
    "statistics": STATISTICS_SUBSKILLS,
    "sat_math": (
        "SAT algebra modeling",
        "SAT linear relationships",
        "SAT percent and data",
        "SAT statistics",
        "SAT mixed-domain",
    ),
    "psat_math": (
        "PSAT algebra modeling",
        "PSAT equation solving",
        "PSAT geometry",
        "PSAT percentages",
        "PSAT mixed-domain",
    ),
    "gre_quant": (
        "GRE quantitative comparison",
        "GRE ratios and proportions",
        "GRE percent reasoning",
        "GRE data interpretation",
    ),
    "calculus_1": CALCULUS_1_SUBSKILLS,
    "calculus_2": CALCULUS_2_SUBSKILLS,
    "calculus_3": CALCULUS_3_SUBSKILLS,
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
