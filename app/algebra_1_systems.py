from __future__ import annotations

import random

ALGEBRA_1_SYSTEM_SUBSKILLS = (
    "Systems of equations",
    "Systems by substitution",
    "Systems by elimination",
    "Graphing systems and intersections",
)

SYSTEMS_KHAN_URL_BY_SUBSKILL = {
    "Systems by substitution": (
        "https://www.khanacademy.org/math/algebra/"
        "x2f8bb11595b61c86:systems-of-equations/"
        "x2f8bb11595b61c86:solving-systems-of-equations-with-substitution"
    ),
    "Systems by elimination": (
        "https://www.khanacademy.org/math/algebra/"
        "x2f8bb11595b61c86:systems-of-equations/"
        "x2f8bb11595b61c86:solving-systems-elimination/"
        "e/systems_of_equations_with_elimination_0.5"
    ),
    "Graphing systems and intersections": (
        "https://www.khanacademy.org/math/algebra/"
        "x2f8bb11595b61c86:systems-of-equations/"
        "x2f8bb11595b61c86:introduction-to-systems-of-equations/"
        "v/solving-systems-graphically"
    ),
}


def _nonzero_int(lo: int, hi: int) -> int:
    value = 0
    while value == 0:
        value = random.randint(lo, hi)
    return value


def _linear_intersection() -> tuple[int, int, int, int, int, int]:
    x = random.randint(-6, 6)
    y = random.randint(-8, 8)
    m1 = _nonzero_int(-4, 4)
    m2 = _nonzero_int(-4, 4)
    while m2 == m1:
        m2 = _nonzero_int(-4, 4)
    b1 = y - m1 * x
    b2 = y - m2 * x
    return x, y, m1, b1, m2, b2


def build_systems_problem(subskill: str) -> tuple[str, float, str, str]:
    if subskill == "Systems of equations":
        x = random.randint(-8, 8)
        y = random.randint(-8, 8)
        eq1 = x + y
        eq2 = x - y
        prompt = f"Solve the system and report x: x + y = {eq1}, x - y = {eq2}."
        explanation = "Add the equations to eliminate y and isolate x."
        return prompt, float(x), explanation, subskill

    if subskill == "Systems by substitution":
        x, _y, m1, b1, m2, b2 = _linear_intersection()
        prompt = (
            f"Solve by substitution and report x: "
            f"y = {m1}x + ({b1}), y = {m2}x + ({b2})."
        )
        explanation = "Set the two expressions for y equal, then solve the one-variable equation."
        return prompt, float(x), explanation, subskill

    if subskill == "Systems by elimination":
        x = random.randint(-6, 6)
        y = random.randint(-6, 6)
        x_coef = _nonzero_int(-5, 5)
        y_coef_1 = _nonzero_int(-5, 5)
        y_coef_2 = _nonzero_int(-5, 5)
        while y_coef_1 + y_coef_2 == 0:
            y_coef_2 = _nonzero_int(-5, 5)
        rhs1 = x_coef * x + y_coef_1 * y
        rhs2 = -x_coef * x + y_coef_2 * y
        prompt = (
            f"Solve by elimination and report y: "
            f"{x_coef}x + ({y_coef_1})y = {rhs1}, "
            f"{-x_coef}x + ({y_coef_2})y = {rhs2}."
        )
        explanation = "Add the equations so the x-terms cancel, then divide to isolate y."
        return prompt, float(y), explanation, subskill

    x, _y, m1, b1, m2, b2 = _linear_intersection()
    prompt = (
        f"On a graph, y = {m1}x + ({b1}) and y = {m2}x + ({b2}) "
        "intersect at one point. Report the x-coordinate of the intersection."
    )
    explanation = "The solution to a graphed system is the intersection point shared by both lines."
    return prompt, float(x), explanation, "Graphing systems and intersections"
