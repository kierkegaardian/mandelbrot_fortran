from __future__ import annotations

import random

from .models import ReasoningKind
from .pilot_problem import PilotProblem


DENOMINATIONS: tuple[tuple[str, int], ...] = (
    ("penny", 1),
    ("nickel", 5),
    ("dime", 10),
    ("quarter", 25),
    ("one-dollar coin", 100),
)


def coin_values(kind: ReasoningKind) -> PilotProblem:
    if kind is ReasoningKind.CONCEPTUAL:
        name, value = random.choice(DENOMINATIONS)
        wrong_one, wrong_two = _wrong_values(value)
        return PilotProblem(
            f"Which value matches one {name}?",
            f"{value} cents",
            f"A {name} has a fixed value of {value} cents.",
            (f"{wrong_one} cents", f"{wrong_two} cents"),
        )

    name, value, count, total = _collection()
    plural = _plural(name, count)
    if kind is ReasoningKind.TRANSFER:
        return PilotProblem(
            f"A learner counts {count} {plural} and says the coins are worth {count} cents. "
            "Correct the coin-count-versus-value error.",
            f"{total} cents",
            f"Each {name} is worth {value} cents, so {count} x {value} = {total} cents.",
            (f"{count} cents", f"{total} dollars"),
        )
    if kind is ReasoningKind.APPLICATION:
        return PilotProblem(
            f"A classroom coin tray has {count} {plural}. Select a model and find the total value in "
            "cents. Answer model; result.",
            f"coin-value table; {total} cents",
            f"Use coin count x cents per coin: {count} x {value} = {total} cents.",
            (f"coin-count model; {count} cents", f"dollars-as-cents model; {total} dollars"),
        )
    return PilotProblem(
        f"How many cents are {count} {plural} worth?",
        f"{total} cents",
        f"Multiply {count} coins by {value} cents per {name} to get {total} cents.",
        (f"{count} cents", f"{total} dollars"),
    )


def _collection() -> tuple[str, int, int, int]:
    name, value = random.choice(DENOMINATIONS[1:])
    max_count = min(4, 100 // value)
    count = random.randint(1, max_count)
    return name, value, count, count * value


def _wrong_values(correct: int) -> tuple[int, int]:
    wrong = [value for _, value in DENOMINATIONS if value != correct]
    chosen = random.sample(wrong, 2)
    return chosen[0], chosen[1]


def _plural(name: str, count: int) -> str:
    if count == 1:
        return name
    if name == "penny":
        return "pennies"
    return f"{name}s"
