from __future__ import annotations

import random


PRE_ALGEBRA_SUBSKILLS = (
    "Integer and fraction fluency",
    "Order of operations",
    "Expressions and variables",
    "One-step equations",
    "Two-step equations and inequalities",
    "Ratios, rates, and proportional relationships",
    "Percent problems",
    "Exponents, roots, and scientific notation",
    "Coordinate plane and function tables",
)


def _pick_subskill(requested_subskill: str | None, options: tuple[str, ...]) -> str:
    if requested_subskill and requested_subskill in options:
        return requested_subskill
    return random.choice(options)


def _nonzero_int(lo: int, hi: int) -> int:
    value = 0
    while value == 0:
        value = random.randint(lo, hi)
    return value


def _integer_fraction_problem(level: int) -> tuple[str, float, str]:
    if random.choice([True, False]):
        a = random.randint(-25, 25)
        b = random.randint(-20, 20)
        if random.choice([True, False]):
            prompt = f"Evaluate: {a} + ({b})"
            answer = a + b
            explanation = "Treat signed addition as movement on a number line."
        else:
            prompt = f"Evaluate: {a} - ({b})"
            answer = a - b
            explanation = "Subtracting a negative is adding a positive."
        return prompt, float(answer), explanation

    denominator = random.choice([2, 4, 5, 8, 10, 20, 25, 50])
    if level <= 1:
        numerator = random.randint(1, denominator - 1)
    elif level == 2:
        numerator = random.randint(1, denominator * 2 - 1)
    else:
        numerator = random.randint(1, denominator * 3 - 1)
    if numerator % denominator == 0:
        numerator = max(1, numerator - 1)
    decimal_value = round(numerator / denominator, 2)
    prompt = f"Convert {numerator}/{denominator} to a decimal."
    explanation = "A fraction is numerator divided by denominator."
    return prompt, float(decimal_value), explanation


def _order_problem(level: int) -> tuple[str, float, str]:
    a = random.randint(-12, 12)
    b = random.randint(-12, 12)
    c = random.randint(-8, 8)
    if c == 0:
        c = 1
    if level <= 1:
        expression = f"({a} + {b}) * {c}"
        answer = (a + b) * c
    elif level == 2:
        d = random.randint(-12, 12)
        expression = f"{a} - ({b} * {c}) + {d}"
        answer = a - (b * c) + d
    else:
        d = random.randint(-6, 6)
        expression = f"({a} + {b}) * {c} - ({d} * {d})"
        answer = (a + b) * c - (d * d)
    prompt = f"Evaluate: {expression}"
    explanation = "Resolve parentheses first, then multiplication, then addition/subtraction."
    return prompt, float(answer), explanation


def _expression_variable_problem(level: int) -> tuple[str, float, str]:
    x_value = random.randint(-6, 9)
    if level <= 1:
        coeff = _nonzero_int(-6, 6)
        bias = random.randint(-12, 12)
        prompt = f"Evaluate {coeff}x + ({bias}) when x = {x_value}."
        answer = coeff * x_value + bias
        explanation = "Substitute the value for x, then simplify."
        return prompt, float(answer), explanation

    a = _nonzero_int(-5, 5)
    b = _nonzero_int(-5, 5)
    c = random.randint(-10, 10)
    prompt = f"Simplify and evaluate ({a}x) + ({b}x) + ({c}) when x = {x_value}."
    answer = (a + b) * x_value + c
    explanation = "Combine like terms first, then substitute the value for x."
    return prompt, float(answer), explanation


def _one_step_equation_problem() -> tuple[str, float, str]:
    solution = random.randint(-15, 18)
    mode = random.choice(("add", "subtract", "multiply", "divide"))
    if mode == "add":
        offset = random.randint(-12, 12)
        rhs = solution + offset
        prompt = f"Solve for x: x + ({offset}) = {rhs}"
        explanation = "Undo the addition to isolate x."
        return prompt, float(solution), explanation
    if mode == "subtract":
        offset = random.randint(-12, 12)
        rhs = solution - offset
        prompt = f"Solve for x: x - ({offset}) = {rhs}"
        explanation = "Undo the subtraction to isolate x."
        return prompt, float(solution), explanation
    if mode == "multiply":
        coeff = _nonzero_int(-9, 9)
        rhs = coeff * solution
        prompt = f"Solve for x: {coeff}x = {rhs}"
        explanation = "Divide both sides by the coefficient."
        return prompt, float(solution), explanation

    divisor = random.choice([2, 3, 4, 5, 6, 8, 10])
    rhs = solution / divisor
    prompt = f"Solve for x: x/{divisor} = {rhs:.2f}"
    explanation = "Multiply both sides by the divisor."
    return prompt, float(solution), explanation


def _two_step_problem(level: int) -> tuple[str, float, str]:
    if level >= 2 and random.choice([True, False]):
        coeff = random.choice([2, 3, 4, 5, 6])
        boundary = random.randint(-12, 10)
        rhs = coeff * boundary + random.randint(1, coeff)
        prompt = f"Find the smallest integer x satisfying {coeff}x + {rhs - coeff * boundary} > {rhs}."
        explanation = "First isolate x, then choose the least integer that makes the inequality true."
        smallest = boundary + 1
        return prompt, float(smallest), explanation

    solution = random.randint(-12, 14)
    coeff = _nonzero_int(-8, 8)
    bias = random.randint(-15, 15)
    rhs = coeff * solution + bias
    prompt = f"Solve for x: {coeff}x + ({bias}) = {rhs}"
    explanation = "Undo addition/subtraction first, then divide by the coefficient."
    return prompt, float(solution), explanation


def _ratio_problem(level: int) -> tuple[str, float, str]:
    if random.choice([True, False]):
        a = random.randint(2, 12)
        b = random.randint(3, 14)
        scale = random.randint(2, 5)
        prompt = f"Complete the proportion: {a}/{b} = x/{b * scale}"
        answer = a * scale
        explanation = "Equivalent ratios scale both parts by the same factor."
        return prompt, float(answer), explanation

    unit_rate = random.randint(2, 16)
    quantity = random.randint(3, 18 if level >= 2 else 12)
    total = unit_rate * quantity
    prompt = f"At ${unit_rate} per notebook, what is the total cost for {quantity} notebooks?"
    explanation = "A unit rate multiplies by the number of groups to get the total."
    return prompt, float(total), explanation


def _percent_problem(level: int) -> tuple[str, float, str]:
    mode = random.choice(("part", "percent_of", "change"))
    if mode == "part":
        base = random.randint(40, 240)
        percent = random.choice([5, 10, 12, 15, 20, 25, 30, 40, 45, 50, 60, 75])
        answer = round(base * percent / 100.0, 2)
        prompt = f"What is {percent}% of {base}?"
        explanation = "Convert the percent to a decimal, then multiply by the whole."
        return prompt, float(answer), explanation

    if mode == "percent_of":
        whole = random.randint(20, 250)
        percent = random.choice([10, 20, 25, 30, 40, 50, 60, 75, 80])
        part = round(whole * percent / 100.0, 2)
        prompt = f"{part:.2f} is what percent of {whole}? Enter the percent number."
        explanation = "Divide the part by the whole, then convert to a percent."
        return prompt, float(percent), explanation

    original = random.randint(20, 140)
    delta = random.randint(5, 40)
    new_value = original + delta if random.choice([True, False]) else original - delta
    answer = round((abs(new_value - original) / original) * 100.0, 2)
    prompt = f"What is the percent change from {original} to {new_value}? Enter the percent number."
    explanation = "Percent change is change divided by the original amount."
    return prompt, float(answer), explanation


def _exponent_problem(level: int) -> tuple[str, float, str]:
    mode = random.choice(("power", "root", "scientific"))
    if mode == "power":
        base = random.randint(2, 9)
        exponent = random.randint(2, 4 if level <= 2 else 5)
        prompt = f"Evaluate: {base}^{exponent}"
        explanation = "Exponents mean repeated multiplication."
        return prompt, float(base**exponent), explanation

    if mode == "root":
        base = random.choice([4, 9, 16, 25, 36, 49, 64, 81])
        prompt = f"Evaluate sqrt({base})."
        explanation = "A square root asks for the positive number whose square is the original value."
        return prompt, float(int(base**0.5)), explanation

    coefficient = round(random.choice([1.2, 2.077, 5.301, 7.45, 9.08]), 3)
    exponent = random.choice([-5, -4, -3, -2, 4, 5, 6, 7])
    prompt = (
        f"In scientific notation, {coefficient} x 10^{exponent} uses what exponent on 10?"
    )
    explanation = "Scientific notation writes a number as a coefficient times a power of 10."
    return prompt, float(exponent), explanation


def _coordinate_function_problem(level: int) -> tuple[str, float, str]:
    if random.choice([True, False]):
        x_coord = random.randint(-8, 8)
        while x_coord == 0:
            x_coord = random.randint(-8, 8)
        y_coord = random.randint(-8, 8)
        prompt = f"Point P is at ({x_coord}, {y_coord}). How far is P from the y-axis?"
        explanation = "Distance from the y-axis is the absolute value of the x-coordinate."
        return prompt, float(abs(x_coord)), explanation

    slope = _nonzero_int(-5, 5)
    intercept = random.randint(-8, 8)
    x_value = random.randint(-4, 6 if level >= 2 else 4)
    answer = slope * x_value + intercept
    prompt = f"A function table follows y = {slope}x + ({intercept}). What is y when x = {x_value}?"
    explanation = "Use the rule to map the input x to its output y."
    return prompt, float(answer), explanation


def build_pre_algebra_problem(level: int, requested_subskill: str | None) -> tuple[str, float, str, str]:
    subskill = _pick_subskill(requested_subskill, PRE_ALGEBRA_SUBSKILLS)

    if subskill == "Integer and fraction fluency":
        prompt, answer, explanation = _integer_fraction_problem(level)
        return prompt, answer, explanation, subskill

    if subskill == "Order of operations":
        prompt, answer, explanation = _order_problem(level)
        return prompt, answer, explanation, subskill

    if subskill == "Expressions and variables":
        prompt, answer, explanation = _expression_variable_problem(level)
        return prompt, answer, explanation, subskill

    if subskill == "One-step equations":
        prompt, answer, explanation = _one_step_equation_problem()
        return prompt, answer, explanation, subskill

    if subskill == "Two-step equations and inequalities":
        prompt, answer, explanation = _two_step_problem(level)
        return prompt, answer, explanation, subskill

    if subskill == "Ratios, rates, and proportional relationships":
        prompt, answer, explanation = _ratio_problem(level)
        return prompt, answer, explanation, subskill

    if subskill == "Percent problems":
        prompt, answer, explanation = _percent_problem(level)
        return prompt, answer, explanation, subskill

    if subskill == "Exponents, roots, and scientific notation":
        prompt, answer, explanation = _exponent_problem(level)
        return prompt, answer, explanation, subskill

    prompt, answer, explanation = _coordinate_function_problem(level)
    return prompt, answer, explanation, "Coordinate plane and function tables"
