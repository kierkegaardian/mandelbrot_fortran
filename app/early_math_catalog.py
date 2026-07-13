from __future__ import annotations

from dataclasses import dataclass

from .early_math_intuition import IntuitionPack, intuition_for as _intuition_for


EARLY_MATH_SKILLS: tuple[str, ...] = (
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
)


@dataclass(frozen=True)
class EarlyMathSpec:
    skill: str
    subskill: str
    khan_query: str
    khan_assignable_url: str
    required_modes: tuple[str, ...]
    source_ids: tuple[str, ...]
    intuition: IntuitionPack


EARLY_MATH_SKILL_URLS: dict[str, str] = {
    "counting": "https://www.khanacademy.org/math/cc-kindergarten-math/cc-kindergarten-counting-and-cardinality",
    "place_value": "https://www.khanacademy.org/math/cc-fourth-grade-math/imp-place-value-and-rounding-2",
    "add_subtract": "https://www.khanacademy.org/math/cc-third-grade-math/imp-addition-and-subtraction",
    "multiply": "https://www.khanacademy.org/math/cc-fourth-grade-math/imp-multiplication-and-division-2",
    "divide": "https://www.khanacademy.org/math/cc-fourth-grade-math/division",
    "ratios": "https://www.khanacademy.org/math/cc-sixth-grade-math/cc-6th-ratios-prop-topic",
    "fractions": "https://www.khanacademy.org/math/cc-fourth-grade-math/comparing-fractions-and-equivalent-fractions",
    "long_addition": "https://www.khanacademy.org/math/arithmetic-home/arith-review-add-subtract",
    "long_subtraction": "https://www.khanacademy.org/math/arithmetic-home/arith-review-add-subtract",
    "long_multiplication": "https://www.khanacademy.org/math/arithmetic-home/arith-review-multiply-divide",
    "long_division": "https://www.khanacademy.org/math/arithmetic-home/arith-review-multiply-divide",
    "money": "https://www.khanacademy.org/math/cc-fourth-grade-math/imp-measurement-and-data-2/imp-money-word-problems",
    "measurement": "https://www.khanacademy.org/math/cc-fourth-grade-math/imp-measurement-and-data-2",
    "geometry_shapes": "https://www.khanacademy.org/math/cc-1st-grade-math/cc-1st-measurement-geometry",
    "data_displays": "https://www.khanacademy.org/math/cc-2nd-grade-math/x3184e0ec:data",
    "integers": "https://www.khanacademy.org/math/cc-sixth-grade-math/cc-6th-negative-number-topic",
    "order_of_operations": "https://www.khanacademy.org/math/cc-sixth-grade-math/x0267d782:cc-6th-exponents-and-order-of-operations",
    "pre_algebra": "https://www.khanacademy.org/math/pre-algebra",
}


_DEFAULT_SOURCES: dict[str, tuple[str, ...]] = {
    "counting": ("basic_arithmetic_student_workbook_2013",),
    "place_value": ("basic_arithmetic_student_workbook_2013",),
    "add_subtract": ("basic_arithmetic_student_workbook_2013", "ray_new_practical_arithmetic_1897"),
    "multiply": ("basic_arithmetic_student_workbook_2013", "ray_new_practical_arithmetic_1897"),
    "divide": ("basic_arithmetic_student_workbook_2013", "ray_new_practical_arithmetic_1897"),
    "ratios": ("ray_new_practical_arithmetic_1897", "elementary_algebra_openstax_2e"),
    "fractions": ("ray_new_practical_arithmetic_1897", "basic_arithmetic_student_workbook_2013"),
    "long_addition": ("basic_arithmetic_student_workbook_2013",),
    "long_subtraction": ("basic_arithmetic_student_workbook_2013",),
    "long_multiplication": ("basic_arithmetic_student_workbook_2013",),
    "long_division": ("basic_arithmetic_student_workbook_2013",),
    "money": ("ray_new_practical_arithmetic_1897", "basic_arithmetic_student_workbook_2013"),
    "measurement": ("ray_new_practical_arithmetic_1897", "school_geometry_1921_hs21"),
    "geometry_shapes": ("school_geometry_1921_hs21",),
    "data_displays": ("basic_arithmetic_student_workbook_2013",),
    "integers": ("elementary_algebra_openstax_2e",),
    "order_of_operations": ("elementary_algebra_openstax_2e",),
    "pre_algebra": ("elementary_algebra_openstax_2e", "ray_new_practical_arithmetic_1897"),
}


def _query(skill: str, subskill: str) -> str:
    base = skill.replace("_", " ")
    return f"{base} {subskill}".lower()


def _spec(
    skill: str,
    subskill: str,
    khan_assignable_url: str,
    *,
    required_modes: tuple[str, ...] = ("expression",),
    source_ids: tuple[str, ...] | None = None,
    khan_query: str | None = None,
) -> EarlyMathSpec:
    intuition = _intuition_for(skill, subskill)
    if intuition is None:
        raise KeyError(f"Missing intuition for {skill} / {subskill}")
    return EarlyMathSpec(
        skill=skill,
        subskill=subskill,
        khan_query=khan_query or _query(skill, subskill),
        khan_assignable_url=khan_assignable_url,
        required_modes=required_modes,
        source_ids=source_ids or _DEFAULT_SOURCES[skill],
        intuition=intuition,
    )


_EARLY_MATH_SPECS: tuple[EarlyMathSpec, ...] = (
    _spec("counting", "Number recognition", EARLY_MATH_SKILL_URLS["counting"]),
    _spec("counting", "Skip-counting", "https://www.khanacademy.org/math/cc-2nd-grade-math/cc-2nd-place-value/cc-2nd-skip-counting/e/skip-counting-by-100s"),
    _spec("counting", "Count-to-number matching", EARLY_MATH_SKILL_URLS["counting"]),
    _spec("place_value", "Ones, tens, and hundreds identification", "https://www.khanacademy.org/math/cc-fourth-grade-math/imp-place-value-and-rounding-2/imp-intro-to-place-value/e/place-value-blocks"),
    _spec("place_value", "Expanded form", "https://www.khanacademy.org/math/cc-2nd-grade-math/cc-2nd-place-value/x3184e0ec:numbers-in-standard-word-and-expanded-form/e/writing-numbers-to-1000"),
    _spec("place_value", "Compare numbers by place value", EARLY_MATH_SKILL_URLS["place_value"]),
    _spec("place_value", "Decimal place value and comparison", "https://www.khanacademy.org/math/cc-fourth-grade-math/imp-decimals/imp-decimals-greater-than-one/e/decimals-greater-than-one-intuition"),
    _spec("add_subtract", "Single-digit addition", "https://www.khanacademy.org/math/cc-2nd-grade-math/x3184e0ec:add-and-subtract-within-20/x3184e0ec:add-within-20/e/addition_2"),
    _spec("add_subtract", "Single-digit subtraction", EARLY_MATH_SKILL_URLS["add_subtract"]),
    _spec("add_subtract", "Borrowing and carrying basics", "https://www.khanacademy.org/math/cc-fourth-grade-math/imp-add-sub-multi-digit"),
    _spec("add_subtract", "Word problems", "https://www.khanacademy.org/math/cc-third-grade-math/imp-addition-and-subtraction/addition-and-subtraction-word-problems/e/add-and-subtract-within-1000-word-problems", required_modes=("expression", "word")),
    _spec("add_subtract", "Missing addends", EARLY_MATH_SKILL_URLS["add_subtract"]),
    _spec("add_subtract", "Multi-digit regrouping", "https://www.khanacademy.org/math/cc-fourth-grade-math/imp-add-sub-multi-digit", required_modes=("expression", "word")),
    _spec("multiply", "Repeated addition", EARLY_MATH_SKILL_URLS["multiply"]),
    _spec("multiply", "Times tables", EARLY_MATH_SKILL_URLS["multiply"]),
    _spec("multiply", "Array and grid models", EARLY_MATH_SKILL_URLS["multiply"]),
    _spec("multiply", "Simple product facts", EARLY_MATH_SKILL_URLS["multiply"]),
    _spec("multiply", "Multiplicative comparison and estimation", "https://www.khanacademy.org/math/cc-fourth-grade-math/imp-multiplication-and-division-2/imp-comparing-with-multiplication/e/comparing-with-multiplication", required_modes=("expression", "word")),
    _spec("divide", "Equal sharing", EARLY_MATH_SKILL_URLS["divide"]),
    _spec("divide", "Division as repeated subtraction", EARLY_MATH_SKILL_URLS["divide"]),
    _spec("divide", "Remainders", "https://www.khanacademy.org/math/cc-fourth-grade-math/division/4th-remainders/e/understanding-remainders", required_modes=("expression", "word")),
    _spec("divide", "Inverse thinking", EARLY_MATH_SKILL_URLS["divide"]),
    _spec("divide", "Remainder interpretation and estimation", "https://www.khanacademy.org/math/cc-fourth-grade-math/division/4th-remainders/e/understanding-remainders", required_modes=("expression", "word")),
    _spec("ratios", "Ratio language (to:of)", EARLY_MATH_SKILL_URLS["ratios"], required_modes=("expression", "word")),
    _spec("ratios", "Equivalent ratios", "https://www.khanacademy.org/math/cc-sixth-grade-math/cc-6th-ratios-prop-topic/cc-6th-equivalent-ratios/e/equivalent-ratios", required_modes=("expression", "word")),
    _spec("ratios", "Fractional comparison", EARLY_MATH_SKILL_URLS["ratios"]),
    _spec("ratios", "Unit rates and proportional relationships", "https://www.khanacademy.org/math/cc-seventh-grade-math/cc-7th-ratio-proportion/cc-7th-proportional-rel/e/analyzing-and-identifying-proportional-relationships", required_modes=("expression", "word")),
    _spec("fractions", "Unit fractions", EARLY_MATH_SKILL_URLS["fractions"]),
    _spec("fractions", "Equivalent fractions", "https://www.khanacademy.org/math/cc-fourth-grade-math/comparing-fractions-and-equivalent-fractions/imp-equivalent-fractions-2/e/visualizing-equivalent-fractions"),
    _spec("fractions", "Shaded region meaning", EARLY_MATH_SKILL_URLS["fractions"]),
    _spec("fractions", "Fraction to decimal", "https://www.khanacademy.org/math/cc-seventh-grade-math/cc-7th-fractions-decimals/cc-7th-fracs-to-decimals/e/converting_decimals_to_fractions_2"),
    _spec("fractions", "Compare fractions and mixed numbers", "https://www.khanacademy.org/math/cc-third-grade-math/equivalent-fractions-and-comparing-fractions/imp-comparing-fractions/e/comparing-fractions-with-the-same-numerator-or-denominator"),
    _spec("long_addition", "Column alignment", EARLY_MATH_SKILL_URLS["long_addition"]),
    _spec("long_addition", "Carry handling", EARLY_MATH_SKILL_URLS["long_addition"]),
    _spec("long_addition", "Multi-digit accuracy", EARLY_MATH_SKILL_URLS["long_addition"]),
    _spec("long_addition", "Place-value structure", EARLY_MATH_SKILL_URLS["long_addition"]),
    _spec("long_subtraction", "Borrowing", EARLY_MATH_SKILL_URLS["long_subtraction"]),
    _spec("long_subtraction", "Column alignment", EARLY_MATH_SKILL_URLS["long_subtraction"]),
    _spec("long_subtraction", "Crossing zero safely", EARLY_MATH_SKILL_URLS["long_subtraction"]),
    _spec("long_multiplication", "Partial products", EARLY_MATH_SKILL_URLS["long_multiplication"]),
    _spec("long_multiplication", "Place-value breakdown", EARLY_MATH_SKILL_URLS["long_multiplication"]),
    _spec("long_multiplication", "Two-digit multiplies", EARLY_MATH_SKILL_URLS["long_multiplication"]),
    _spec("long_division", "Division layout", EARLY_MATH_SKILL_URLS["long_division"]),
    _spec("long_division", "Quotient estimation", EARLY_MATH_SKILL_URLS["long_division"]),
    _spec("long_division", "Remainder handling", EARLY_MATH_SKILL_URLS["long_division"]),
    _spec("money", "Dollar-coin values", EARLY_MATH_SKILL_URLS["money"], required_modes=("expression", "word")),
    _spec("money", "Making change", EARLY_MATH_SKILL_URLS["money"], required_modes=("expression", "word")),
    _spec("money", "Budget-style totals", EARLY_MATH_SKILL_URLS["money"], required_modes=("expression", "word")),
    _spec("money", "Place-value in currency", EARLY_MATH_SKILL_URLS["money"], required_modes=("expression", "word")),
    _spec("measurement", "Length unit conversion", EARLY_MATH_SKILL_URLS["measurement"]),
    _spec("measurement", "Time reading and arithmetic", "https://www.khanacademy.org/math/cc-third-grade-math/time/tell-time-on-number-line/e/telling-time-word-problems-with-the-number-line", required_modes=("expression", "word")),
    _spec("measurement", "Capacity and weight units", EARLY_MATH_SKILL_URLS["measurement"], required_modes=("expression", "word")),
    _spec("measurement", "Temperature basics", EARLY_MATH_SKILL_URLS["measurement"]),
    _spec("measurement", "Metric and customary conversions", "https://www.khanacademy.org/math/cc-fourth-grade-math/imp-measurement-and-data-2/imp-conversion-word-problems/e/metric-conversions-word-problems", required_modes=("expression", "word")),
    _spec("measurement", "Elapsed time", "https://www.khanacademy.org/math/cc-third-grade-math/time/tell-time-on-number-line/e/telling-time-word-problems-with-the-number-line", required_modes=("expression", "word")),
    _spec("geometry_shapes", "2D shape attributes", "https://www.khanacademy.org/math/cc-2nd-grade-math/x3184e0ec:geometry"),
    _spec("geometry_shapes", "3D solid attributes", "https://www.khanacademy.org/math/geometry-home"),
    _spec("geometry_shapes", "Compose 2D shapes", "https://www.khanacademy.org/math/cc-1st-grade-math/cc-1st-measurement-geometry"),
    _spec("geometry_shapes", "Equal shares of shapes", "https://www.khanacademy.org/math/cc-2nd-grade-math/x3184e0ec:geometry"),
    _spec("data_displays", "Sort data into categories", "https://www.khanacademy.org/math/cc-1st-grade-math/cc-1st-measurement-geometry"),
    _spec("data_displays", "Picture and bar graphs", "https://www.khanacademy.org/math/cc-third-grade-math/represent-and-interpret-data/imp-picture-graphs/a/create-pic-graphs"),
    _spec("data_displays", "Dot plots", "https://www.khanacademy.org/math/cc-third-grade-math/represent-and-interpret-data/imp-line-plots/a/line-plots-review"),
    _spec("data_displays", "Frequency tables", EARLY_MATH_SKILL_URLS["data_displays"]),
    _spec("data_displays", "Stem-and-leaf plots", "https://www.khanacademy.org/math/cc-fifth-grade-math/imp-measurement-and-data-3"),
    _spec("data_displays", "Scatterplots and paired data", "https://www.khanacademy.org/math/cc-fifth-grade-math/imp-measurement-and-data-3"),
    _spec("data_displays", "Questions from data displays", "https://www.khanacademy.org/math/cc-2nd-grade-math/x3184e0ec:data"),
    _spec("integers", "Signed numbers", EARLY_MATH_SKILL_URLS["integers"]),
    _spec("integers", "Negative arithmetic", EARLY_MATH_SKILL_URLS["integers"]),
    _spec("integers", "Order-dependent operations", EARLY_MATH_SKILL_URLS["integers"]),
    _spec("integers", "Absolute value", "https://www.khanacademy.org/math/cc-sixth-grade-math/cc-6th-negative-number-topic/x0267d782:cc-6th-comparing-absolute-values/e/absolute-value-word-problems", required_modes=("expression", "word")),
    _spec("order_of_operations", "Parentheses first", "https://www.khanacademy.org/math/cc-sixth-grade-math/x0267d782:cc-6th-exponents-and-order-of-operations/x0267d782:more-on-order-of-operations/e/order_of_operations_2"),
    _spec("order_of_operations", "Multiplication vs addition/subtraction", "https://www.khanacademy.org/math/cc-sixth-grade-math/x0267d782:cc-6th-exponents-and-order-of-operations/x0267d782:more-on-order-of-operations/e/order_of_operations_2"),
    _spec("order_of_operations", "Expression grouping", "https://www.khanacademy.org/math/cc-sixth-grade-math/x0267d782:cc-6th-exponents-and-order-of-operations/x0267d782:more-on-order-of-operations/e/order_of_operations_2"),
    _spec("order_of_operations", "Exponents in expressions", "https://www.khanacademy.org/math/cc-sixth-grade-math/x0267d782:cc-6th-exponents-and-order-of-operations/x0267d782:more-on-order-of-operations/e/order_of_operations_2"),
    _spec("pre_algebra", "Integer and fraction fluency", EARLY_MATH_SKILL_URLS["pre_algebra"]),
    _spec("pre_algebra", "Order of operations", "https://www.khanacademy.org/math/cc-sixth-grade-math/x0267d782:cc-6th-exponents-and-order-of-operations/x0267d782:more-on-order-of-operations/e/order_of_operations_2"),
    _spec("pre_algebra", "Expressions and variables", "https://www.khanacademy.org/math/algebra/x2f8bb11595b61c86:foundation-algebra/x2f8bb11595b61c86:substitute-evaluate-expression/e/evaluating_expressions_2"),
    _spec("pre_algebra", "One-step equations", "https://www.khanacademy.org/math/algebra-basics/alg-basics-solving-equations-and-inequalities"),
    _spec("pre_algebra", "Two-step equations and inequalities", "https://www.khanacademy.org/math/cc-seventh-grade-math/cc-7th-variables-expressions/cc-7th-2-step-equations-intro/e/linear_equations_2"),
    _spec("pre_algebra", "Ratios, rates, and proportional relationships", "https://www.khanacademy.org/math/cc-seventh-grade-math/cc-7th-ratio-proportion/cc-7th-proportional-rel/e/analyzing-and-identifying-proportional-relationships", required_modes=("expression", "word")),
    _spec("pre_algebra", "Percent problems", "https://www.khanacademy.org/math/cc-sixth-grade-math/x0267d782:cc-6th-rates-and-percentages/cc-6th-percent-word-problems/e/percentage_word_problems_1", required_modes=("expression", "word")),
    _spec("pre_algebra", "Exponents, roots, and scientific notation", "https://www.khanacademy.org/math/cc-eighth-grade-math/cc-8th-numbers-operations/cc-8th-scientific-notation/e/scientific_notation"),
    _spec("pre_algebra", "Coordinate plane and function tables", "https://www.khanacademy.org/math/cc-sixth-grade-math/x0267d782:coordinate-plane/x0267d782:cc-6th-distance/e/coordinate-plane-word-problems", required_modes=("expression", "word")),
)


_SPEC_BY_KEY: dict[tuple[str, str], EarlyMathSpec] = {(item.skill, item.subskill): item for item in _EARLY_MATH_SPECS}
_SUBSKILLS_BY_SKILL: dict[str, tuple[str, ...]] = {}
for _skill in EARLY_MATH_SKILLS:
    _SUBSKILLS_BY_SKILL[_skill] = tuple(item.subskill for item in _EARLY_MATH_SPECS if item.skill == _skill)


def early_math_specs() -> tuple[EarlyMathSpec, ...]:
    return _EARLY_MATH_SPECS


def early_math_subskills_for(skill: str) -> tuple[str, ...]:
    return _SUBSKILLS_BY_SKILL.get(skill, ())


def early_math_subskills_by_skill() -> dict[str, tuple[str, ...]]:
    return dict(_SUBSKILLS_BY_SKILL)


def spec_for(skill: str, subskill: str | None) -> EarlyMathSpec | None:
    if subskill is None:
        return None
    return _SPEC_BY_KEY.get((skill, subskill))


def khan_url_for(skill: str, subskill: str | None = None) -> str:
    spec = spec_for(skill, subskill)
    if spec is not None:
        return spec.khan_assignable_url
    return EARLY_MATH_SKILL_URLS.get(skill, "")


def intuition_for(skill: str, subskill: str | None) -> IntuitionPack | None:
    spec = spec_for(skill, subskill)
    if spec is None:
        return None
    return spec.intuition
