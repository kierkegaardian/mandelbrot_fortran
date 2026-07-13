from __future__ import annotations

import random

ALGEBRA_1_LINEAR_SUBSKILLS = (
    "Slope from points",
    "Slope-intercept form",
    "Graphing linear inequalities",
)

LINEAR_KHAN_URL_BY_SUBSKILL = {
    "Slope from points": (
        "https://www.khanacademy.org/math/algebra/"
        "x2f8bb11595b61c86:linear-equations-graphs/"
        "x2f8bb11595b61c86:slope/e/slope-from-two-points"
    ),
    "Slope-intercept form": (
        "https://www.khanacademy.org/math/algebra/"
        "x2f8bb11595b61c86:forms-of-linear-equations/"
        "x2f8bb11595b61c86:intro-to-slope-intercept-form/"
        "e/slope-from-an-equation-in-slope-intercept-form"
    ),
    "Graphing linear inequalities": (
        "https://www.khanacademy.org/math/algebra/"
        "x2f8bb11595b61c86:inequalities-systems-graphs/"
        "x2f8bb11595b61c86:graphing-two-variable-inequalities/"
        "e/graphing_inequalities_2"
    ),
}


def _nonzero_int(lo: int, hi: int) -> int:
    value = 0
    while value == 0:
        value = random.randint(lo, hi)
    return value


def build_linear_problem(subskill: str) -> tuple[str, float, str, str]:
    if subskill == "Slope from points":
        x1 = random.randint(-8, 4)
        y1 = random.randint(-8, 8)
        run = _nonzero_int(1, 6)
        slope = _nonzero_int(-6, 6)
        x2 = x1 + run
        y2 = y1 + slope * run
        prompt = f"Find the slope of the line through ({x1}, {y1}) and ({x2}, {y2})."
        explanation = "Slope is change in y divided by change in x: rise over run."
        return prompt, float(slope), explanation, subskill

    if subskill == "Slope-intercept form":
        slope = _nonzero_int(-6, 6)
        intercept = _nonzero_int(-10, 10)
        prompt = f"In y = {slope}x + ({intercept}), what is y when x = 0?"
        explanation = "In y = mx + b, b is the y-intercept because it is the output when x is 0."
        return prompt, float(intercept), explanation, subskill

    boundary = 0
    while boundary == 0:
        slope = _nonzero_int(-4, 4)
        intercept = random.randint(-8, 8)
        x = random.randint(-5, 5)
        boundary = slope * x + intercept
    symbol = random.choice((">", "<"))
    prompt = (
        f"For the inequality y {symbol} {slope}x + ({intercept}), at x = {x}, "
        "what boundary y-value separates the shaded region?"
    )
    explanation = "Graph the boundary line y = mx + b first; > shades above it and < shades below it."
    return prompt, float(boundary), explanation, "Graphing linear inequalities"
