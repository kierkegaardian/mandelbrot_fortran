from __future__ import annotations

from dataclasses import dataclass
import random

from .models import ReasoningKind
from .pilot_problem import PilotProblem


@dataclass(frozen=True)
class PlaceValueCase:
    number: int
    digit: int
    place: str
    value: int
    wrong_values: tuple[int, int]


@dataclass(frozen=True)
class ComparisonCase:
    first: int
    second: int
    greater: int
    smaller: int
    decisive_place: str


def identify_place_value(kind: ReasoningKind) -> PilotProblem:
    case = _place_value_case()
    wrong_one, wrong_two = case.wrong_values
    if kind is ReasoningKind.CONCEPTUAL:
        return PilotProblem(
            f"In {case.number}, which statement correctly describes the digit {case.digit}?",
            f"{case.digit} represents {case.value}",
            f"The {case.place} place makes {case.digit} worth {case.value}.",
            (f"{case.digit} represents {wrong_one}", f"{case.digit} represents {wrong_two}"),
        )
    if kind is ReasoningKind.TRANSFER:
        return PilotProblem(
            f"A learner says the digit {case.digit} in {case.number} is worth {wrong_one}. "
            "Correct the place-value error and give the digit's value.",
            str(case.value),
            f"Read the {case.place} place: {case.digit} is worth {case.value}.",
            (str(wrong_one), str(wrong_two)),
        )
    if kind is ReasoningKind.APPLICATION:
        return PilotProblem(
            f"A school records {case.number} library visits. Select a place-value model and find what "
            f"the digit {case.digit} contributes. Answer model; result.",
            f"place-value decomposition; {case.value}",
            f"Decompose the count by place; the {case.place} digit contributes {case.value}.",
            (f"digit-only count; {wrong_one}", f"wrong-place model; {wrong_two}"),
        )
    return PilotProblem(
        f"What value does the digit {case.digit} have in {case.number}?",
        str(case.value),
        f"The digit is in the {case.place} place, so its value is {case.value}.",
        (str(wrong_one), str(wrong_two)),
    )


def compare_place_values(kind: ReasoningKind) -> PilotProblem:
    case = _comparison_case(force_tens=kind is ReasoningKind.TRANSFER)
    if kind is ReasoningKind.CONCEPTUAL:
        return PilotProblem(
            f"Which method correctly compares {case.first} and {case.second}?",
            "compare from the leftmost place where they differ",
            f"The {case.decisive_place} place decides before any place to its right.",
            ("compare the ones digits first", "choose the number with the larger last digit"),
        )
    if kind is ReasoningKind.TRANSFER:
        return PilotProblem(
            f"A learner compares the ones digits first and chooses {case.smaller} as greater than "
            f"{case.greater}. Diagnose the error and give the correct greater number.",
            str(case.greater),
            f"Compare the tens first; {case.greater} has more tens than {case.smaller}.",
            (str(case.smaller), "equal"),
        )
    if kind is ReasoningKind.APPLICATION:
        return PilotProblem(
            f"Two classes logged {case.first} and {case.second} reading minutes. Select a comparison "
            "model and identify the greater count. Answer model; result.",
            f"leftmost-place comparison; {case.greater}",
            f"Compare from the left; the {case.decisive_place} place makes {case.greater} greater.",
            (f"ones-digit comparison; {case.smaller}", "same-digit-count model; equal"),
        )
    return PilotProblem(
        f"Which number is greater: {case.first} or {case.second}?",
        str(case.greater),
        f"Compare from the left; the first difference is in the {case.decisive_place} place.",
        (str(case.smaller), "equal"),
    )


def _place_value_case() -> PlaceValueCase:
    place = random.choice(("ones", "tens", "hundreds"))
    if place == "hundreds":
        digit = 1
        number = 100 + random.randint(0, 1) * 10 + random.randint(1, 9)
        return PlaceValueCase(number, digit, place, 100, (1, 10))
    if place == "tens":
        digit = random.randint(1, 9)
        number = digit * 10 + random.randint(1, 9)
        return PlaceValueCase(number, digit, place, digit * 10, (digit, digit * 100))
    digit = random.randint(1, 9)
    number = random.randint(1, 9) * 10 + digit
    return PlaceValueCase(number, digit, place, digit, (digit * 10, digit * 100))


def _comparison_case(*, force_tens: bool = False) -> ComparisonCase:
    decisive_place = "tens" if force_tens else random.choice(("ones", "tens", "hundreds"))
    if decisive_place == "hundreds":
        greater = 100 + random.randint(0, 19)
        smaller = random.randint(80, 99)
    elif decisive_place == "tens":
        greater_tens = random.randint(2, 9)
        smaller_tens = random.randint(1, greater_tens - 1)
        greater = greater_tens * 10 + random.randint(0, 3)
        smaller = smaller_tens * 10 + random.randint(6, 9)
    else:
        tens = random.randint(1, 9)
        greater_ones = random.randint(5, 9)
        smaller_ones = random.randint(0, greater_ones - 1)
        greater = tens * 10 + greater_ones
        smaller = tens * 10 + smaller_ones
    if random.choice((True, False)):
        return ComparisonCase(greater, smaller, greater, smaller, decisive_place)
    return ComparisonCase(smaller, greater, greater, smaller, decisive_place)
