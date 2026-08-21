from __future__ import annotations

import random

from .models import ReasoningKind
from .pilot_problem import PilotProblem


def finance(kind: ReasoningKind) -> PilotProblem:
    assets = random.randrange(600, 1300, 100)
    liabilities = random.randrange(100, 500, 50)
    if kind is ReasoningKind.CONCEPTUAL:
        return PilotProblem(
            "Which model correctly represents net worth?", "assets - liabilities",
            "Liabilities reduce the value remaining from assets.",
            ("assets + liabilities", "income - expenses"),
        )
    if kind is ReasoningKind.TRANSFER:
        income, percent = random.randrange(400, 1000, 100), random.choice((10, 20, 25))
        amount = income * percent // 100
        return PilotProblem(
            f"A learner treats {percent}% of ${income} as ${percent}. Correct the budget amount.",
            f"${amount}", "Convert the percent to a rate and multiply by the whole income.",
            (f"${percent}", f"${income - amount}"),
        )
    if kind is ReasoningKind.APPLICATION:
        worth = assets - liabilities
        return PilotProblem(
            f"A household has ${assets} in assets and ${liabilities} in liabilities. Select the model and calculate the result. Answer model; result.",
            f"net worth; ${worth}", "Use assets minus liabilities.",
            (f"sum; ${assets + liabilities}", f"budget percent; ${worth}"),
        )
    principal = random.choice((200, 400, 500))
    rate, years = random.choice((4, 5, 8)), random.choice((2, 3))
    interest = principal * rate * years // 100
    return PilotProblem(
        f"Find the simple interest on ${principal} at {rate}% for {years} years.", f"${interest}",
        "Use I = principal x decimal rate x time.",
        (f"${principal * rate // 100}", f"${principal + interest}"),
    )


def sample_inference(kind: ReasoningKind) -> PilotProblem:
    sample_size = random.choice((20, 25, 40, 50))
    successes = sample_size * random.choice((2, 3, 4)) // 5
    population = random.choice((100, 200))
    estimate = successes * population // sample_size
    if kind is ReasoningKind.CONCEPTUAL:
        return PilotProblem(
            "Which sample best supports an inference about every student in a school?",
            "randomly select students from every grade", "A broad random sample reduces selection bias.",
            ("ask only art-club members", "ask the first students entering one classroom"),
        )
    if kind is ReasoningKind.TRANSFER:
        return PilotProblem(
            "A sports-club poll is used to claim that all students prefer team sports. Diagnose the inference.",
            "not justified because the sample is biased", "The sample overrepresents students already interested in sports.",
            ("justified because the sample has data", "estimate by copying the club count"),
        )
    if kind is ReasoningKind.APPLICATION:
        return PilotProblem(
            f"In a random sample, {successes} of {sample_size} students prefer art. Select a model and estimate how many of {population} students prefer art. Answer model; result.",
            f"sample proportion; {estimate}", "Scale the representative sample proportion to the population.",
            (f"biased sample; {estimate}", f"sample count; {successes}"),
        )
    return PilotProblem(
        f"In a random sample, {successes} of {sample_size} students prefer art. Estimate how many of {population} students prefer art.",
        str(estimate), "Multiply the sample proportion by the population size.",
        ("not justified because the sample is biased", str(successes)),
    )
