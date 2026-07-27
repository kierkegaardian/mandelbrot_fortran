from __future__ import annotations

from dataclasses import dataclass
import random

from .models import ReasoningKind
from .pilot_problem import PilotProblem


@dataclass(frozen=True)
class WordProblemCase:
    prompt: str
    equation: str
    answer: int
    model: str
    wrong_equation: str
    wrong_answer: int
    wrong_model: str


def subtraction(kind: ReasoningKind) -> PilotProblem:
    start, removed, left = _subtraction_values()
    if kind is ReasoningKind.CONCEPTUAL:
        return PilotProblem(
            f"There are {start} counters. {removed} are removed. Which equation models what is left?",
            f"{start} - {removed} = {left}",
            "Subtraction separates the removed part from the starting whole.",
            (f"{start} + {removed} = {start + removed}", f"{removed} - {start} = {removed - start}"),
        )
    if kind is ReasoningKind.TRANSFER:
        return PilotProblem(
            f"A learner solves {start} - {removed} by adding and answers {start + removed}. "
            "Diagnose the operation error and give the correct difference.",
            str(left),
            f"Count back {removed} from {start}; the difference is {left}.",
            (str(start + removed), str(removed)),
        )
    if kind is ReasoningKind.APPLICATION:
        return PilotProblem(
            f"A game begins with {start} tokens and spends {removed}. Select a model and find how many "
            "remain. Answer model; result.",
            f"take-away subtraction; {left}",
            "Spending removes a part from the starting amount.",
            (f"joining addition; {start + removed}", f"reverse subtraction; {removed - start}"),
        )
    return PilotProblem(
        f"Compute {start} - {removed}.",
        str(left),
        f"Start at {start} and count back {removed} steps to reach {left}.",
        (str(start + removed), str(removed)),
    )


def missing_addend(kind: ReasoningKind) -> PilotProblem:
    known, missing, total = _missing_addend_values()
    if kind is ReasoningKind.CONCEPTUAL:
        return PilotProblem(
            f"Which equation shows the missing part in {known} + ? = {total}?",
            f"{known} + {missing} = {total}",
            "The missing addend is the part between the known amount and the whole.",
            (f"{known} + {total} = {known + total}", f"{total} - {missing} = {missing}"),
        )
    if kind is ReasoningKind.TRANSFER:
        return PilotProblem(
            f"A learner adds every visible number in {known} + ? = {total} and answers {known + total}. "
            "Correct the whole-versus-part error and give the missing addend.",
            str(missing),
            f"Count from {known} up to {total}; the missing part is {missing}.",
            (str(known + total), str(known)),
        )
    if kind is ReasoningKind.APPLICATION:
        return PilotProblem(
            f"A shelf has {known} books and needs {total}. Select a model and find how many more books "
            "are needed. Answer model; result.",
            f"missing-part addition; {missing}",
            f"The unknown part completes {known} + ? = {total}.",
            (f"join-all addition; {known + total}", f"known-part only; {known}"),
        )
    return PilotProblem(
        f"Find the missing addend: {known} + ? = {total}.",
        str(missing),
        f"Use the inverse relationship: {total} - {known} = {missing}.",
        (str(known + total), str(known)),
    )


def word_problem(kind: ReasoningKind) -> PilotProblem:
    case = _word_problem_case()
    if kind is ReasoningKind.CONCEPTUAL:
        return PilotProblem(
            f"{case.prompt} Which equation models the story?",
            case.equation,
            f"The relationship is {case.model}, so {case.equation}.",
            (case.wrong_equation, f"{case.answer} + 1 = {case.answer + 1}"),
        )
    if kind is ReasoningKind.TRANSFER:
        return PilotProblem(
            f"{case.prompt} A learner uses {case.wrong_equation} and gets {case.wrong_answer}. "
            "Diagnose the story-model error and give the correct answer.",
            str(case.answer),
            f"Name the relationship before calculating: use {case.model} to get {case.answer}.",
            (str(case.wrong_answer), str(case.answer + 1)),
        )
    if kind is ReasoningKind.APPLICATION:
        return PilotProblem(
            f"{case.prompt} Select a model and solve. Answer model; result.",
            f"{case.model}; {case.answer}",
            f"The story describes {case.model}, represented by {case.equation}.",
            (f"{case.wrong_model}; {case.wrong_answer}", f"number-picking; {case.answer + 1}"),
        )
    return PilotProblem(
        case.prompt,
        str(case.answer),
        f"Translate the story as {case.equation}; the answer is {case.answer}.",
        (str(case.wrong_answer), str(case.answer + 1)),
    )


def _subtraction_values() -> tuple[int, int, int]:
    while True:
        start = random.randint(3, 9)
        removed = random.randint(1, start - 1)
        left = start - removed
        if left != removed:
            return start, removed, left


def _missing_addend_values() -> tuple[int, int, int]:
    while True:
        known = random.randint(1, 9)
        missing = random.randint(1, 9)
        if known != missing:
            return known, missing, known + missing


def _word_problem_case() -> WordProblemCase:
    relationship = random.choice(("join", "separate", "compare"))
    if relationship == "join":
        first, second = random.randint(1, 9), random.randint(1, 9)
        total = first + second
        return WordProblemCase(
            f"Lena has {first} blue beads and {second} red beads. How many beads altogether?",
            f"{first} + {second} = {total}",
            total,
            "joining addition",
            f"{max(first, second)} - {min(first, second)} = {abs(first - second)}",
            abs(first - second),
            "take-away subtraction",
        )
    if relationship == "separate":
        start, removed, left = _subtraction_values()
        return WordProblemCase(
            f"Noah has {start} stickers and gives away {removed}. How many stickers remain?",
            f"{start} - {removed} = {left}",
            left,
            "take-away subtraction",
            f"{start} + {removed} = {start + removed}",
            start + removed,
            "joining addition",
        )
    smaller = random.randint(1, 8)
    difference = random.randint(1, 9)
    larger = smaller + difference
    return WordProblemCase(
        f"Ari reads {larger} pages and Bea reads {smaller}. How many more pages does Ari read?",
        f"{larger} - {smaller} = {difference}",
        difference,
        "comparison subtraction",
        f"{larger} + {smaller} = {larger + smaller}",
        larger + smaller,
        "joining addition",
    )
