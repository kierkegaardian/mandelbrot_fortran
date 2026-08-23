from __future__ import annotations

import math
import random

ALGEBRA_2_SUBSKILLS = (
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
)

ALGEBRA_2_KHAN_URL = "https://www.khanacademy.org/math/algebra2"
ALGEBRA_2_KHAN_URL_BY_SUBSKILL = {
    "Polynomial arithmetic": "https://www.khanacademy.org/math/algebra2/x2ec2f6f830c9fb89:poly-arithmetic",
    "Complex numbers": "https://www.khanacademy.org/math/algebra2/x2ec2f6f830c9fb89:complex",
    "Polynomial factorization": "https://www.khanacademy.org/math/algebra2/x2ec2f6f830c9fb89:poly-factor",
    "Polynomial division": "https://www.khanacademy.org/math/algebra2/x2ec2f6f830c9fb89:poly-div",
    "Polynomial graphs": "https://www.khanacademy.org/math/algebra2/x2ec2f6f830c9fb89:poly-graphs",
    "Domain and range": "https://www.khanacademy.org/math/algebra2/x2ec2f6f830c9fb89:func-domain-range",
    "Inverse and composition": "https://www.khanacademy.org/math/algebra2/x2ec2f6f830c9fb89:composite-and-inverse-functions",
    "Rational exponents and radicals": "https://www.khanacademy.org/math/algebra2/x2ec2f6f830c9fb89:radical-rational-exponents",
    "Exponential models": "https://www.khanacademy.org/math/algebra2/x2ec2f6f830c9fb89:exp",
    "Logarithms": "https://www.khanacademy.org/math/algebra2/x2ec2f6f830c9fb89:logs",
    "Transformations of functions": "https://www.khanacademy.org/math/algebra2/x2ec2f6f830c9fb89:transformations",
    "Equations": "https://www.khanacademy.org/math/algebra2/x2ec2f6f830c9fb89:advanced-equations",
    "Trigonometry": "https://www.khanacademy.org/math/algebra2/x2ec2f6f830c9fb89:trig",
    "Modeling": "https://www.khanacademy.org/math/algebra2/x2ec2f6f830c9fb89:modeling",
    "Rational expressions": "https://www.khanacademy.org/math/algebra2/x2ec2f6f830c9fb89:poly-div/x2ec2f6f830c9fb89:rational-expressions",
    "Rational functions": "https://www.khanacademy.org/math/algebra2/x2ec2f6f830c9fb89:rational",
    "Sequences and series": "https://www.khanacademy.org/math/algebra2/x2ec2f6f830c9fb89:seq",
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
        return ALGEBRA_2_KHAN_URL_BY_SUBSKILL.get(cleaned, ALGEBRA_2_KHAN_URL)
    return ALGEBRA_2_KHAN_URL


def build_algebra_2_problem(level: int, requested_subskill: str | None) -> tuple[str, float, str, str]:
    subskill = _pick_subskill(requested_subskill, ALGEBRA_2_SUBSKILLS)

    if subskill == "Polynomial arithmetic":
        a = _nonzero_int(-5, 6)
        b = random.randint(-8, 8)
        c = random.randint(-8, 8)
        x = random.randint(-4, 5)
        value = (a * (x**2)) + (b * x) + c
        prompt = f"Evaluate P({x}) for P(x) = {a}x^2 + {b}x + {c}."
        explanation = "Substitute x and combine terms carefully."
        return prompt, float(value), explanation, subskill

    if subskill == "Complex numbers":
        n = random.randint(1, 40)
        cycle = [1, -1, -1, 1]
        answer = cycle[(n - 1) % 4]
        prompt = f"What is the real value of i^{2*n}?"
        explanation = "Powers of i repeat every 4; even powers are real."
        return prompt, float(answer), explanation, subskill

    if subskill == "Polynomial factorization":
        r1 = random.randint(-8, 8)
        r2 = random.randint(-8, 8)
        if r2 == r1:
            r2 += 2
        b = -(r1 + r2)
        c = r1 * r2
        prompt = f"For x^2 + ({b})x + ({c}) = 0, report one integer root (the larger one)."
        explanation = "Find two numbers with product c and sum b."
        return prompt, float(max(r1, r2)), explanation, subskill

    if subskill == "Polynomial division":
        r = random.randint(-6, 6)
        x_val = random.randint(-4, 7)
        quotient_at_x = x_val + r
        prompt = (
            f"If (x^2 - {r**2})/(x - ({r})) simplifies to x + {r}, "
            f"what is the value at x = {x_val}?"
        )
        explanation = "Use difference of squares, then substitute x."
        return prompt, float(quotient_at_x), explanation, subskill

    if subskill == "Polynomial graphs":
        a = _nonzero_int(-4, 5)
        c = random.randint(-12, 12)
        prompt = f"For y = {a}x^3 + {c}, what is the y-intercept?"
        explanation = "The y-intercept is y when x = 0."
        return prompt, float(c), explanation, subskill

    if subskill == "Domain and range":
        excluded = random.randint(-8, 8)
        prompt = f"For f(x) = 1/(x - ({excluded})), what x-value is excluded from the domain?"
        explanation = "A rational function's denominator cannot equal zero."
        return prompt, float(excluded), explanation, subskill

    if subskill == "Inverse and composition":
        x = random.randint(-8, 8)
        a = _nonzero_int(-6, 6)
        b = random.randint(-12, 12)
        output = a * x + b
        prompt = f"If f(x) = {a}x + ({b}), what is f^-1({output})?"
        explanation = "An inverse function reverses the original function's input-output pairing."
        return prompt, float(x), explanation, subskill

    if subskill == "Rational exponents and radicals":
        base = random.choice([4, 9, 16, 25, 36, 49, 64])
        prompt = f"Evaluate {base}^(1/2)."
        explanation = "An exponent of 1/2 means square root."
        return prompt, float(int(round(math.sqrt(base)))), explanation, subskill

    if subskill == "Exponential models":
        start = random.randint(20, 180)
        factor = random.choice([1.2, 1.3, 1.5, 0.8, 0.75])
        steps = random.randint(2, 5)
        value = round(start * (factor**steps), 2)
        prompt = (
            f"A quantity starts at {start} and is multiplied by {factor} each step. "
            f"Find the value after {steps} steps (2 decimals)."
        )
        explanation = "Repeated multiplication is modeled by exponentials."
        return prompt, float(value), explanation, subskill

    if subskill == "Logarithms":
        base = random.choice([2, 3, 4, 5, 10])
        power = random.randint(1, 6)
        prompt = f"Compute log base {base} of {base**power}."
        explanation = "log_b(b^k) = k."
        return prompt, float(power), explanation, subskill

    if subskill == "Transformations of functions":
        x = random.randint(-5, 7)
        h = random.randint(-6, 6)
        k = random.randint(-8, 8)
        a = _nonzero_int(-4, 4)
        value = a * ((x - h) ** 2) + k
        prompt = f"Evaluate g({x}) if g(x) = {a}(x - ({h}))^2 + {k}."
        explanation = "Apply shifts/scaling in the transformed function, then substitute."
        return prompt, float(value), explanation, subskill

    if subskill == "Equations":
        root = random.randint(-10, 10)
        a = _nonzero_int(-9, 9)
        b = random.randint(-15, 15)
        rhs = a * root + b
        prompt = f"Solve for x: {a}x + {b} = {rhs}"
        explanation = "Isolate x via inverse operations."
        return prompt, float(root), explanation, subskill

    if subskill == "Trigonometry":
        opposite, adjacent, _hyp = random.choice(((3, 4, 5), (5, 12, 13), (8, 15, 17)))
        value = round(opposite / adjacent, 3)
        prompt = (
            f"In a right triangle, opposite = {opposite} and adjacent = {adjacent}. "
            "Find tan(theta) to 3 decimals."
        )
        explanation = "tan(theta) = opposite/adjacent."
        return prompt, float(value), explanation, subskill

    if subskill == "Modeling":
        x = random.randint(5, 20)
        a = random.randint(1, 4)
        b = random.randint(20, 80)
        c = random.randint(100, 300)
        revenue = -(a * (x**2)) + (b * x) + c
        prompt = f"A model gives revenue R(x) = -{a}x^2 + {b}x + {c}. Find R({x})."
        explanation = "Modeling means evaluating the given function in context."
        return prompt, float(revenue), explanation, subskill

    if subskill == "Rational expressions":
        a = random.randint(2, 9)
        b = random.randint(2, 9)
        prompt = (
            f"Simplify ((x + {a})(x + {b}))/(x + {a}). "
            "What constant remains in the simplified factor x + ?"
        )
        explanation = "Cancel the common nonzero factor, then keep the remaining factor."
        return prompt, float(b), explanation, subskill

    if subskill == "Sequences and series":
        first = random.randint(-5, 12)
        difference = _nonzero_int(-4, 6)
        terms = random.randint(4, 12)
        total = (terms * ((2 * first) + ((terms - 1) * difference))) / 2
        prompt = (
            f"An arithmetic series has first term {first}, common difference {difference}, "
            f"and {terms} terms. Find the sum."
        )
        explanation = "An arithmetic-series sum averages the first and last terms, then multiplies by the count."
        return prompt, float(total), explanation, subskill

    denom_shift = random.choice([2, 3, 4, 5, 6])
    x = random.choice([n for n in range(-8, 9) if n != denom_shift])
    numer_a = _nonzero_int(-6, 6)
    numer_b = random.randint(-10, 10)
    value = (numer_a * x + numer_b) / (x - denom_shift)
    prompt = (
        f"Evaluate f({x}) for f(x) = ({numer_a}x + {numer_b})/(x - ({denom_shift})). "
        "Round to 3 decimals if needed."
    )
    explanation = "Substitute x while checking denominator is nonzero."
    return prompt, float(round(value, 3)), explanation, "Rational functions"
