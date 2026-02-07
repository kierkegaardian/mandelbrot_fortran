from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Optional


SKILLS = [
    "counting",
    "add_subtract",
    "multiply",
    "divide",
    "ratios",
    "fractions",
    "long_addition",
    "long_subtraction",
    "long_multiplication",
    "long_division",
    "money",
]
QUESTION_TYPES = ["mc", "typed", "both"]


@dataclass(frozen=True)
class Question:
    skill: str
    prompt: str
    correct_answer: str
    explanation: str
    choices: Optional[list[str]]
    visual: Optional[dict]


def _level_range(level: int) -> tuple[int, int]:
    if level <= 1:
        return (0, 10)
    if level == 2:
        return (0, 20)
    return (0, 50)


def _choice_set(correct: int, spread: int = 4) -> list[str]:
    choices = {correct}
    while len(choices) < 4:
        delta = random.randint(-spread, spread)
        if delta == 0:
            continue
        choices.add(max(0, correct + delta))
    ordered = list(choices)
    random.shuffle(ordered)
    return [str(c) for c in ordered]


def _long_range(level: int) -> tuple[int, int]:
    if level <= 1:
        return (10, 99)
    if level == 2:
        return (100, 999)
    return (1000, 9999)


def _money_choice_set(dollars: int, cents: int) -> list[str]:
    def fmt(d: int, c: int) -> str:
        return f"${d}.{c:02d}"

    choices = {fmt(dollars, cents)}
    while len(choices) < 4:
        d = max(0, dollars + random.choice([-2, -1, 1, 2, 5]))
        c = (cents + random.choice([-25, -10, -5, 5, 10, 25])) % 100
        choices.add(fmt(d, c))
    ordered = list(choices)
    random.shuffle(ordered)
    return ordered


def _fraction_choice_set(numerator: int, denominator: int) -> list[str]:
    def fmt(n: int, d: int) -> str:
        return f"{n}/{d}"

    choices = {fmt(numerator, denominator)}
    while len(choices) < 4:
        d = max(2, denominator + random.choice([-2, -1, 1, 2]))
        n = max(0, min(d - 1, numerator + random.choice([-2, -1, 1, 2])))
        if n == 0:
            n = 1
        choices.add(fmt(n, d))
    ordered = list(choices)
    random.shuffle(ordered)
    return ordered


def _division_answer(quotient: int, remainder: int) -> str:
    if remainder:
        return f"{quotient} R {remainder}"
    return str(quotient)


def _division_choices(quotient: int, remainder: int, divisor: int) -> list[str]:
    if remainder == 0:
        return _choice_set(quotient, spread=4)
    choices = {_division_answer(quotient, remainder)}
    while len(choices) < 4:
        dq = max(0, quotient + random.randint(-2, 2))
        dr = random.randint(0, max(0, divisor - 1))
        if dq == quotient and dr == remainder:
            continue
        choices.add(_division_answer(dq, dr))
    ordered = list(choices)
    random.shuffle(ordered)
    return ordered


def generate_question(skill: str, level: int, question_type: str) -> Question:
    if question_type not in QUESTION_TYPES:
        raise ValueError("Unknown question type")

    if skill == "mixed":
        skill = random.choice(SKILLS)

    if skill == "counting":
        low, high = _level_range(level)
        count = random.randint(max(1, low), max(3, high))
        prompt = "Count the objects. How many are there?"
        explanation = "Counting matches a number to a group of objects."
        choices = _choice_set(count) if question_type == "mc" else None
        visual = {"kind": "counting", "count": count}
        return Question(skill, prompt, str(count), explanation, choices, visual)

    if skill == "add_subtract":
        low, high = _level_range(level)
        a = random.randint(low, high)
        b = random.randint(low, high)
        if random.choice([True, False]):
            prompt = f"{a} + {b} = ?"
            answer = a + b
            explanation = "Adding combines two groups into one."
            visual = {"kind": "add", "a": a, "b": b}
        else:
            a, b = max(a, b), min(a, b)
            prompt = f"{a} - {b} = ?"
            answer = a - b
            explanation = "Subtracting removes part of a group."
            visual = {"kind": "subtract", "a": a, "b": b}
        choices = _choice_set(answer) if question_type == "mc" else None
        return Question(skill, prompt, str(answer), explanation, choices, visual)

    if skill == "multiply":
        low, high = _level_range(level)
        a = random.randint(1, max(2, high // 2))
        b = random.randint(1, max(2, high // 2))
        prompt = f"{a} x {b} = ?"
        answer = a * b
        explanation = "Multiplication is repeated groups."
        choices = _choice_set(answer, spread=6) if question_type == "mc" else None
        visual = {"kind": "multiply", "a": a, "b": b}
        return Question(skill, prompt, str(answer), explanation, choices, visual)

    if skill == "divide":
        low, high = _level_range(level)
        divisor = random.randint(1, max(2, high // 3))
        quotient = random.randint(1, max(2, high // 3))
        total = divisor * quotient
        prompt = f"{total} / {divisor} = ?"
        answer = quotient
        explanation = "Division shares a total into equal groups."
        choices = _choice_set(answer, spread=4) if question_type == "mc" else None
        visual = {"kind": "divide", "total": total, "groups": divisor}
        return Question(skill, prompt, str(answer), explanation, choices, visual)

    if skill == "ratios":
        low, high = _level_range(level)
        a = random.randint(1, max(2, high // 2))
        b = random.randint(1, max(2, high // 2))
        prompt = f"What is the ratio of A to B if A={a} and B={b}? (A:B)"
        answer = f"{a}:{b}"
        explanation = "A ratio compares two amounts side by side."
        choices = None if question_type == "typed" else [f"{a}:{b}", f"{b}:{a}", f"{a+b}:1", f"1:{a+b}"]
        visual = {"kind": "ratio", "a": a, "b": b}
        return Question(skill, prompt, answer, explanation, choices, visual)

    if skill == "fractions":
        if level <= 1:
            denominator = random.randint(2, 6)
            numerator = random.randint(1, denominator - 1)
        elif level == 2:
            denominator = random.randint(2, 8)
            numerator = random.randint(1, denominator * 2 - 1)
        else:
            denominator = random.randint(2, 10)
            numerator = random.randint(1, denominator * 3 - 1)
        if numerator % denominator == 0:
            numerator = max(1, numerator - 1)
        prompt = "What fraction is shaded? (fraction, decimal, or repeating like 0.(3) or 0.1(6))"
        answer = f"{numerator}/{denominator}"
        explanation = "The denominator is the total slices; the numerator is the shaded slices."
        choices = _fraction_choice_set(numerator, denominator) if question_type == "mc" else None
        visual = {"kind": "fraction", "numerator": numerator, "denominator": denominator}
        return Question(skill, prompt, answer, explanation, choices, visual)

    if skill == "long_addition":
        low, high = _long_range(level)
        a = random.randint(low, high)
        b = random.randint(low, high)
        prompt = f"Long addition: {a} + {b} = ?"
        answer = a + b
        explanation = "Long addition lines up place values and uses carries."
        choices = _choice_set(answer, spread=12) if question_type == "mc" else None
        visual = {"kind": "long_addition", "a": a, "b": b}
        return Question(skill, prompt, str(answer), explanation, choices, visual)

    if skill == "long_subtraction":
        low, high = _long_range(level)
        a = random.randint(low, high)
        b = random.randint(low, high)
        a, b = max(a, b), min(a, b)
        prompt = f"Long subtraction: {a} - {b} = ?"
        answer = a - b
        explanation = "Long subtraction keeps digits aligned and uses borrowing when needed."
        choices = _choice_set(answer, spread=12) if question_type == "mc" else None
        visual = {"kind": "long_subtraction", "a": a, "b": b}
        return Question(skill, prompt, str(answer), explanation, choices, visual)

    if skill == "long_multiplication":
        if level <= 1:
            a = random.randint(10, 99)
            b = random.randint(2, 9)
        elif level == 2:
            a = random.randint(10, 99)
            b = random.randint(10, 99)
        else:
            a = random.randint(100, 999)
            b = random.randint(10, 99)
        prompt = f"Long multiplication: {a} x {b} = ?"
        answer = a * b
        explanation = "Long multiplication builds partial products by place value."
        choices = _choice_set(answer, spread=20) if question_type == "mc" else None
        visual = {"kind": "long_multiplication", "a": a, "b": b}
        return Question(skill, prompt, str(answer), explanation, choices, visual)

    if skill == "long_division":
        if level <= 1:
            divisor = random.randint(2, 9)
            quotient = random.randint(2, 9)
        elif level == 2:
            divisor = random.randint(2, 9)
            quotient = random.randint(10, 99)
        else:
            divisor = random.randint(2, 12)
            quotient = random.randint(10, 99)
        remainder = random.randint(0, divisor - 1)
        dividend = divisor * quotient + remainder
        prompt = f"Long division: {dividend} / {divisor} = ? (use 'R' for remainder)"
        answer = _division_answer(quotient, remainder)
        explanation = "Long division shows how many groups fit, with any leftover as remainder."
        choices = _division_choices(quotient, remainder, divisor) if question_type == "mc" else None
        visual = {"kind": "long_division", "dividend": dividend, "divisor": divisor}
        return Question(skill, prompt, answer, explanation, choices, visual)

    if skill == "money":
        if level <= 1:
            dollars = random.randint(0, 20)
        elif level == 2:
            dollars = random.randint(0, 50)
        else:
            dollars = random.randint(0, 100)
        cents = random.randint(0, 99)
        prompt = "How much money is shown? (write as $d.cc)"
        answer = f"${dollars}.{cents:02d}"
        explanation = "Money totals combine dollars and cents."
        choices = _money_choice_set(dollars, cents) if question_type == "mc" else None
        visual = {"kind": "money", "dollars": dollars, "cents": cents}
        return Question(skill, prompt, answer, explanation, choices, visual)

    raise ValueError("Unknown skill")
