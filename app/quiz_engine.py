from __future__ import annotations

import math
import random
from dataclasses import dataclass
from typing import Optional

from .question_bank import try_generate_from_templates


SKILLS = [
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
    "calculus_slope",
    "pre_algebra",
    "algebra_1",
    "algebra_2",
    "statistics",
    "sat_math",
    "psat_math",
    "gre_quant",
]
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

    if preferred_mode is not None:
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

    if skill == "counting":
        low, high = _level_range(level)
        count = random.randint(max(1, low), max(3, high))
        prompt = "Count the objects. How many are there?"
        explanation = "Counting matches a number to a group of objects."
        choices = _choice_set(count) if question_type == "mc" else None
        visual = {"kind": "counting", "count": count}
        return Question(skill, prompt, str(count), explanation, choices, visual)

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
        prompt, answer = _linear_problem(level)
        answer = float(answer)
        explanation = "Isolate x using inverse operations, doing the reverse order of operations."
        choices = _signed_choice_set(int(answer), spread=8) if question_type == "mc" else None
        return Question(skill, prompt, _format_numeric(answer), explanation, choices, None)

    if skill == "geometry_area":
        if level == 1:
            length = random.randint(1, 12)
            width = random.randint(1, 12)
            answer = float(length * width)
            prompt = f"Find the area of a rectangle with length {length} and width {width}."
        elif level == 2:
            base = random.randint(1, 12)
            height = random.randint(1, 12)
            answer = float(base * height)
            prompt = f"Find the area of a square with side {base}." if base == height else f"Find the area of a rectangle with length {base} and width {height}."
        else:
            base = random.choice([2, 4, 6, 8, 10, 12])
            height = random.randint(1, 12)
            answer = base * height / 2
            prompt = f"Find the area of a right triangle with base {base} and height {height}."
        explanation = "Area is built from the shape formula: width × height for rectangles, 1/2 × base × height for triangles."
        choices = _float_choice_set(answer, spread=6.0) if question_type == "mc" else None
        return Question(skill, prompt, _format_numeric(answer), explanation, choices, None)

    if skill == "trig_right_triangle":
        a, b, c = random.choice(RIGHT_TRIANGLE_TRIPLES)
        function = random.choice(["sin", "cos", "tan"])
        if function == "sin":
            prompt = f"For a right triangle with opposite side {a}, adjacent side {b}, hypotenuse {c}, find sin θ."
            answer = a / c
        elif function == "cos":
            prompt = f"For a right triangle with opposite side {a}, adjacent side {b}, hypotenuse {c}, find cos θ."
            answer = b / c
        else:
            prompt = f"For a right triangle with opposite side {a}, adjacent side {b}, hypotenuse {c}, find tan θ."
            answer = a / b
        explanation = "Use the primary trig ratio: sin, cos, tan correspond to opposite/hypotenuse, adjacent/hypotenuse, opposite/adjacent."
        choices = _float_choice_set(answer, spread=0.5) if question_type == "mc" else None
        return Question(skill, prompt, _format_numeric(answer), explanation, choices, None)

    if skill == "stats_percent":
        number = random.randint(10, 400)
        percent = random.choice([10, 12.5, 15, 20, 25, 33, 40, 50, 60, 75, 80, 90]) if level == 1 else random.randint(1, 99)
        answer = number * (percent / 100)
        prompt = f"What is {percent}% of {number}?"
        explanation = "Percent questions are multiplying by a decimal fraction of one."
        choices = _float_choice_set(answer, spread=6.0) if question_type == "mc" else None
        return Question(skill, prompt, _format_numeric(answer), explanation, choices, None)

    if skill == "stats_mean":
        count = 3 if level == 1 else 4 if level == 2 else 5
        values = [random.randint(0, 30) for _ in range(count)]
        answer = sum(values) / count
        prompt = f"Find the mean of these values: {', '.join(map(str, values))}"
        explanation = "The mean is the sum of values divided by how many values there are."
        choices = _float_choice_set(answer, spread=8.0) if question_type == "mc" else None
        return Question(skill, prompt, _format_numeric(answer), explanation, choices, None)

    if skill == "stats_probability":
        favorable = random.randint(1, 9)
        total = random.randint(favorable + 1, favorable + 10)
        answer = _format_probability_as_fraction(favorable, total)
        prompt = f"In equally likely outcomes, if {favorable} outcomes are a success out of {total}, what is the probability of success?"
        explanation = "Probability is the number of successful outcomes divided by all equally likely outcomes."
        choices = _ratio_choice_set(favorable, total) if question_type == "mc" else None
        return Question(skill, prompt, answer, explanation, choices, None)

    if skill == "calculus_slope":
        x1, y1, x2, y2, slope = _slope_line_points(level)
        prompt = f"Find the slope of the line through ({x1}, {y1}) and ({x2}, {y2})."
        answer = slope
        explanation = "Slope is rise over run: (y2 - y1)/(x2 - x1)."
        choices = _signed_choice_set(answer, spread=4) if question_type == "mc" else None
        visual = {"kind": "slope", "x1": x1, "y1": y1, "x2": x2, "y2": y2}
        return Question(skill, prompt, str(answer), explanation, choices, visual)

    raise ValueError("Unknown skill")
