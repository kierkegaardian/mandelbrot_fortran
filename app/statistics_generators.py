from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
import random

from .statistics_catalog import STATISTICS_SUBSKILLS, intuition_for


@dataclass(frozen=True)
class StatisticsProblem:
    prompt: str
    correct_answer: str
    explanation: str
    choices: list[str] | None
    subskill: str
    mode: str = "expression"


def build_statistics_problem(
    level: int,
    question_type: str,
    subskill: str | None,
    preferred_mode: str | None,
) -> StatisticsProblem:
    chosen = _selected_subskill(subskill)
    if preferred_mode == "intuition":
        return _build_intuition_problem(chosen, question_type)
    if chosen == "Integrated descriptive statistics and probability":
        return _integrated_problem(question_type)
    if chosen == "Data collection and study design":
        return _text_problem(
            chosen,
            "Which method best supports a fair claim about all students in a school?",
            "random sample",
            "A random sample reduces selection bias compared with convenience or voluntary samples.",
            ("voluntary poll", "asking only friends", "choosing one class only"),
            question_type,
        )
    if chosen == "Distributions and standard deviation":
        value = random.randint(4, 12)
        prompt = f"A data set is {value}, {value}, {value}, {value}. What is its standard deviation?"
        return _numeric(chosen, prompt, 0, "When every value equals the mean, every distance from the mean is zero.", question_type)
    if chosen == "Probability rules":
        first, second = random.choice(((2, 3), (3, 4), (4, 5), (5, 6)))
        answer = _fraction(1, first * second)
        prompt = f"Two independent events have probabilities 1/{first} and 1/{second}. What is P(both)?"
        return _fraction_problem(chosen, prompt, answer, "Independent and events multiply their probabilities.", question_type)
    if chosen == "Combinatorics":
        shirts, pants = random.randint(3, 8), random.randint(2, 7)
        prompt = f"How many outfits can be made from {shirts} shirts and {pants} pants?"
        return _numeric(chosen, prompt, shirts * pants, "Multiply choices from independent stages.", question_type)
    if chosen == "Expected value":
        denominator = random.choice((2, 4, 5, 10))
        expected = random.randint(2, 8)
        prize = expected * denominator
        prompt = f"A game pays {prize} points with probability 1/{denominator} and 0 otherwise. What is the expected value?"
        return _numeric(chosen, prompt, expected, "Expected value weights each outcome by its probability.", question_type)
    if chosen == "Sampling and margin of error":
        return _text_problem(
            chosen,
            "Which random sample usually has the smaller margin of error?",
            "400 people",
            "Larger random samples usually reduce sampling variability and margin of error.",
            ("25 people", "10 people", "same no matter what"),
            question_type,
        )
    if chosen == "Confidence intervals":
        center = random.randint(40, 70)
        margin = random.randint(3, 9)
        low, high = center - margin, center + margin
        prompt = f"A confidence interval runs from {low}% to {high}%. What is the margin of error?"
        return _numeric(chosen, prompt, margin, "Margin of error is half the interval width.", question_type)
    if chosen == "Hypothesis tests":
        p_value = random.choice((0.01, 0.03, 0.08, 0.12))
        answer = "reject" if p_value < 0.05 else "do not reject"
        prompt = f"At alpha = 0.05, a test has p-value {p_value}. Should you reject or not reject the null?"
        return _text_problem(
            chosen,
            prompt,
            answer,
            "Reject the null when the p-value is below alpha.",
            ("reject", "do not reject", "increase alpha", "ignore p-value"),
            question_type,
        )
    slope = random.randint(-6, 8) or 3
    prompt = f"A regression line has slope {slope}. What is the predicted y-change when x increases by 1?"
    return _numeric("Correlation and regression", prompt, slope, "A regression slope is predicted y-change per 1 x-unit.", question_type)


def _selected_subskill(requested: str | None) -> str:
    if requested:
        if requested not in STATISTICS_SUBSKILLS:
            raise KeyError(requested)
        return requested
    return "Integrated descriptive statistics and probability"


def _build_intuition_problem(subskill: str, question_type: str) -> StatisticsProblem:
    prompts = {
        "Integrated descriptive statistics and probability": ("What should you check before trusting a sample percent?", "sample size", ("color name", "font size", "calculator brand")),
        "Data collection and study design": ("Which sampling plan best reduces selection bias?", "random sample", ("voluntary response", "asking friends", "one convenient row")),
        "Distributions and standard deviation": ("Standard deviation measures typical distance from what?", "mean", ("maximum", "sample name", "bar color")),
        "Probability rules": ("For independent and events, probabilities are usually what?", "multiplied", ("subtracted", "ignored", "sorted")),
        "Combinatorics": ("For stages of choices, the counting principle usually tells you to do what?", "multiply", ("average", "round", "graph")),
        "Expected value": ("Expected value is a probability-weighted what?", "average", ("maximum", "minimum only", "sample label")),
        "Sampling and margin of error": ("A larger random sample usually makes margin of error do what?", "shrink", ("double always", "become bias", "turn into correlation")),
        "Confidence intervals": ("A confidence interval gives a plausible range for what?", "population value", ("one guaranteed person", "graph title", "axis color")),
        "Hypothesis tests": ("A small p-value is evidence against which claim?", "null hypothesis", ("sample size", "histogram bin", "confidence level")),
        "Correlation and regression": ("Correlation alone does not prove what?", "causation", ("association", "direction", "prediction error")),
    }
    prompt, answer, distractors = prompts[subskill]
    choices = _text_choices(answer, distractors, question_type)
    intuition = intuition_for(subskill)
    explanation = intuition[0] if intuition else "Reason about the data context before calculating."
    return StatisticsProblem(prompt, answer, explanation, choices, subskill, mode="intuition")


def _integrated_problem(question_type: str) -> StatisticsProblem:
    a, b, c = random.randint(5, 25), random.randint(5, 25), random.randint(5, 25)
    total = a + b + c
    answer = round((b * 100) / total)
    prompt = f"A random sample has {a} red, {b} blue, and {c} green items. About what percent is blue?"
    return _numeric(
        "Integrated descriptive statistics and probability",
        prompt,
        answer,
        "Start with the sample total, then compare the category to the whole.",
        question_type,
    )


def _numeric(subskill: str, prompt: str, answer: int, explanation: str, question_type: str) -> StatisticsProblem:
    choices = _number_choices(answer, question_type)
    return StatisticsProblem(prompt, str(answer), explanation, choices, subskill)


def _fraction_problem(subskill: str, prompt: str, answer: str, explanation: str, question_type: str) -> StatisticsProblem:
    choices = None
    if question_type == "mc":
        choices = _text_choice_list(answer, ("1/2", "1/3", "2/3", "3/4"))
    return StatisticsProblem(prompt, answer, explanation, choices, subskill)


def _text_problem(
    subskill: str,
    prompt: str,
    answer: str,
    explanation: str,
    distractors: tuple[str, ...],
    question_type: str,
) -> StatisticsProblem:
    return StatisticsProblem(prompt, answer, explanation, _text_choices(answer, distractors, question_type), subskill)


def _fraction(numerator: int, denominator: int) -> str:
    value = Fraction(numerator, denominator)
    return f"{value.numerator}/{value.denominator}"


def _number_choices(correct: int, question_type: str) -> list[str] | None:
    if question_type != "mc":
        return None
    choices = {correct}
    for delta in range(1, 8):
        if len(choices) >= 4:
            break
        choices.add(correct + delta)
        if len(choices) >= 4:
            break
        choices.add(max(0, correct - delta))
    ordered = list(choices)
    random.shuffle(ordered)
    return [str(value) for value in ordered]


def _text_choices(correct: str, distractors: tuple[str, ...], question_type: str) -> list[str] | None:
    if question_type != "mc":
        return None
    return _text_choice_list(correct, distractors)


def _text_choice_list(correct: str, distractors: tuple[str, ...]) -> list[str]:
    choices = [correct]
    for distractor in distractors:
        if distractor != correct and distractor not in choices:
            choices.append(distractor)
        if len(choices) == 4:
            break
    random.shuffle(choices)
    return choices
