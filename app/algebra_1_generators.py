from __future__ import annotations

import math
import random

from .algebra_1_linear import (
    ALGEBRA_1_LINEAR_SUBSKILLS,
    LINEAR_KHAN_URL_BY_SUBSKILL,
    build_linear_problem,
)
from .algebra_1_polynomials import (
    ALGEBRA_1_POLYNOMIAL_SUBSKILLS,
    POLYNOMIAL_KHAN_URL_BY_SUBSKILL,
    build_polynomial_problem,
)
from .algebra_1_systems import (
    ALGEBRA_1_SYSTEM_SUBSKILLS,
    SYSTEMS_KHAN_URL_BY_SUBSKILL,
    build_systems_problem,
)

ALGEBRA_1_SUBSKILLS = (
    "Algebra foundations",
    "Solving equations & inequalities",
    "Working with units",
    "Linear equations & graphs",
    "Forms of linear equations",
    *ALGEBRA_1_LINEAR_SUBSKILLS,
    *ALGEBRA_1_SYSTEM_SUBSKILLS,
    "Inequalities (systems & graphs)",
    "Functions",
    "Sequences",
    "Absolute value & piecewise functions",
    "Function transformations",
    "Exponents & radicals",
    "Radicals and rational exponents",
    "Exponential growth & decay",
    *ALGEBRA_1_POLYNOMIAL_SUBSKILLS,
    "Quadratic functions & equations",
    "Completing the square",
    "Quadratic formula",
    "Irrational numbers",
)

ALGEBRA_1_KHAN_URL = "https://www.khanacademy.org/math/algebra"
ALGEBRA_1_KHAN_URL_BY_SUBSKILL = {
    **LINEAR_KHAN_URL_BY_SUBSKILL,
    **POLYNOMIAL_KHAN_URL_BY_SUBSKILL,
    **SYSTEMS_KHAN_URL_BY_SUBSKILL,
    "Completing the square": (
        "https://www.khanacademy.org/math/algebra/"
        "x2f8bb11595b61c86:quadratic-functions-equations/"
        "x2f8bb11595b61c86:more-on-completing-square/e/completing_the_square_2"
    ),
    "Quadratic formula": (
        "https://www.khanacademy.org/math/algebra/"
        "x2f8bb11595b61c86:quadratic-functions-equations/"
        "x2f8bb11595b61c86:quadratic-formula-a1/a/quadratic-formula-review"
    ),
}


def _pick_subskill(requested_subskill: str | None, options: tuple[str, ...]) -> str:
    if requested_subskill and requested_subskill in options:
        return requested_subskill
    return random.choice(options)


def _nonzero_int(lo: int, hi: int) -> int:
    value = 0
    while value == 0:
        value = random.randint(lo, hi)
    return value


def khan_url_for(subskill: str | None) -> str:
    cleaned = (subskill or "").strip()
    if cleaned and cleaned != "Any":
        return ALGEBRA_1_KHAN_URL_BY_SUBSKILL.get(cleaned, ALGEBRA_1_KHAN_URL)
    return ALGEBRA_1_KHAN_URL


def build_algebra_1_problem(level: int, requested_subskill: str | None) -> tuple[str, float, str, str]:
    subskill = _pick_subskill(requested_subskill, ALGEBRA_1_SUBSKILLS)

    if subskill == "Algebra foundations":
        x = random.randint(-9, 9)
        a = random.randint(-7, 7)
        b = random.randint(-7, 7)
        prompt = f"Simplify and evaluate at x = {x}: {a}x + {b}x"
        answer = (a + b) * x
        explanation = "Combine like terms first, then substitute x."
        return prompt, float(answer), explanation, subskill

    if subskill == "Solving equations & inequalities":
        x = random.randint(-12, 12)
        m = _nonzero_int(-8, 8)
        b = random.randint(-12, 12)
        rhs = m * x + b
        prompt = f"Solve for x: {m}x + {b} = {rhs}"
        explanation = "Undo addition/subtraction, then divide by the coefficient."
        return prompt, float(x), explanation, subskill

    if subskill == "Working with units":
        miles = random.randint(8, 60)
        minutes = random.randint(20, 120)
        mph = round(miles / (minutes / 60.0), 1)
        prompt = f"A car travels {miles} miles in {minutes} minutes. What is the speed in mph? (1 decimal)"
        explanation = "Convert minutes to hours, then divide distance by time."
        return prompt, float(mph), explanation, subskill

    if subskill == "Linear equations & graphs":
        m = _nonzero_int(-6, 6)
        b = random.randint(-10, 10)
        x = random.randint(-6, 8)
        y = m * x + b
        prompt = f"For y = {m}x + {b}, find y when x = {x}."
        explanation = "Substitute x into the linear equation."
        return prompt, float(y), explanation, subskill

    if subskill == "Forms of linear equations":
        m = _nonzero_int(-6, 6)
        x0 = random.randint(-6, 6)
        y0 = random.randint(-8, 8)
        y = m * (x0 - 1) + y0
        prompt = (
            f"Line in point-slope form: y - {y0} = {m}(x - {x0}). "
            f"What is y when x = {x0 - 1}?"
        )
        explanation = "Point-slope form is equivalent to a linear equation; substitute x directly."
        return prompt, float(y), explanation, subskill

    if subskill in ALGEBRA_1_LINEAR_SUBSKILLS:
        return build_linear_problem(subskill)

    if subskill in ALGEBRA_1_SYSTEM_SUBSKILLS:
        return build_systems_problem(subskill)

    if subskill == "Inequalities (systems & graphs)":
        boundary = random.randint(-8, 12)
        prompt = f"Find the smallest integer x satisfying both x > {boundary} and x <= {boundary + 5}."
        explanation = "The smallest integer strictly greater than the boundary is boundary + 1."
        return prompt, float(boundary + 1), explanation, subskill

    if subskill == "Functions":
        a = _nonzero_int(-5, 5)
        b = random.randint(-9, 9)
        c = random.randint(-5, 5)
        value = a * (c**2) + b
        prompt = f"If f(x) = {a}x^2 + {b}, find f({c})."
        explanation = "Evaluate the function by substitution."
        return prompt, float(value), explanation, subskill

    if subskill == "Sequences":
        first = random.randint(-6, 12)
        step = _nonzero_int(-5, 7)
        n = random.randint(5, 15)
        term_n = first + (n - 1) * step
        prompt = f"An arithmetic sequence starts at {first} with common difference {step}. Find term {n}."
        explanation = "Use a_n = a_1 + (n - 1)d."
        return prompt, float(term_n), explanation, subskill

    if subskill == "Absolute value & piecewise functions":
        x = random.randint(-15, 15)
        shift = random.randint(-10, 10)
        value = abs(x - shift)
        prompt = f"Evaluate: |{x} - ({shift})|"
        explanation = "Absolute value is distance from zero."
        return prompt, float(value), explanation, subskill

    if subskill == "Function transformations":
        x = random.randint(-6, 6)
        shift = _nonzero_int(-5, 5)
        vertical = random.randint(-8, 8)
        value = (x - shift) ** 2 + vertical
        prompt = f"If g(x) = (x - ({shift}))^2 + {vertical}, find g({x})."
        explanation = "A horizontal shift changes the input before squaring; the vertical shift adds after."
        return prompt, float(value), explanation, subskill

    if subskill == "Exponents & radicals":
        base = random.randint(2, 15)
        prompt = f"Evaluate sqrt({base**2})."
        explanation = "The principal square root of n^2 is n for n > 0."
        return prompt, float(base), explanation, subskill

    if subskill == "Radicals and rational exponents":
        base = random.randint(2, 8)
        exponent = random.choice((2, 3))
        radicand = base**exponent
        prompt = f"Evaluate {radicand}^(1/{exponent})."
        explanation = "A rational exponent of 1/n asks for the nth root of the number."
        return prompt, float(base), explanation, subskill

    if subskill == "Exponential growth & decay":
        start = random.randint(40, 300)
        pct = random.choice([5, 8, 10, 12, 15, 20])
        years = random.randint(1, 4)
        value = round(start * ((1 + pct / 100.0) ** years), 2)
        prompt = (
            f"An amount of {start} grows by {pct}% each year for {years} years. "
            "Find the final amount (2 decimals)."
        )
        explanation = "Use A = P(1 + r)^t."
        return prompt, float(value), explanation, subskill

    if subskill in ALGEBRA_1_POLYNOMIAL_SUBSKILLS:
        return build_polynomial_problem(subskill)

    if subskill == "Quadratic functions & equations":
        r1 = random.randint(-9, 9)
        r2 = random.randint(-9, 9)
        if r2 == r1:
            r2 += 1
        b = -(r1 + r2)
        c = r1 * r2
        answer = max(r1, r2)
        prompt = f"Solve x^2 + ({b})x + ({c}) = 0. Report the larger real root."
        explanation = "Choose factors that multiply to c and add to b."
        return prompt, float(answer), explanation, subskill

    if subskill == "Completing the square":
        h = _nonzero_int(-6, 6)
        radius = random.randint(1, 8)
        b = 2 * h
        c = h**2 - radius**2
        answer = -h + radius
        prompt = (
            f"Solve by completing the square: x^2 + ({b})x + ({c}) = 0. "
            "Report the larger root."
        )
        explanation = "Move c, add (b/2)^2 to both sides, then take square roots."
        return prompt, float(answer), explanation, subskill

    if subskill == "Quadratic formula":
        lead = random.randint(1, 3)
        r1 = random.randint(-8, 8)
        r2 = random.randint(-8, 8)
        if r2 == r1:
            r2 += 1
        b = -lead * (r1 + r2)
        c = lead * r1 * r2
        answer = max(r1, r2)
        prompt = (
            f"Use the quadratic formula on {lead}x^2 + ({b})x + ({c}) = 0. "
            "Report the larger real root."
        )
        explanation = "Use b^2 - 4ac under the square root, then divide the whole numerator by 2a."
        return prompt, float(answer), explanation, subskill

    n = random.choice([2, 3, 5, 6, 7, 8, 10, 11, 12])
    approx = round(math.sqrt(n), 2)
    prompt = f"Approximate sqrt({n}) to 2 decimals."
    explanation = "Non-perfect-square roots are irrational; estimate with decimal approximation."
    return prompt, float(approx), explanation, "Irrational numbers"
