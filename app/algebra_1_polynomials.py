from __future__ import annotations

import random

ALGEBRA_1_POLYNOMIAL_SUBSKILLS = (
    "Polynomial arithmetic",
    "Factoring basics",
    "Quadratics: Multiplying & factoring",
    "Quadratic factoring by grouping",
    "Difference of squares",
)

POLYNOMIAL_KHAN_URL_BY_SUBSKILL = {
    "Polynomial arithmetic": "https://www.khanacademy.org/math/algebra-home/alg-polynomials",
    "Factoring basics": (
        "https://www.khanacademy.org/math/algebra/"
        "x2f8bb11595b61c86:quadratics-multiplying-factoring/"
        "x2f8bb11595b61c86:factor-quadratics-intro/e/factoring_polynomials_1"
    ),
    "Quadratics: Multiplying & factoring": (
        "https://www.khanacademy.org/math/algebra/"
        "x2f8bb11595b61c86:quadratics-multiplying-factoring"
    ),
    "Quadratic factoring by grouping": (
        "https://www.khanacademy.org/math/algebra/"
        "x2f8bb11595b61c86:quadratics-multiplying-factoring/"
        "x2f8bb11595b61c86:factor-quadratics-grouping/"
        "e/factoring_polynomials_by_grouping_1"
    ),
    "Difference of squares": (
        "https://www.khanacademy.org/math/algebra/"
        "x2f8bb11595b61c86:quadratics-multiplying-factoring/"
        "x2f8bb11595b61c86:factor-difference-squares/"
        "e/factoring_difference_of_squares_2"
    ),
}


def _poly(a: int, b: int, c: int) -> str:
    return f"{a}x^2 + ({b})x + ({c})"


def build_polynomial_problem(subskill: str) -> tuple[str, float, str, str]:
    if subskill == "Polynomial arithmetic":
        a = b = c = d = e = f = 0
        op = "+"
        answer = 0
        while answer == 0:
            a = random.randint(-6, 8)
            b = random.randint(-9, 9)
            c = random.randint(-12, 12)
            d = random.randint(-6, 8)
            e = random.randint(-9, 9)
            f = random.randint(-12, 12)
            subtract = random.choice((False, True))
            op = "-" if subtract else "+"
            answer = a - d if subtract else a + d
        prompt = (
            f"Simplify ({_poly(a, b, c)}) {op} ({_poly(d, e, f)}). "
            "What is the coefficient of x^2?"
        )
        explanation = "Combine like terms only; x^2 terms combine with x^2 terms."
        return prompt, float(answer), explanation, subskill

    if subskill == "Factoring basics":
        m = random.choice([value for value in range(-9, 10) if value != 0])
        n = random.choice([value for value in range(-9, 10) if value not in (0, m)])
        b = m + n
        c = m * n
        prompt = (
            f"Factor x^2 + ({b})x + ({c}) as (x + m)(x + n). "
            "Report the larger constant."
        )
        explanation = "Find two numbers that multiply to the constant term and add to the x-coefficient."
        return prompt, float(max(m, n)), explanation, subskill

    if subskill == "Quadratic factoring by grouping":
        lead_1 = random.randint(2, 6)
        lead_2 = random.randint(1, 6)
        while lead_2 == lead_1:
            lead_2 = random.randint(1, 6)
        constant_1 = random.choice([value for value in range(-8, 9) if value != 0])
        constant_2 = random.choice([value for value in range(-8, 9) if value != 0])
        a = lead_1 * lead_2
        b = lead_1 * constant_2 + lead_2 * constant_1
        c = constant_1 * constant_2
        answer = constant_1 if lead_1 > lead_2 else constant_2
        prompt = (
            f"Factor {a}x^2 + ({b})x + ({c}) into two binomials. "
            "Report the constant in the factor with the larger x-coefficient."
        )
        explanation = "Use the ac method to split the middle term, then factor by grouping."
        return prompt, float(answer), explanation, subskill

    if subskill == "Difference of squares":
        factor_coef = random.randint(2, 9)
        constant = random.randint(2, 12)
        a = factor_coef**2
        c = constant**2
        prompt = f"Factor {a}x^2 - {c} as (ax + b)(ax - b). What is b?"
        explanation = "A difference of squares follows A^2 - B^2 = (A + B)(A - B)."
        return prompt, float(constant), explanation, subskill

    m = n = 0
    coef = 0
    while coef == 0:
        m = random.randint(-9, 9)
        n = random.randint(-9, 9)
        coef = m + n
    prompt = f"Expand (x + {m})(x + {n}). What is the coefficient of x?"
    explanation = "The middle term comes from m*x plus n*x, so the x-coefficient is m + n."
    return prompt, float(coef), explanation, "Quadratics: Multiplying & factoring"
