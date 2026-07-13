from __future__ import annotations

import math
import random
from dataclasses import dataclass
from typing import Optional

from .data_analysis import build_data_analysis_problem
from .early_math_catalog import early_math_subskills_for
from .financial_literacy import build_financial_literacy_problem
from .models import ScaffoldStep
from .quiz_content import ContentUnavailableError, is_template_only_skill
from .algebra_1_generators import build_algebra_1_problem
from .algebra_2_generators import build_algebra_2_problem
from .calculus_generators import build_calculus_problem
from .elementary_generators import build_data_display_problem, build_geometry_shapes_problem
from .pre_algebra_generators import build_pre_algebra_problem
from .question_bank import try_generate_from_templates
from .statistics_generators import build_statistics_problem

__all__ = (
    "ALGEBRA_LINEAR_SUBSKILLS",
    "ContentUnavailableError",
    "GEOMETRY_AREA_SUBSKILLS",
    "LEGACY_SKILL_ALIASES",
    "MEASUREMENT_SUBSKILLS",
    "PLACE_VALUE_SUBSKILLS",
    "QUESTION_TYPES",
    "Question",
    "RIGHT_TRIANGLE_TRIPLES",
    "SKILLS",
    "TRIG_PRECALCULUS_SUBSKILLS",
    "generate_question",
)


SKILLS = [
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
    "financial_literacy",
    "measurement",
    "geometry_shapes",
    "data_displays",
    "data_analysis",
    "integers",
    "order_of_operations",
    "algebra_linear",
    "geometry_area",
    "trig_right_triangle",
    "stats_percent",
    "stats_mean",
    "stats_probability",
    "calculus_1",
    "calculus_2",
    "calculus_3",
    "pre_algebra",
    "algebra_1",
    "algebra_2",
    "statistics",
    "sat_math",
    "psat_math",
    "gre_quant",
]
LEGACY_SKILL_ALIASES = {
    "calculus_slope": "calculus_1",
}
QUESTION_TYPES = ["mc", "typed", "both"]
RIGHT_TRIANGLE_TRIPLES = [(3, 4, 5), (5, 12, 13), (6, 8, 10), (8, 15, 17), (9, 12, 15)]


@dataclass
class Question:
    skill: str
    prompt: str
    correct_answer: str
    explanation: str
    choices: Optional[list[str]]
    visual: Optional[dict]
    template_id: Optional[int] = None
    template_external_id: Optional[str] = None
    subskill: Optional[str] = None
    question_label: str = "Core"
    mode: str = "expression"
    scaffold_steps: Optional[list[ScaffoldStep]] = None


def _level_range(level: int) -> tuple[int, int]:
    if level <= 1:
        return (0, 10)
    if level == 2:
        return (0, 20)
    return (0, 50)


def _choice_set(correct: int, spread: int = 4) -> list[str]:
    choices = {correct}
    while len(choices) < 4:
        delta = random.randint(-spread, spread)
        if delta == 0:
            continue
        choices.add(max(0, correct + delta))
    ordered = list(choices)
    random.shuffle(ordered)
    return [str(c) for c in ordered]


def _signed_choice_set(correct: int, spread: int = 4) -> list[str]:
    choices = {correct}
    while len(choices) < 4:
        delta = random.randint(-spread, spread)
        if delta == 0:
            continue
        choices.add(correct + delta)
    ordered = list(choices)
    random.shuffle(ordered)
    return [str(c) for c in ordered]


def _float_choice_set(correct: float, spread: float = 2.0) -> list[str]:
    cent = int(round(correct * 100))
    choices = {correct}
    while len(choices) < 4:
        delta = random.randint(-round(spread * 100), round(spread * 100))
        if delta == 0:
            continue
        choices.add(round((cent + delta) / 100, 2))
    ordered = list(choices)
    random.shuffle(ordered)
    return [_format_numeric(v) for v in ordered]


def _format_numeric(value: float) -> str:
    rounded = round(value, 2)
    if abs(rounded - round(rounded)) < 1e-9:
        return str(int(round(rounded)))
    return f"{rounded:.2f}".rstrip("0").rstrip(".")


def _frac(num: int, den: int) -> tuple[int, int]:
    if den == 0:
        return (0, 1)
    if den < 0:
        num = -num
        den = -den
    gcd = math.gcd(num, den)
    if gcd == 0:
        return (0, 1)
    return (num // gcd, den // gcd)


def _fraction_string(num: int, den: int) -> str:
    num, den = _frac(num, den)
    return f"{num}/{den}"


def _long_range(level: int) -> tuple[int, int]:
    if level <= 1:
        return (10, 99)
    if level == 2:
        return (100, 999)
    return (1000, 9999)


def _money_choice_set(dollars: int, cents: int) -> list[str]:
    def fmt(d: int, c: int) -> str:
        return f"${d}.{c:02d}"

    choices = {fmt(dollars, cents)}
    while len(choices) < 4:
        d = max(0, dollars + random.choice([-2, -1, 1, 2, 5]))
        c = (cents + random.choice([-25, -10, -5, 5, 10, 25])) % 100
        choices.add(fmt(d, c))
    ordered = list(choices)
    random.shuffle(ordered)
    return ordered


def _fraction_choice_set(numerator: int, denominator: int) -> list[str]:
    def fmt(n: int, d: int) -> str:
        return f"{n}/{d}"

    choices = {fmt(numerator, denominator)}
    while len(choices) < 4:
        d = max(2, denominator + random.choice([-2, -1, 1, 2]))
        n = max(0, min(d - 1, numerator + random.choice([-2, -1, 1, 2])))
        if n == 0:
            n = 1
        choices.add(fmt(n, d))
    ordered = list(choices)
    random.shuffle(ordered)
    return ordered


def _ratio_choice_set(numerator: int, denominator: int) -> list[str]:
    choices = {_fraction_string(numerator, denominator)}
    while len(choices) < 4:
        wrong_num = max(0, numerator + random.randint(-5, 5))
        wrong_den = max(1, denominator + random.randint(-5, 5))
        if wrong_num == numerator and wrong_den == denominator:
            continue
        choices.add(_fraction_string(wrong_num, wrong_den))
    ordered = list(choices)
    random.shuffle(ordered)
    return ordered


def _text_choice_set(correct: str, distractors: list[str]) -> list[str]:
    choices = [correct, *distractors]
    random.shuffle(choices)
    return choices[:4]


def _random_expression_with_parentheses(level: int) -> tuple[str, int]:
    a = random.randint(-12, 12)
    b = random.randint(-12, 12)
    c = random.randint(-6, 6)
    if c == 0:
        c = 1

    templates = [
        (f"({a} + {b}) * {c}", (a + b) * c),
        (f"{a} * ({b} + {c})", a * (b + c)),
        (f"({a} - {b}) * {c}", (a - b) * c),
        (f"{a} - ({b} * {c})", a - (b * c)),
    ]
    if level >= 2:
        templates.extend([
            (f"({a} + {b}) - ({c} * 2)", (a + b) - (c * 2)),
            (f"({a} * {b}) + ({c} * {c})", (a * b) + (c * c)),
        ])
    prompt, answer = random.choice(templates)
    return prompt, answer


def _linear_term(coeff: int) -> str:
    if coeff == 1:
        return "x"
    if coeff == -1:
        return "-x"
    return f"{coeff}x"


def _linear_problem(level: int) -> tuple[str, float]:
    coeff = random.randint(-9, 9)
    if coeff == 0:
        coeff = 1
    x = random.randint(-12, 12)
    if level == 1:
        intercept = random.randint(-15, 15)
        rhs = coeff * x + intercept
        if random.choice([True, False]):
            lhs = (
                f"{_linear_term(coeff)} + {abs(intercept)}"
                if intercept >= 0
                else f"{_linear_term(coeff)} - {abs(intercept)}"
            )
            answer = float(x)
        else:
            lhs = (
                f"{_linear_term(coeff)} - {abs(intercept)}"
                if intercept >= 0
                else f"{_linear_term(coeff)} + {abs(intercept)}"
            )
            answer = float(x)
        prompt = f"Solve for x: {lhs} = {rhs}"
        return prompt, answer

    denominator = random.choice([2, 3, 4, 5, 6])
    intercept = random.randint(-9, 9)
    rhs = (coeff * x + intercept * denominator) / denominator
    prompt = (
        f"Solve for x: ({_linear_term(coeff)} / {denominator}) + "
        f"{intercept} = {_format_numeric(rhs)}"
    )
    return prompt, float(x)


def _slope_line_points(level: int) -> tuple[int, int, int, int, int]:
    x1 = random.randint(0, max(1, level * 2))
    x2 = random.randint(x1 + 1, x1 + 5)
    slope = random.choice([n for n in range(-5, 6) if n != 0])
    intercept = random.randint(-8, 8)
    y1 = slope * x1 + intercept
    y2 = slope * x2 + intercept
    return x1, y1, x2, y2, slope


ALGEBRA_LINEAR_SUBSKILLS = (
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
)

GEOMETRY_AREA_SUBSKILLS = (
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
)

TRIG_PRECALCULUS_SUBSKILLS = (
    "Right-triangle trig ratios",
    "Unit circle trig values",
    "Trig functions and graphs",
    "Trig identities",
    "Inverse trig",
    "Vectors",
    "Matrices and linear transformations",
    "Polar coordinates",
)


PLACE_VALUE_SUBSKILLS = early_math_subskills_for("place_value")

MEASUREMENT_SUBSKILLS = early_math_subskills_for("measurement")


def _selected_subskill(requested: str | None, options: tuple[str, ...]) -> str:
    if requested and requested in options:
        return requested
    return random.choice(options)


def _algebra_linear_problem(level: int, requested_subskill: str | None) -> tuple[str, float, str, str]:
    subskill = _selected_subskill(requested_subskill, ALGEBRA_LINEAR_SUBSKILLS)
    if subskill == "One-step equations":
        x = random.randint(-12, 12)
        a = random.randint(-20, 20)
        if random.choice([True, False]):
            prompt = f"Solve for x: x + {a} = {x + a}"
            explanation = "Undo addition/subtraction with the inverse operation."
        else:
            coeff = random.choice([n for n in range(-12, 13) if n not in (0, 1, -1)])
            prompt = f"Solve for x: {coeff}x = {coeff * x}"
            explanation = "Undo multiplication/division to isolate x."
        return prompt, float(x), explanation, subskill
    if subskill == "Two-step equations":
        x = random.randint(-12, 12)
        coeff = random.choice([n for n in range(-9, 10) if n not in (0, 1, -1)])
        intercept = random.randint(-20, 20)
        rhs = (coeff * x) + intercept
        prompt = f"Solve for x: {coeff}x + {intercept} = {rhs}"
        explanation = "Undo constant addition/subtraction first, then divide by the coefficient."
        return prompt, float(x), explanation, subskill
    if subskill == "Variables on both sides":
        x = random.randint(-10, 10)
        left_coeff = random.choice([n for n in range(-8, 9) if n not in (0,)])
        right_coeff = random.choice([n for n in range(-8, 9) if n not in (0, left_coeff)])
        left_const = random.randint(-12, 12)
        right_const = (left_coeff * x + left_const) - (right_coeff * x)
        prompt = f"Solve for x: {left_coeff}x + {left_const} = {right_coeff}x + {right_const}"
        explanation = "Move x terms to one side and constants to the other, then divide."
        return prompt, float(x), explanation, subskill
    if subskill == "Distributive property equations":
        x = random.randint(-8, 8)
        outer = random.choice([2, 3, 4, 5, -2, -3])
        inner = random.randint(-8, 8)
        shift = random.randint(-12, 12)
        rhs = outer * (x + inner) + shift
        prompt = f"Solve for x: {outer}(x + {inner}) + {shift} = {rhs}"
        explanation = "Distribute, combine like terms, then isolate x."
        return prompt, float(x), explanation, subskill
    if subskill == "Fraction and decimal equations":
        denom = random.choice([2, 3, 4, 5, 6, 8, 10])
        x = random.randint(-12, 12) * denom
        shift = random.randint(-15, 15)
        rhs = (x / denom) + shift
        prompt = f"Solve for x: x/{denom} + {shift} = {_format_numeric(rhs)}"
        explanation = "Subtract the constant term, then multiply both sides by the denominator."
        return prompt, float(x), explanation, subskill
    if subskill == "Linear inequalities":
        coeff = random.choice([2, 3, 4, 5])
        threshold = random.randint(-6, 14) + 0.5
        offset = random.randint(-8, 8)
        rhs = int((coeff * threshold) + offset)
        answer = math.floor(((rhs - offset) / coeff) + 1e-9) + 1
        prompt = f"For {coeff}x + {offset} > {rhs}, what is the smallest integer value of x that satisfies it?"
        explanation = "Solve the inequality, then choose the next integer above the boundary."
        return prompt, float(answer), explanation, subskill
    if subskill == "Slope from points":
        x1, y1, x2, y2, slope = _slope_line_points(level)
        prompt = f"Find the slope of the line through ({x1}, {y1}) and ({x2}, {y2})."
        explanation = "Slope is rise over run: (y2 - y1)/(x2 - x1)."
        return prompt, float(slope), explanation, subskill
    if subskill == "Slope-intercept interpretation":
        m = random.choice([n for n in range(-6, 7) if n != 0])
        b = random.randint(-12, 12)
        x = random.randint(-6, 8)
        y = (m * x) + b
        prompt = f"For y = {m}x + {b}, what is y when x = {x}?"
        explanation = "Substitute x into slope-intercept form and evaluate."
        return prompt, float(y), explanation, subskill
    if subskill == "Systems of linear equations":
        x = random.randint(-8, 8)
        y = random.randint(-8, 8)
        s = x + y
        d = x - y
        prompt = (
            "Solve the system and report x: "
            f"x + y = {s}, x - y = {d}."
        )
        explanation = "Add the equations to eliminate y, then divide by 2."
        return prompt, float(x), explanation, subskill
    if subskill == "Direct variation":
        k = random.choice([2, 3, 4, 5, 6, 8, 10])
        x1 = random.randint(2, 8)
        y1 = k * x1
        x2 = random.randint(9, 16)
        y2 = k * x2
        prompt = f"If y varies directly with x and y = {y1} when x = {x1}, find y when x = {x2}."
        explanation = "Direct variation means y = kx with constant ratio y/x."
        return prompt, float(y2), explanation, subskill
    if subskill == "Rate and unit-rate modeling":
        base_fee = random.randint(2, 12)
        rate = random.randint(2, 9)
        miles = random.randint(4, 20)
        total = base_fee + (rate * miles)
        prompt = (
            f"A ride costs ${base_fee} plus ${rate} per mile. "
            f"What is the total cost for {miles} miles?"
        )
        explanation = "This is a linear model: total = fixed fee + rate * quantity."
        return prompt, float(total), explanation, subskill
    tickets_adult = random.randint(12, 40)
    tickets_child = random.randint(6, 28)
    adult_price = random.randint(8, 18)
    child_price = random.randint(4, 12)
    total = (tickets_adult * adult_price) + (tickets_child * child_price)
    prompt = (
        f"A school event sold {tickets_adult} adult tickets at ${adult_price} each "
        f"and {tickets_child} child tickets at ${child_price} each. "
        "What was the total revenue?"
    )
    explanation = "Build and evaluate a linear expression for each group, then add."
    return prompt, float(total), explanation, "Word problems with linear models"


def _geometry_area_problem(level: int, requested_subskill: str | None) -> tuple[str, float, str, str]:
    subskill = _selected_subskill(requested_subskill, GEOMETRY_AREA_SUBSKILLS)
    if subskill == "Area of rectangles and squares":
        length = random.randint(3, 18)
        width = random.randint(3, 18)
        answer = length * width
        prompt = f"Find the area of a rectangle with length {length} and width {width}."
        explanation = "Rectangle area is length * width."
        return prompt, float(answer), explanation, subskill
    if subskill == "Area of triangles and parallelograms":
        base = random.randint(4, 20)
        height = random.randint(3, 16)
        if random.choice([True, False]):
            prompt = f"Find the area of a triangle with base {base} and height {height}."
            answer = (base * height) / 2.0
            explanation = "Triangle area is 1/2 * base * height."
        else:
            prompt = f"Find the area of a parallelogram with base {base} and height {height}."
            answer = float(base * height)
            explanation = "Parallelogram area uses base * perpendicular height."
        return prompt, float(answer), explanation, subskill
    if subskill == "Area of trapezoids and composite figures":
        b1 = random.randint(6, 18)
        b2 = random.randint(5, 16)
        h = random.randint(4, 14)
        answer = ((b1 + b2) * h) / 2.0
        prompt = f"Find the area of a trapezoid with bases {b1} and {b2}, and height {h}."
        explanation = "Trapezoid area is 1/2 * (b1 + b2) * h."
        return prompt, float(answer), explanation, subskill
    if subskill == "Perimeter and missing sides":
        length = random.randint(8, 24)
        width = random.randint(4, 15)
        perimeter = 2 * (length + width)
        prompt = (
            f"A rectangle has perimeter {perimeter} and length {length}. "
            "What is its width?"
        )
        explanation = "Use P = 2L + 2W, then solve for W."
        return prompt, float(width), explanation, subskill
    if subskill == "Circumference and area of circles":
        r = random.randint(2, 14)
        if random.choice([True, False]):
            answer = round(2 * math.pi * r, 2)
            prompt = f"Using pi, find the circumference of a circle with radius {r}. Round to 2 decimals."
            explanation = "Circumference is C = 2*pi*r."
        else:
            answer = round(math.pi * (r**2), 2)
            prompt = f"Using pi, find the area of a circle with radius {r}. Round to 2 decimals."
            explanation = "Circle area is A = pi*r^2."
        return prompt, float(answer), explanation, subskill
    if subskill == "Surface area and volume":
        length = random.randint(3, 12)
        width = random.randint(3, 12)
        height = random.randint(3, 12)
        if random.choice([True, False]):
            answer = 2 * ((length * width) + (length * height) + (width * height))
            prompt = (
                f"Find the surface area of a rectangular prism with l={length}, w={width}, h={height}."
            )
            explanation = "Surface area adds both of each face pair."
        else:
            answer = length * width * height
            prompt = f"Find the volume of a rectangular prism with l={length}, w={width}, h={height}."
            explanation = "Volume of a rectangular prism is l*w*h."
        return prompt, float(answer), explanation, subskill
    if subskill == "Pythagorean theorem":
        a, b, c = random.choice(RIGHT_TRIANGLE_TRIPLES)
        if random.choice([True, False]):
            prompt = f"A right triangle has legs {a} and {b}. Find the hypotenuse."
            answer = float(c)
        else:
            prompt = f"A right triangle has hypotenuse {c} and one leg {a}. Find the other leg."
            answer = float(b)
        explanation = "Use a^2 + b^2 = c^2."
        return prompt, answer, explanation, subskill
    if subskill == "Coordinate geometry distance and midpoint":
        x1 = random.randint(-10, 10)
        y1 = random.randint(-10, 10)
        dx, dy, dist = random.choice(((3, 4, 5), (5, 12, 13), (8, 15, 17)))
        x2 = x1 + random.choice([-1, 1]) * dx
        y2 = y1 + random.choice([-1, 1]) * dy
        if random.choice([True, False]):
            prompt = f"Find the distance between ({x1}, {y1}) and ({x2}, {y2})."
            answer = float(dist)
            explanation = "Distance uses the coordinate form of the Pythagorean theorem."
        else:
            answer = (x1 + x2) / 2.0
            prompt = (
                f"Find the x-coordinate of the midpoint between ({x1}, {y1}) and ({x2}, {y2})."
            )
            explanation = "Midpoint coordinates are averages of the endpoints."
        return prompt, answer, explanation, subskill
    if subskill == "Angles in lines and triangles":
        angle_a = random.randint(25, 110)
        angle_b = random.randint(25, 110)
        answer = 180 - angle_a - angle_b
        prompt = (
            f"In a triangle, two angles are {angle_a} and {angle_b} degrees. "
            "What is the third angle?"
        )
        explanation = "Triangle angles sum to 180 degrees."
        return prompt, float(answer), explanation, subskill
    if subskill == "Triangle congruence criteria":
        criterion, matching_parts = random.choice((("SSS", 3), ("SAS", 3), ("ASA", 3), ("AAS", 3), ("HL", 2)))
        if criterion == "HL":
            prompt = (
                "A proof uses HL triangle congruence for right triangles. "
                "Besides knowing both triangles are right triangles, how many corresponding side lengths are named?"
            )
        else:
            prompt = (
                f"A proof uses {criterion} triangle congruence. "
                "How many corresponding side/angle facts must be named for that criterion?"
            )
        explanation = (
            "Congruence criteria are proof shortcuts: name the required corresponding parts, "
            "then every remaining matching part follows from congruent triangles."
        )
        return prompt, float(matching_parts), explanation, subskill
    if subskill == "Transformations and congruence":
        x = random.randint(-8, 8)
        y = random.randint(-8, 8)
        prompt = f"Point ({x}, {y}) is reflected across the y-axis. What is the new x-coordinate?"
        explanation = "Reflection across the y-axis flips the sign of x."
        return prompt, float(-x), explanation, subskill
    if subskill == "Similarity and scale factor":
        scale = random.randint(2, 6)
        side_small = random.randint(3, 14)
        side_large = scale * side_small
        prompt = (
            f"Two similar triangles have scale factor {scale} from small to large. "
            f"If a side on the small triangle is {side_small}, what is the corresponding large side?"
        )
        explanation = "Corresponding sides in similar figures scale by the same factor."
        return prompt, float(side_large), explanation, subskill
    x1 = random.randint(-7, 7)
    y1 = random.randint(-7, 7)
    x2 = random.randint(-7, 7)
    y2 = random.randint(-7, 7)
    x3 = random.randint(-7, 7)
    y3 = y1 + (y2 - y1)
    x4 = x3 + (x2 - x1)
    prompt = (
        f"Points A({x1},{y1}), B({x2},{y2}), C({x3},{y3}), and D({x4},{y2}) "
        "form a translated shape. What is the horizontal shift from A to C?"
    )
    explanation = "Coordinate proofs track consistent horizontal and vertical shifts."
    return prompt, float(x3 - x1), explanation, "Analytic geometry and coordinate proofs"


def _place_value_problem(level: int, requested_subskill: str | None) -> tuple[str, int, str, str]:
    subskill = _selected_subskill(requested_subskill, PLACE_VALUE_SUBSKILLS)
    if subskill == "Ones, tens, and hundreds identification":
        if level <= 1:
            number = random.randint(10, 99)
        elif level == 2:
            number = random.randint(100, 999)
        else:
            number = random.randint(1000, 9999)
        place = random.choice(["ones", "tens", "hundreds"] if number >= 100 else ["ones", "tens"])
        digits = str(number)
        if place == "ones":
            answer = int(digits[-1])
        elif place == "tens":
            answer = int(digits[-2])
        else:
            answer = int(digits[-3])
        prompt = f"What digit is in the {place} place of {number}?"
        explanation = f"The {place} place is found by looking at the correct position from the right."
        return prompt, answer, explanation, subskill
    if subskill == "Expanded form":
        if level <= 1:
            number = random.randint(10, 99)
        elif level == 2:
            number = random.randint(100, 999)
        else:
            number = random.randint(1000, 9999)
        digits = str(number)
        parts: list[str] = []
        for i, d in enumerate(digits):
            if d != "0":
                place_val = 10 ** (len(digits) - 1 - i)
                parts.append(str(int(d) * place_val))
        expanded = " + ".join(parts)
        prompt = f"What number is represented by the expanded form: {expanded}?"
        explanation = "Expanded form breaks a number into the sum of each digit times its place value."
        return prompt, number, explanation, subskill
    if subskill == "Decimal place value and comparison":
        whole = random.randint(0, 9)
        tenths = random.randint(0, 9)
        hundredths = random.randint(0, 9)
        if random.choice([True, False]):
            prompt = f"What digit is in the tenths place of {whole}.{tenths}{hundredths}?"
            explanation = "The tenths place is the first digit to the right of the decimal point."
            return prompt, tenths, explanation, subskill
        other_tenths = tenths
        other_hundredths = hundredths
        while other_tenths == tenths and other_hundredths == hundredths:
            other_tenths = random.randint(0, 9)
            other_hundredths = random.randint(0, 9)
        a = float(f"{whole}.{tenths}{hundredths}")
        b = float(f"{whole}.{other_tenths}{other_hundredths}")
        larger = a if a > b else b
        prompt = f"Which decimal is larger: {a:.2f} or {b:.2f}? Enter the answer in hundredths."
        explanation = "Compare decimals place by place: ones, tenths, then hundredths."
        return prompt, int(round(larger * 100)), explanation, subskill
    # Compare numbers by place value
    if level <= 1:
        a = random.randint(10, 99)
        b = random.randint(10, 99)
    elif level == 2:
        a = random.randint(100, 999)
        b = random.randint(100, 999)
    else:
        a = random.randint(1000, 9999)
        b = random.randint(1000, 9999)
    while a == b:
        b = random.randint(a - 20, a + 20)
        b = max(10, b)
    larger = max(a, b)
    prompt = f"Which number is larger: {a} or {b}?"
    explanation = "Compare digit by digit from the highest place value to the lowest."
    return prompt, larger, explanation, subskill


def _measurement_problem(level: int, requested_subskill: str | None) -> tuple[str, float, str, str]:
    subskill = _selected_subskill(requested_subskill, MEASUREMENT_SUBSKILLS)
    if subskill == "Length unit conversion":
        if random.choice([True, False]):
            feet = random.randint(1, 20)
            inches = feet * 12
            prompt = f"How many inches are in {feet} feet?"
            answer = float(inches)
            explanation = "There are 12 inches in 1 foot."
        else:
            meters = random.randint(1, 50)
            cm = meters * 100
            prompt = f"How many centimeters are in {meters} meters?"
            answer = float(cm)
            explanation = "There are 100 centimeters in 1 meter."
        return prompt, answer, explanation, subskill
    if subskill == "Time reading and arithmetic":
        hours = random.randint(1, 8)
        minutes = random.randint(1, 5) * 15
        total_minutes = hours * 60 + minutes
        prompt = f"How many minutes are in {hours} hours and {minutes} minutes?"
        answer = float(total_minutes)
        explanation = "There are 60 minutes in 1 hour. Multiply hours by 60, then add remaining minutes."
        return prompt, answer, explanation, subskill
    if subskill == "Capacity and weight units":
        if random.choice([True, False]):
            quarts = random.randint(1, 8)
            prompt = f"How many cups are in {quarts} quarts?"
            answer = float(quarts * 4)
            explanation = "There are 4 cups in 1 quart."
        else:
            pounds = random.randint(1, 12)
            prompt = f"How many ounces are in {pounds} pounds?"
            answer = float(pounds * 16)
            explanation = "There are 16 ounces in 1 pound."
        return prompt, answer, explanation, subskill
    if subskill == "Metric and customary conversions":
        if random.choice([True, False]):
            yards = random.randint(2, 15)
            prompt = f"How many feet are in {yards} yards?"
            answer = float(yards * 3)
            explanation = "There are 3 feet in 1 yard."
        else:
            liters = random.randint(2, 12)
            prompt = f"How many milliliters are in {liters} liters?"
            answer = float(liters * 1000)
            explanation = "There are 1000 milliliters in 1 liter."
        return prompt, answer, explanation, subskill
    if subskill == "Elapsed time":
        start_hour = random.randint(1, 10)
        start_minute = random.choice([0, 10, 15, 20, 30, 40, 45, 50])
        elapsed = random.randint(10, 9 + level * 20)
        start_total = start_hour * 60 + start_minute
        finish_total = start_total + elapsed
        finish_hour = (finish_total // 60) % 12 or 12
        finish_minute = finish_total % 60
        prompt = (
            f"A practice starts at {start_hour}:{start_minute:02d} and ends at "
            f"{finish_hour}:{finish_minute:02d}. How many minutes elapsed?"
        )
        explanation = "Elapsed time is the distance between the start time and end time."
        return prompt, float(elapsed), explanation, subskill
    # Temperature basics
    temp_f = random.choice([32, 50, 68, 86, 104, 122, 140, 158, 176, 194, 212])
    temp_c = (temp_f - 32) * 5 // 9
    prompt = f"Water boils at 212°F and freezes at 32°F. Is {temp_f}°F above or below freezing? Answer the temperature in °C. (Use: °C = (°F − 32) × 5/9)"
    answer = float(temp_c)
    explanation = "Convert using the formula: °C = (°F − 32) × 5/9."
    return prompt, answer, explanation, subskill


def _canonical_skill_name(skill: str) -> str:
    return LEGACY_SKILL_ALIASES.get(skill, skill)


def _poly_term(coeff: int, power: int) -> str:
    if coeff == 0:
        return ""
    if power == 0:
        return str(coeff)
    magnitude = abs(coeff)
    coeff_text = "" if magnitude == 1 else str(magnitude)
    if power == 1:
        base = f"{coeff_text}x"
    else:
        base = f"{coeff_text}x^{power}"
    if coeff < 0:
        return f"-{base}"
    return base


def _join_terms(terms: list[str]) -> str:
    out: list[str] = []
    for term in terms:
        if not term:
            continue
        if not out:
            out.append(term)
            continue
        if term.startswith("-"):
            out.append(f"- {term[1:]}")
        else:
            out.append(f"+ {term}")
    return " ".join(out) if out else "0"


def _format_probability_as_fraction(numer: int, denom: int) -> str:
    g = math.gcd(numer, denom)
    return _fraction_string(numer // g, denom // g)


def _division_answer(quotient: int, remainder: int) -> str:
    if remainder:
        return f"{quotient} R {remainder}"
    return str(quotient)


def _division_choices(quotient: int, remainder: int, divisor: int) -> list[str]:
    if remainder == 0:
        return _choice_set(quotient, spread=4)
    choices = {_division_answer(quotient, remainder)}
    while len(choices) < 4:
        dq = max(0, quotient + random.randint(-2, 2))
        dr = random.randint(0, max(0, divisor - 1))
        if dq == quotient and dr == remainder:
            continue
        choices.add(_division_answer(dq, dr))
    ordered = list(choices)
    random.shuffle(ordered)
    return ordered


def generate_question(
    skill: str,
    level: int,
    question_type: str,
    *,
    subskill: str | None = None,
    preferred_mode: str | None = None,
) -> Question:
    if question_type not in QUESTION_TYPES:
        raise ValueError("Unknown question type")

    if skill == "mixed":
        skill = random.choice(SKILLS)
        subskill = None

    skill = _canonical_skill_name(skill)
    use_templates = skill not in {"trig_right_triangle", "calculus_1", "calculus_2", "calculus_3"}
    if use_templates and subskill is not None and skill in {"algebra_linear", "geometry_area", "algebra_1", "algebra_2"}:
        use_templates = False
    if use_templates and subskill is not None and skill in {"stats_percent", "stats_mean", "stats_probability", "statistics"}:
        use_templates = False
    if use_templates and subskill is not None and skill == "financial_literacy":
        use_templates = False
    if use_templates and subskill is not None and skill == "data_analysis":
        use_templates = False

    if use_templates:
        templated = try_generate_from_templates(
            skill,
            level,
            question_type if question_type != "both" else "typed",
            rng=random,
            subskill=subskill,
            mode=preferred_mode,
        )
        if templated is not None:
            if question_type == "both":
                # Let the caller alternate mc/typed; we generated typed above.
                return templated
            return templated

    if preferred_mode is not None and use_templates:
        templated = try_generate_from_templates(
            skill,
            level,
            question_type if question_type != "both" else "typed",
            rng=random,
            subskill=subskill,
            mode=None,
        )
        if templated is not None:
            if question_type == "both":
                return templated
            return templated

    if use_templates and subskill is not None and skill != "pre_algebra" and not early_math_subskills_for(skill):
        raise ContentUnavailableError(skill, subskill=subskill, mode=preferred_mode)

    if use_templates and is_template_only_skill(skill):
        raise ContentUnavailableError(skill, subskill=subskill, mode=preferred_mode)

    if skill == "counting":
        low, high = _level_range(level)
        count = random.randint(max(1, low), max(3, high))
        prompt = "Count the objects. How many are there?"
        explanation = "Counting matches a number to a group of objects."
        choices = _choice_set(count) if question_type == "mc" else None
        visual = {"kind": "counting", "count": count}
        return Question(skill, prompt, str(count), explanation, choices, visual)

    if skill == "place_value":
        prompt, answer, explanation, chosen_subskill = _place_value_problem(level, subskill)
        choices = _choice_set(answer, spread=6) if question_type == "mc" else None
        return Question(
            skill, prompt, str(answer), explanation, choices, None,
            subskill=chosen_subskill,
        )

    if skill == "add_subtract":
        low, high = _level_range(level)
        a = random.randint(low, high)
        b = random.randint(low, high)
        if random.choice([True, False]):
            prompt = f"{a} + {b} = ?"
            answer = a + b
            explanation = "Adding combines two groups into one."
            visual = {"kind": "add", "a": a, "b": b}
        else:
            a, b = max(a, b), min(a, b)
            prompt = f"{a} - {b} = ?"
            answer = a - b
            explanation = "Subtracting removes part of a group."
            visual = {"kind": "subtract", "a": a, "b": b}
        choices = _choice_set(answer) if question_type == "mc" else None
        return Question(skill, prompt, str(answer), explanation, choices, visual)

    if skill == "multiply":
        low, high = _level_range(level)
        a = random.randint(1, max(2, high // 2))
        b = random.randint(1, max(2, high // 2))
        prompt = f"{a} x {b} = ?"
        answer = a * b
        explanation = "Multiplication is repeated groups."
        choices = _choice_set(answer, spread=6) if question_type == "mc" else None
        visual = {"kind": "multiply", "a": a, "b": b}
        return Question(skill, prompt, str(answer), explanation, choices, visual)

    if skill == "divide":
        low, high = _level_range(level)
        divisor = random.randint(1, max(2, high // 3))
        quotient = random.randint(1, max(2, high // 3))
        total = divisor * quotient
        prompt = f"{total} / {divisor} = ?"
        answer = quotient
        explanation = "Division shares a total into equal groups."
        choices = _choice_set(answer, spread=4) if question_type == "mc" else None
        visual = {"kind": "divide", "total": total, "groups": divisor}
        return Question(skill, prompt, str(answer), explanation, choices, visual)

    if skill == "ratios":
        low, high = _level_range(level)
        a = random.randint(1, max(2, high // 2))
        b = random.randint(1, max(2, high // 2))
        prompt = f"What is the ratio of A to B if A={a} and B={b}? (A:B)"
        answer = f"{a}:{b}"
        explanation = "A ratio compares two amounts side by side."
        choices = None if question_type == "typed" else [f"{a}:{b}", f"{b}:{a}", f"{a+b}:1", f"1:{a+b}"]
        visual = {"kind": "ratio", "a": a, "b": b}
        return Question(skill, prompt, answer, explanation, choices, visual)

    if skill == "fractions":
        if level <= 1:
            denominator = random.randint(2, 6)
            numerator = random.randint(1, denominator - 1)
        elif level == 2:
            denominator = random.randint(2, 8)
            numerator = random.randint(1, denominator * 2 - 1)
        else:
            denominator = random.randint(2, 10)
            numerator = random.randint(1, denominator * 3 - 1)
        if numerator % denominator == 0:
            numerator = max(1, numerator - 1)
        prompt = "What fraction is shaded? (fraction, decimal, or repeating like 0.(3) or 0.1(6))"
        answer = f"{numerator}/{denominator}"
        explanation = "The denominator is the total slices; the numerator is the shaded slices."
        choices = _fraction_choice_set(numerator, denominator) if question_type == "mc" else None
        visual = {"kind": "fraction", "numerator": numerator, "denominator": denominator}
        return Question(skill, prompt, answer, explanation, choices, visual)

    if skill == "long_addition":
        low, high = _long_range(level)
        a = random.randint(low, high)
        b = random.randint(low, high)
        prompt = f"Long addition: {a} + {b} = ?"
        answer = a + b
        explanation = "Long addition lines up place values and uses carries."
        choices = _choice_set(answer, spread=12) if question_type == "mc" else None
        visual = {"kind": "long_addition", "a": a, "b": b}
        return Question(skill, prompt, str(answer), explanation, choices, visual)

    if skill == "long_subtraction":
        low, high = _long_range(level)
        a = random.randint(low, high)
        b = random.randint(low, high)
        a, b = max(a, b), min(a, b)
        prompt = f"Long subtraction: {a} - {b} = ?"
        answer = a - b
        explanation = "Long subtraction keeps digits aligned and uses borrowing when needed."
        choices = _choice_set(answer, spread=12) if question_type == "mc" else None
        visual = {"kind": "long_subtraction", "a": a, "b": b}
        return Question(skill, prompt, str(answer), explanation, choices, visual)

    if skill == "long_multiplication":
        if level <= 1:
            a = random.randint(10, 99)
            b = random.randint(2, 9)
        elif level == 2:
            a = random.randint(10, 99)
            b = random.randint(10, 99)
        else:
            a = random.randint(100, 999)
            b = random.randint(10, 99)
        prompt = f"Long multiplication: {a} x {b} = ?"
        answer = a * b
        explanation = "Long multiplication builds partial products by place value."
        choices = _choice_set(answer, spread=20) if question_type == "mc" else None
        visual = {"kind": "long_multiplication", "a": a, "b": b}
        return Question(skill, prompt, str(answer), explanation, choices, visual)

    if skill == "long_division":
        if level <= 1:
            divisor = random.randint(2, 9)
            quotient = random.randint(2, 9)
        elif level == 2:
            divisor = random.randint(2, 9)
            quotient = random.randint(10, 99)
        else:
            divisor = random.randint(2, 12)
            quotient = random.randint(10, 99)
        remainder = random.randint(0, divisor - 1)
        dividend = divisor * quotient + remainder
        prompt = f"Long division: {dividend} / {divisor} = ? (use 'R' for remainder)"
        answer = _division_answer(quotient, remainder)
        explanation = "Long division shows how many groups fit, with any leftover as remainder."
        choices = _division_choices(quotient, remainder, divisor) if question_type == "mc" else None
        visual = {"kind": "long_division", "dividend": dividend, "divisor": divisor}
        return Question(skill, prompt, answer, explanation, choices, visual)

    if skill == "money":
        if level <= 1:
            dollars = random.randint(0, 20)
        elif level == 2:
            dollars = random.randint(0, 50)
        else:
            dollars = random.randint(0, 100)
        cents = random.randint(0, 99)
        prompt = "How much money is shown? (write as $d.cc)"
        answer = f"${dollars}.{cents:02d}"
        explanation = "Money totals combine dollars and cents."
        choices = _money_choice_set(dollars, cents) if question_type == "mc" else None
        visual = {"kind": "money", "dollars": dollars, "cents": cents}
        return Question(skill, prompt, answer, explanation, choices, visual)

    if skill == "financial_literacy":
        problem = build_financial_literacy_problem(level, subskill, multiple_choice=question_type == "mc")
        return Question(
            skill,
            problem.prompt,
            problem.answer,
            problem.explanation,
            problem.choices,
            None,
            subskill=problem.subskill,
        )

    if skill == "measurement":
        prompt, answer, explanation, chosen_subskill = _measurement_problem(level, subskill)
        if abs(answer - round(answer)) < 1e-9:
            choices = _signed_choice_set(int(round(answer)), spread=20) if question_type == "mc" else None
        else:
            choices = _float_choice_set(answer, spread=10.0) if question_type == "mc" else None
        return Question(
            skill, prompt, _format_numeric(answer), explanation, choices, None,
            subskill=chosen_subskill,
        )

    if skill == "geometry_shapes":
        problem = build_geometry_shapes_problem(level, subskill, multiple_choice=question_type == "mc")
        return Question(
            skill,
            problem.prompt,
            problem.answer,
            problem.explanation,
            problem.choices,
            None,
            subskill=problem.subskill,
        )

    if skill == "data_displays":
        problem = build_data_display_problem(level, subskill, multiple_choice=question_type == "mc")
        return Question(
            skill,
            problem.prompt,
            problem.answer,
            problem.explanation,
            problem.choices,
            None,
            subskill=problem.subskill,
        )

    if skill == "data_analysis":
        problem = build_data_analysis_problem(level, subskill, multiple_choice=question_type == "mc")
        return Question(
            skill,
            problem.prompt,
            problem.answer,
            problem.explanation,
            problem.choices,
            None,
            subskill=problem.subskill,
        )

    if skill == "integers":
        prompt, answer = _random_expression_with_parentheses(level)
        explanation = "Apply parentheses first, then multiplication, and finally addition and subtraction."
        answer_int = int(answer)
        choices = _signed_choice_set(answer_int, spread=14) if question_type == "mc" else None
        return Question(skill, f"Simplify this expression: {prompt}", str(answer_int), explanation, choices, None)

    if skill == "order_of_operations":
        prompt, answer = _random_expression_with_parentheses(level)
        answer = int(answer)
        explanation = "Use order-of-operations: parentheses, multiplication, then addition and subtraction."
        choices = _signed_choice_set(answer) if question_type == "mc" else None
        return Question(skill, f"Evaluate: {prompt}", str(answer), explanation, choices, None)

    if skill == "algebra_linear":
        prompt, answer, explanation, chosen_subskill = _algebra_linear_problem(level, subskill)
        spread = 10 if level >= 2 else 6
        if abs(answer - round(answer)) < 1e-9:
            choices = _signed_choice_set(int(round(answer)), spread=spread) if question_type == "mc" else None
        else:
            choices = _float_choice_set(answer, spread=4.0) if question_type == "mc" else None
        return Question(
            skill,
            prompt,
            _format_numeric(answer),
            explanation,
            choices,
            None,
            subskill=chosen_subskill,
        )

    if skill == "geometry_area":
        prompt, answer, explanation, chosen_subskill = _geometry_area_problem(level, subskill)
        if abs(answer - round(answer)) < 1e-9:
            choices = _signed_choice_set(int(round(answer)), spread=10) if question_type == "mc" else None
        else:
            choices = _float_choice_set(answer, spread=6.0) if question_type == "mc" else None
        return Question(
            skill,
            prompt,
            _format_numeric(answer),
            explanation,
            choices,
            None,
            subskill=chosen_subskill,
        )

    if skill == "place_value":
        prompt, answer, explanation, chosen_subskill = _place_value_problem(level, subskill)
        if abs(answer - round(answer)) < 1e-9:
            choices = _signed_choice_set(int(round(answer)), spread=5) if question_type == "mc" else None
        else:
            choices = _float_choice_set(answer, spread=2.0) if question_type == "mc" else None
        return Question(
            skill,
            prompt,
            _format_numeric(answer),
            explanation,
            choices,
            None,
            subskill=chosen_subskill,
        )

    if skill == "measurement":
        prompt, answer, explanation, chosen_subskill = _measurement_problem(level, subskill)
        if abs(answer - round(answer)) < 1e-9:
            choices = _signed_choice_set(int(round(answer)), spread=5) if question_type == "mc" else None
        else:
            choices = _float_choice_set(answer, spread=2.0) if question_type == "mc" else None
        return Question(
            skill,
            prompt,
            _format_numeric(answer),
            explanation,
            choices,
            None,
            subskill=chosen_subskill,
        )

    if skill == "pre_algebra":
        prompt, answer, explanation, chosen_subskill = build_pre_algebra_problem(level, subskill)
        if abs(answer - round(answer)) < 1e-9:
            choices = _signed_choice_set(int(round(answer)), spread=8) if question_type == "mc" else None
        else:
            choices = _float_choice_set(answer, spread=4.0) if question_type == "mc" else None
        return Question(
            skill,
            prompt,
            _format_numeric(answer),
            explanation,
            choices,
            None,
            subskill=chosen_subskill,
        )

    if skill == "algebra_1":
        prompt, answer, explanation, chosen_subskill = build_algebra_1_problem(level, subskill)
        if abs(answer - round(answer)) < 1e-9:
            choices = _signed_choice_set(int(round(answer)), spread=10) if question_type == "mc" else None
        else:
            choices = _float_choice_set(answer, spread=5.0) if question_type == "mc" else None
        return Question(
            skill,
            prompt,
            _format_numeric(answer),
            explanation,
            choices,
            None,
            subskill=chosen_subskill,
        )

    if skill == "algebra_2":
        prompt, answer, explanation, chosen_subskill = build_algebra_2_problem(level, subskill)
        if abs(answer - round(answer)) < 1e-9:
            choices = _signed_choice_set(int(round(answer)), spread=12) if question_type == "mc" else None
        else:
            choices = _float_choice_set(answer, spread=6.0) if question_type == "mc" else None
        return Question(
            skill,
            prompt,
            _format_numeric(answer),
            explanation,
            choices,
            None,
            subskill=chosen_subskill,
        )

    if skill == "trig_right_triangle":
        chosen_subskill = _selected_subskill(subskill, TRIG_PRECALCULUS_SUBSKILLS)
        if chosen_subskill == "Right-triangle trig ratios":
            a, b, c = random.choice(RIGHT_TRIANGLE_TRIPLES)
            function = random.choice(["sin", "cos", "tan"])
            if preferred_mode == "intuition":
                ratio_by_function = {
                    "sin": "opposite/hypotenuse",
                    "cos": "adjacent/hypotenuse",
                    "tan": "opposite/adjacent",
                }
                correct_ratio = ratio_by_function[function]
                prompt = (
                    f"For a right triangle with opposite side {a}, adjacent side {b}, and hypotenuse {c}, "
                    f"which side ratio matches {function} theta before you compute any value?"
                )
                explanation = "Match the trig name to the side roles first, then plug in the actual side lengths."
                choices = (
                    _text_choice_set(
                        correct_ratio,
                        ["adjacent/opposite", "hypotenuse/opposite", "hypotenuse/adjacent"],
                    )
                    if question_type == "mc"
                    else None
                )
                return Question(
                    skill,
                    prompt,
                    correct_ratio,
                    explanation,
                    choices,
                    None,
                    subskill=chosen_subskill,
                    mode="intuition",
                )
            if function == "sin":
                prompt = f"For a right triangle with opposite side {a}, adjacent side {b}, hypotenuse {c}, find sin theta."
                answer = a / c
            elif function == "cos":
                prompt = f"For a right triangle with opposite side {a}, adjacent side {b}, hypotenuse {c}, find cos theta."
                answer = b / c
            else:
                prompt = f"For a right triangle with opposite side {a}, adjacent side {b}, hypotenuse {c}, find tan theta."
                answer = a / b
            explanation = "Use the primary trig ratio: sin, cos, tan correspond to opposite/hypotenuse, adjacent/hypotenuse, opposite/adjacent."
        elif chosen_subskill == "Unit circle trig values":
            angle, sin_value, cos_value = random.choice(
                ((0, 0.0, 1.0), (30, 0.5, 0.866), (45, 0.707, 0.707), (60, 0.866, 0.5), (90, 1.0, 0.0))
            )
            if random.choice([True, False]):
                prompt = f"On the unit circle, what is sin({angle} degrees)? Round to 2 decimals."
                answer = sin_value
            else:
                prompt = f"On the unit circle, what is cos({angle} degrees)? Round to 2 decimals."
                answer = cos_value
            explanation = "Unit-circle coordinates are (cos theta, sin theta)."
        elif chosen_subskill == "Trig functions and graphs":
            amplitude = random.randint(2, 8)
            prompt = f"For y = {amplitude}sin(x), what is the amplitude of the graph?"
            answer = float(amplitude)
            explanation = "The amplitude is the distance from the midline to a peak."
        elif chosen_subskill == "Trig identities":
            angle = random.choice([15, 30, 45, 60, 75])
            prompt = f"For any angle, simplify sin^2({angle}) + cos^2({angle})."
            answer = 1.0
            explanation = "The Pythagorean identity says sin^2(theta) + cos^2(theta) = 1."
        elif chosen_subskill == "Inverse trig":
            angle, value = random.choice(((0, 0.0), (30, 0.5), (90, 1.0)))
            prompt = f"In the first quadrant, arcsin({value}) equals how many degrees?"
            answer = float(angle)
            explanation = "Inverse trig reverses a trig ratio back to an angle in the stated range."
        elif chosen_subskill == "Vectors":
            x, y, magnitude = random.choice(((3, 4, 5), (5, 12, 13), (8, 15, 17)))
            prompt = f"Find the magnitude of vector <{x}, {y}>."
            answer = float(magnitude)
            explanation = "Vector magnitude uses the Pythagorean theorem on the components."
        elif chosen_subskill == "Matrices and linear transformations":
            scale_x = random.randint(2, 6)
            x = random.randint(-5, 7)
            y = random.randint(-5, 7)
            prompt = (
                f"A diagonal matrix scales x by {scale_x} and leaves y unchanged. "
                f"What is the new x-coordinate of ({x}, {y})?"
            )
            answer = float(scale_x * x)
            explanation = "A diagonal transformation multiplies each coordinate by its matching diagonal entry."
        else:
            x, y, radius = random.choice(((3, 4, 5), (5, 12, 13), (8, 15, 17)))
            prompt = f"Convert point ({x}, {y}) to polar form. What is r?"
            answer = float(radius)
            explanation = "The polar radius is the distance from the origin to the point."
        if abs(answer - round(answer)) < 1e-9:
            choices = _signed_choice_set(int(round(answer)), spread=8) if question_type == "mc" else None
        else:
            choices = _float_choice_set(answer, spread=0.8) if question_type == "mc" else None
        return Question(skill, prompt, _format_numeric(answer), explanation, choices, None, subskill=chosen_subskill)

    if skill == "stats_percent":
        chosen_subskill = _selected_subskill(
            subskill,
            ("Percent change", "Reverse percent change", "Percent word problems"),
        )
        number = random.randint(10, 400)
        percent = random.choice([10, 12.5, 15, 20, 25, 33, 40, 50, 60, 75, 80, 90]) if level == 1 else random.randint(1, 99)
        answer = number * (percent / 100)
        if chosen_subskill == "Reverse percent change":
            prompt = f"{_format_numeric(answer)} is {percent}% of what number?"
            answer = float(number)
            explanation = "Reverse percent problems divide the part by the percent-as-decimal to recover the whole."
        elif chosen_subskill == "Percent word problems":
            whole = random.randint(20, 120)
            part = random.randint(2, whole - 2)
            prompt = f"A sample has {part} items in one category out of {whole} total. About what percent is that category?"
            answer = (part * 100) / whole
            explanation = "A percent compares the category count to the whole sample out of 100."
        else:
            prompt = f"What is {percent}% of {number}?"
            explanation = "Percent questions are multiplying by a decimal fraction of one."
        choices = _float_choice_set(answer, spread=6.0) if question_type == "mc" else None
        return Question(skill, prompt, _format_numeric(answer), explanation, choices, None, subskill=chosen_subskill)

    if skill == "stats_mean":
        chosen_subskill = _selected_subskill(subskill, ("Mean", "Mean from display"))
        count = 3 if level == 1 else 4 if level == 2 else 5
        values = [random.randint(0, 30) for _ in range(count)]
        answer = sum(values) / count
        if chosen_subskill == "Mean from display":
            prompt = f"A dot plot shows these counts by value: {', '.join(map(str, values))}. Find the mean count."
            explanation = "Read the displayed counts, add them, then divide by how many counts are shown."
        else:
            prompt = f"Find the mean of these values: {', '.join(map(str, values))}"
            explanation = "The mean is the sum of values divided by how many values there are."
        choices = _float_choice_set(answer, spread=8.0) if question_type == "mc" else None
        return Question(skill, prompt, _format_numeric(answer), explanation, choices, None, subskill=chosen_subskill)

    if skill == "stats_probability":
        chosen_subskill = "Probability models"
        if subskill is not None and subskill != chosen_subskill:
            raise ContentUnavailableError(skill, subskill=subskill, mode=preferred_mode)
        favorable = random.randint(1, 9)
        total = random.randint(favorable + 1, favorable + 10)
        answer = _format_probability_as_fraction(favorable, total)
        prompt = f"In equally likely outcomes, if {favorable} outcomes are a success out of {total}, what is the probability of success?"
        explanation = "Probability is the number of successful outcomes divided by all equally likely outcomes."
        choices = _ratio_choice_set(favorable, total) if question_type == "mc" else None
        return Question(skill, prompt, answer, explanation, choices, None, subskill=chosen_subskill)

    if skill == "statistics":
        try:
            problem = build_statistics_problem(level, question_type, subskill, preferred_mode)
        except KeyError as exc:
            raise ContentUnavailableError(skill, subskill=subskill, mode=preferred_mode) from exc
        return Question(
            skill,
            problem.prompt,
            problem.correct_answer,
            problem.explanation,
            problem.choices,
            None,
            subskill=problem.subskill,
            mode=problem.mode,
        )

    if skill in {"calculus_1", "calculus_2", "calculus_3"}:
        try:
            problem = build_calculus_problem(skill, level, question_type, subskill, preferred_mode)
        except KeyError as exc:
            raise ContentUnavailableError(skill, subskill=subskill, mode=preferred_mode) from exc
        return Question(
            skill,
            problem.prompt,
            problem.correct_answer,
            problem.explanation,
            problem.choices,
            problem.visual,
            subskill=problem.subskill,
            mode=problem.mode,
        )

    raise ValueError("Unknown skill")
