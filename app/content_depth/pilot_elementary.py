from __future__ import annotations

import random

from .models import ReasoningKind
from .pilot_problem import PilotProblem


def addition(kind: ReasoningKind) -> PilotProblem:
    a, b = random.randint(1, 9), random.randint(1, 9)
    total = a + b
    if kind is ReasoningKind.CONCEPTUAL:
        return PilotProblem(
            f"A tray has {a} red counters and {b} blue counters. Which equation models all the counters?",
            f"{a} + {b} = {total}", "Addition joins the two groups into one total.",
            (f"{a} - {b} = {a - b}", f"{a}{b} = {a}{b}"),
        )
    if kind is ReasoningKind.TRANSFER:
        return PilotProblem(
            f"A learner says {a} + {b} = {total + 1}. Diagnose the counting slip and give the correct total.",
            str(total), f"Count on exactly {b} times from {a}; the total is {total}.",
            (str(abs(a - b)), str(total + 1)),
        )
    if kind is ReasoningKind.APPLICATION:
        return PilotProblem(
            f"One supply bin holds {a} pencils and another holds {b}. Select the model and find the combined total. Answer model; result.",
            f"addition; {total}", "The word combined calls for an addition model.",
            (f"subtraction; {abs(a - b)}", f"addition; {total + 1}"),
        )
    return PilotProblem(
        f"Compute {a} + {b}.", str(total), f"Count on from {max(a, b)} to get {total}.",
        (str(abs(a - b)), str(total + 1)),
    )


def equivalent_fractions(kind: ReasoningKind) -> PilotProblem:
    denominator = random.randint(3, 8)
    numerator = random.randint(1, denominator - 1)
    factor = random.randint(2, 4)
    scaled_n, scaled_d = numerator * factor, denominator * factor
    equivalent = f"{scaled_n}/{scaled_d}"
    if kind is ReasoningKind.CONCEPTUAL:
        return PilotProblem(
            f"Which equality shows {numerator}/{denominator} renamed without changing its value?",
            f"{numerator}/{denominator} = {equivalent}", "Both numerator and denominator are scaled by the same factor.",
            (f"{numerator}/{denominator} = {numerator}/{scaled_d}", f"{numerator}/{denominator} = {denominator}/{numerator}"),
        )
    if kind is ReasoningKind.TRANSFER:
        return PilotProblem(
            f"A learner writes {numerator}/{denominator} = {scaled_n}/{denominator}. Correct the one-part scaling error.",
            equivalent, f"Scale both parts by {factor}: {equivalent}.",
            (f"{scaled_n}/{denominator}", f"{scaled_d}/{scaled_n}"),
        )
    if kind is ReasoningKind.APPLICATION:
        return PilotProblem(
            f"A recipe needs {numerator}/{denominator} cup. A scoop is 1/{scaled_d} cup. Select the fraction model and find the number of scoops. Answer model; result.",
            f"equivalent fraction; {scaled_n} scoops", "Rename the amount in units of the smaller scoop.",
            (f"one-part scaling; {numerator} scoops", f"reciprocal; {scaled_d} scoops"),
        )
    return PilotProblem(
        f"Complete {numerator}/{denominator} = ?/{scaled_d}.", str(scaled_n),
        f"The denominator was multiplied by {factor}, so multiply the numerator by {factor}.",
        (str(numerator), str(scaled_d)),
    )


def graphs(kind: ReasoningKind) -> PilotProblem:
    first, second = random.randint(3, 7), random.randint(1, 2)
    scale = random.choice((2, 5))
    if kind is ReasoningKind.CONCEPTUAL:
        return PilotProblem(
            "A class wants to compare counts for four favorite pets. Which model makes category sizes easiest to compare?",
            "bar graph", "Bar graphs compare categorical counts on a common scale.",
            ("picture graph with no key", "line graph over time"),
        )
    if kind is ReasoningKind.TRANSFER:
        return PilotProblem(
            f"A picture graph has {first} icons for art and {second} for music; each icon means {scale} votes. A learner reports {first - second} more art votes. Give the corrected difference.",
            str((first - second) * scale), "Apply the key to the icon difference.",
            (str(first - second), str((first + second) * scale)),
        )
    if kind is ReasoningKind.APPLICATION:
        art, music = first * scale, second * scale
        return PilotProblem(
            f"A survey records art {art} and music {music}. Select a display model and identify the larger category. Answer model; result.",
            "bar graph; art", "A labeled bar graph supports the category comparison.",
            ("picture graph without a key; art", "bar graph; music"),
        )
    return PilotProblem(
        f"A picture graph shows {first} art icons and {second} music icons. Each icon means {scale} votes. How many more art votes are there?",
        str((first - second) * scale), "Subtract the icon counts, then multiply by the key.",
        (str(first - second), str((first + second) * scale)),
    )
