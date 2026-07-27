from __future__ import annotations

from fractions import Fraction
import random

from .models import ReasoningKind
from .pilot_problem import PilotProblem


def two_step(kind: ReasoningKind) -> PilotProblem:
    coefficient, solution, offset = random.randint(2, 6), random.randint(2, 10), random.randint(1, 9)
    total = coefficient * solution + offset
    if kind is ReasoningKind.CONCEPTUAL:
        return PilotProblem(
            f"Which operation sequence isolates x in {coefficient}x + {offset} = {total}?",
            f"subtract {offset}, then divide by {coefficient}", "Undo operations in reverse order.",
            (f"divide by {coefficient}, then subtract {offset}", f"add {offset}, then multiply by {coefficient}"),
        )
    if kind is ReasoningKind.TRANSFER:
        wrong = total // coefficient - offset
        return PilotProblem(
            f"A learner divides first and gets x = {wrong} for {coefficient}x + {offset} = {total}. Give the correct x.",
            str(solution), "Subtract the offset before dividing by the coefficient.",
            (str(wrong), str(solution + 1)),
        )
    if kind is ReasoningKind.APPLICATION:
        return PilotProblem(
            f"A club charges ${offset} plus ${coefficient} per visit. A child can spend at most ${total}. Select a model and state the greatest whole-number visits. Answer model; result.",
            f"inequality; x <= {solution}", "The at-most language creates an inequality boundary.",
            (f"equation; x = {solution}", f"inequality; x >= {solution}"),
        )
    return PilotProblem(
        f"Solve {coefficient}x + {offset} = {total}.", str(solution),
        f"Subtract {offset}, then divide by {coefficient}.",
        (str(total // coefficient - offset), str(solution + 1)),
    )


def slope(kind: ReasoningKind) -> PilotProblem:
    run = random.randint(2, 5)
    slope_value = random.choice((-3, -2, 2, 3))
    x1, y1 = random.randint(-2, 2), random.randint(-5, 5)
    x2, y2 = x1 + run, y1 + slope_value * run
    if kind is ReasoningKind.CONCEPTUAL:
        return PilotProblem(
            "Which ratio defines slope between two points?", "change in y / change in x",
            "Slope compares vertical change with horizontal change.",
            ("change in x / change in y", "y-coordinate / x-coordinate"),
        )
    if kind is ReasoningKind.TRANSFER:
        reciprocal = str(Fraction(run, y2 - y1))
        return PilotProblem(
            f"A learner uses run over rise for ({x1}, {y1}) and ({x2}, {y2}) and gets {reciprocal}. Give the correct slope.",
            str(slope_value), "Use (y2-y1)/(x2-x1) in one consistent point order.",
            (reciprocal, str(-slope_value)),
        )
    if kind is ReasoningKind.APPLICATION:
        rise, ramp_run = random.choice(((1, 4), (2, 5), (3, 8)))
        rate = str(Fraction(rise, ramp_run))
        return PilotProblem(
            f"A ramp rises {rise} m over a horizontal run of {ramp_run} m. Select the model and find its slope. Answer model; result.",
            f"linear rate; {rate}", "Ramp slope is rise divided by run.",
            (f"linear rate; {Fraction(ramp_run, rise)}", f"area model; {rate}"),
        )
    return PilotProblem(
        f"Find the slope through ({x1}, {y1}) and ({x2}, {y2}).", str(slope_value),
        f"({y2}-{y1})/({x2}-{x1}) = {slope_value}.",
        (str(Fraction(run, y2 - y1)), str(-slope_value)),
    )


def systems(kind: ReasoningKind) -> PilotProblem:
    x, y = random.randint(1, 6), random.randint(1, 6)
    if y == x:
        y = y % 6 + 1
    first, second = 2 * x + y, -2 * x + 2 * y
    if kind is ReasoningKind.CONCEPTUAL:
        return PilotProblem(
            "The x-coefficients in a system are 3 and -3. What should you do next?", "add the equations",
            "Adding makes the x-terms cancel to zero.",
            ("add without opposite coefficients", "change one sign and subtract"),
        )
    if kind is ReasoningKind.TRANSFER:
        return PilotProblem(
            f"A learner adds 2x + y = {first} and 2x - 2y = {2*x-2*y} without first making x-coefficients opposite. What correction is needed?",
            "multiply one equation so a variable has opposite coefficients", "Elimination requires opposite coefficients before addition.",
            ("add the equations as written", "divide only the constants"),
        )
    if kind is ReasoningKind.APPLICATION:
        total, revenue = x + y, 10 * x + 6 * y
        return PilotProblem(
            f"A show sold {total} tickets: adult tickets cost $10 and child tickets cost $6, for ${revenue}. Select a model and find both counts. Answer model; result.",
            f"system; {x} adults and {y} children", "The count and revenue facts form two simultaneous equations.",
            (f"single equation; {x} adults and {y} children", f"system; {y} adults and {x} children"),
        )
    return PilotProblem(
        f"Solve by elimination and report y: 2x + y = {first}, -2x + 2y = {second}.", str(y),
        f"Add the equations to get 3y = {3*y}, then divide by 3.",
        (str(3 * y), str(-y)),
    )


def congruence(kind: ReasoningKind) -> PilotProblem:
    if kind is ReasoningKind.CONCEPTUAL:
        return PilotProblem(
            "Two side pairs and the included angle are congruent. Which criterion proves triangle congruence?",
            "SAS", "The known angle is between the two known sides.", ("AAA", "SSA"),
        )
    if kind is ReasoningKind.TRANSFER:
        return PilotProblem(
            "A learner claims two triangles are congruent because all three angle pairs match. Diagnose the claim.",
            "similar, not necessarily congruent", "AAA fixes shape but not size.",
            ("congruent by AAA", "congruent by SSA"),
        )
    if kind is ReasoningKind.APPLICATION:
        return PilotProblem(
            "Two triangular bridge braces have two matching side lengths and the matching included angle. Select the proof model and conclusion. Answer model; result.",
            "SAS; triangles congruent", "SAS is sufficient and uses corresponding facts.",
            ("AAA; triangles congruent", "SSA; triangles congruent"),
        )
    return PilotProblem(
        "Three pairs of corresponding sides are congruent. Name the congruence criterion.", "SSS",
        "Three corresponding side pairs establish SSS.", ("AAA", "SSA"),
    )
