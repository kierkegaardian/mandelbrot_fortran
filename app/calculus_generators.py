from __future__ import annotations

from dataclasses import dataclass
import random

from .calculus_catalog import CALCULUS_SKILL_SUBSKILLS, DEFAULT_SUBSKILL, intuition_for


@dataclass(frozen=True)
class CalculusProblem:
    prompt: str
    correct_answer: str
    explanation: str
    choices: list[str] | None
    visual: dict[str, object] | None
    subskill: str
    mode: str = "expression"


def build_calculus_problem(
    skill: str,
    level: int,
    question_type: str,
    subskill: str | None,
    preferred_mode: str | None,
) -> CalculusProblem:
    chosen = _selected_subskill(skill, subskill)
    if preferred_mode == "intuition":
        return _build_intuition_problem(skill, chosen, question_type, level)
    if skill == "calculus_1":
        return _build_calculus_1(level, question_type, chosen)
    if skill == "calculus_2":
        return _build_calculus_2(level, question_type, chosen)
    if skill == "calculus_3":
        return _build_calculus_3(level, question_type, chosen)
    raise KeyError(skill)


def _selected_subskill(skill: str, requested: str | None) -> str:
    options = CALCULUS_SKILL_SUBSKILLS.get(skill)
    if options is None:
        raise KeyError(skill)
    if requested:
        if requested not in options:
            raise KeyError(requested)
        return requested
    return DEFAULT_SUBSKILL[skill]


def _build_calculus_1(level: int, question_type: str, subskill: str) -> CalculusProblem:
    if subskill == "Limits and continuity":
        m, b, x0 = random.randint(-5, 5) or 2, random.randint(-8, 8), random.randint(-4, 4)
        answer = m * x0 + b
        prompt = f"For continuous f(x) = {_join_terms([_poly_term(m, 1), _poly_term(b, 0)])}, find lim x->{x0} f(x)."
        return _numeric(subskill, prompt, answer, "Continuity lets you evaluate the limit by substituting the target x.", question_type)
    if subskill == "Average rate of change between two points":
        x1, y1, x2, y2, slope = _slope_line_points(level)
        prompt = f"Find the average rate of change from ({x1}, {y1}) to ({x2}, {y2})."
        visual = {"kind": "slope", "x1": x1, "y1": y1, "x2": x2, "y2": y2}
        return _numeric(subskill, prompt, slope, "Average rate of change is rise over run, (y2 - y1)/(x2 - x1).", question_type, visual)
    if subskill == "Derivative rules":
        power = random.randint(2, 5)
        coeff = random.randint(2, 8)
        x0 = random.randint(-3, 4)
        answer = coeff * power * (x0 ** (power - 1))
        prompt = f"For f(x) = {coeff}x^{power}, find f'({x0})."
        return _numeric(subskill, prompt, answer, "Use the power rule, then substitute the point.", question_type, spread=10)
    if subskill == "Derivative as slope and velocity":
        a, b, t = random.randint(1, 5), random.randint(-4, 6), random.randint(1, 6)
        answer = (2 * a * t) + b
        prompt = f"If position s(t) = {a}t^2 + {b}t, what is the velocity at t = {t}?"
        return _numeric(subskill, prompt, answer, "Velocity is the derivative of position with respect to time.", question_type, spread=10)
    h, k = random.randint(-4, 5), random.randint(4, 18)
    prompt = f"For f(x) = -(x - {h})^2 + {k}, what is the maximum value?"
    return _numeric("Optimization", prompt, k, "A downward-opening vertex form has maximum value at the vertex height.", question_type)


def _build_calculus_2(level: int, question_type: str, subskill: str) -> CalculusProblem:
    if subskill == "Definite integral of a linear function":
        m, b, a = random.randint(-5, 5) or 3, random.randint(-8, 8), random.randint(-2, 2)
        c = a + random.randint(2, 5)
        integrand = _join_terms([_poly_term(m, 1), _poly_term(b, 0)])
        answer = (0.5 * m * ((c * c) - (a * a))) + (b * (c - a))
        prompt = f"Compute the definite integral from {a} to {c} of ({integrand}) dx."
        return _numeric(subskill, prompt, answer, "Use antiderivatives term by term and evaluate upper minus lower.", question_type, spread=8)
    if subskill == "Accumulation and area under curves":
        rate, minutes = random.randint(2, 12), random.randint(3, 15)
        prompt = f"A constant rate is {rate} units per minute for {minutes} minutes. What is the total accumulation?"
        return _numeric(subskill, prompt, rate * minutes, "For a constant rate, accumulation is the rectangle area rate times time.", question_type)
    if subskill == "Basic integration techniques":
        new_power = random.randint(2, 5)
        result_coeff = random.randint(2, 8)
        integrand_coeff = result_coeff * new_power
        prompt = f"An antiderivative of {integrand_coeff}x^{new_power - 1} is c*x^{new_power}. What is c?"
        return _numeric(subskill, prompt, result_coeff, "Reverse the power rule by raising the power and dividing by the new power.", question_type)
    gap, width, start = random.randint(2, 9), random.randint(2, 8), random.randint(-3, 3)
    end = start + width
    prompt = f"Between y=x+{gap} and y=x from x={start} to x={end}, what is the area between the curves?"
    return _numeric("Area between curves", prompt, gap * width, "The vertical gap is constant, so area is gap times interval width.", question_type)


def _build_calculus_3(level: int, question_type: str, subskill: str) -> CalculusProblem:
    if subskill == "Partial derivative with respect to x at a point":
        a, b, c = random.randint(1, 5), random.randint(-5, 5), random.randint(1, 5)
        x0, y0 = random.randint(-3, 3), random.randint(-3, 3)
        expression = _join_terms([_poly_term(a, 2), _xy_term(b), f"{c}y^2"])
        answer = (2 * a * x0) + (b * y0)
        prompt = f"For f(x,y) = {expression}, find the partial derivative with respect to x at ({x0}, {y0})."
        return _numeric(subskill, prompt, answer, "Treat y as constant while differentiating with respect to x, then substitute.", question_type, spread=8)
    if subskill == "Gradient and directional change":
        a, b = random.randint(-6, 6) or 2, random.randint(-6, 6) or 3
        prompt = f"For f(x,y) = {a}x + {b}y, what is the x-component of the gradient?"
        return _numeric(subskill, prompt, a, "The gradient of ax + by is <a, b>.", question_type)
    h, k, peak = random.randint(-4, 4), random.randint(-4, 4), random.randint(5, 20)
    prompt = f"For f(x,y)=-(x-{h})^2-(y-{k})^2+{peak}, what is the maximum value?"
    return _numeric("Multivariable optimization", prompt, peak, "The negative squared terms are largest at zero, leaving the peak value.", question_type)


def _build_intuition_problem(skill: str, subskill: str, question_type: str, level: int) -> CalculusProblem:
    if subskill == "Average rate of change between two points":
        x1, y1, x2, y2, slope = _slope_line_points(level)
        sign = "positive" if slope > 0 else "negative" if slope < 0 else "zero"
        prompt = (
            f"Before computing the exact slope through ({x1}, {y1}) and ({x2}, {y2}), "
            "is the average rate of change positive, negative, or zero?"
        )
        choices = _text_choice_set(sign, ["positive", "negative", "zero", "undefined"]) if question_type == "mc" else None
        visual = {"kind": "slope", "x1": x1, "y1": y1, "x2": x2, "y2": y2}
        return CalculusProblem(
            prompt,
            sign,
            "Look at whether the line rises, falls, or stays flat as x increases before doing the fraction.",
            choices,
            visual,
            subskill,
            mode="intuition",
        )
    prompts = {
        "Limits and continuity": ("For a continuous function, the limit at x=a should match what?", "function value", ["slope", "area", "random sample"]),
        "Derivative rules": ("The power rule lowers the exponent by what amount?", "one", ["two", "the coefficient", "the x-value"]),
        "Derivative as slope and velocity": ("If s(t) is position, what does s'(t) represent?", "velocity", ["area", "total distance only", "midline"]),
        "Optimization": ("For a smooth function, optimization first checks endpoints and what interior points?", "critical points", ["random points", "only intercepts", "asymptotes"]),
        "Definite integral of a linear function": ("A definite integral measures signed area over what?", "interval", ["single point", "slope only", "denominator"]),
        "Accumulation and area under curves": ("Accumulation from a rate graph is represented by what?", "area under rate graph", ["x-intercept", "maximum height only", "axis label"]),
        "Basic integration techniques": ("An antiderivative should undo what operation?", "differentiation", ["factoring", "rounding", "sampling"]),
        "Area between curves": ("Area between curves uses which vertical difference?", "upper minus lower", ["lower minus upper always", "left minus right", "slope divided by run"]),
        "Partial derivative with respect to x at a point": ("While taking a partial derivative with respect to x, y is treated as what?", "constant", ["zero", "equal to x", "ignored completely"]),
        "Gradient and directional change": ("The gradient points in the direction of what?", "steepest increase", ["least x-value", "smallest sample", "period length"]),
        "Multivariable optimization": ("For a surface peak, both partial derivatives should usually do what?", "balance at zero", ["increase forever", "turn into area", "match the axes"]),
    }
    prompt, answer, distractors = prompts[subskill]
    choices = _text_choice_set(answer, distractors) if question_type == "mc" else None
    explanation = intuition_for(skill, subskill)
    text = explanation[0] if explanation else "Use the structure before calculating."
    return CalculusProblem(prompt, answer, text, choices, None, subskill, mode="intuition")


def _numeric(subskill: str, prompt: str, answer: float, explanation: str, question_type: str, visual: dict[str, object] | None = None, spread: int = 6) -> CalculusProblem:
    choices = _numeric_choices(answer, question_type, spread)
    return CalculusProblem(prompt, _format_numeric(answer), explanation, choices, visual, subskill)


def _numeric_choices(answer: float, question_type: str, spread: int) -> list[str] | None:
    if question_type != "mc":
        return None
    if abs(answer - round(answer)) < 1e-9:
        return _signed_choice_set(int(round(answer)), spread)
    return _float_choice_set(answer, float(spread))


def _slope_line_points(level: int) -> tuple[int, int, int, int, int]:
    x1 = random.randint(-5, 5)
    x2 = x1 + random.choice([n for n in range(1, 7)])
    slope = random.choice([n for n in range(-5, 6) if n != 0]) if level > 1 else random.randint(1, 4)
    y1 = random.randint(-8, 8)
    y2 = y1 + slope * (x2 - x1)
    return x1, y1, x2, y2, slope


def _poly_term(coeff: int, power: int) -> str:
    if coeff == 0:
        return ""
    sign = "-" if coeff < 0 else ""
    mag = abs(coeff)
    coeff_text = "" if mag == 1 and power > 0 else str(mag)
    if power == 0:
        return f"{coeff}"
    if power == 1:
        return f"{sign}{coeff_text}x"
    return f"{sign}{coeff_text}x^{power}"


def _xy_term(coeff: int) -> str:
    if coeff == 0:
        return ""
    sign = "-" if coeff < 0 else ""
    mag = abs(coeff)
    return f"{sign}{'' if mag == 1 else mag}xy"


def _join_terms(terms: list[str]) -> str:
    cleaned = [term for term in terms if term]
    if not cleaned:
        return "0"
    expression = cleaned[0]
    for term in cleaned[1:]:
        expression += f" - {term[1:]}" if term.startswith("-") else f" + {term}"
    return expression


def _format_numeric(value: float) -> str:
    rounded = round(value, 2)
    if abs(rounded - round(rounded)) < 1e-9:
        return str(int(round(rounded)))
    return f"{rounded:.2f}".rstrip("0").rstrip(".")


def _signed_choice_set(correct: int, spread: int) -> list[str]:
    choices = {correct}
    while len(choices) < 4:
        delta = random.randint(-spread, spread)
        if delta:
            choices.add(correct + delta)
    ordered = list(choices)
    random.shuffle(ordered)
    return [str(value) for value in ordered]


def _float_choice_set(correct: float, spread: float) -> list[str]:
    cent = int(round(correct * 100))
    choices = {round(correct, 2)}
    while len(choices) < 4:
        delta = random.randint(-round(spread * 100), round(spread * 100))
        if delta:
            choices.add(round((cent + delta) / 100, 2))
    ordered = list(choices)
    random.shuffle(ordered)
    return [_format_numeric(value) for value in ordered]


def _text_choice_set(correct: str, distractors: list[str]) -> list[str]:
    choices = [correct]
    for option in distractors:
        if option != correct and option not in choices:
            choices.append(option)
        if len(choices) == 4:
            break
    random.shuffle(choices)
    return choices
