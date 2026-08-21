from __future__ import annotations

import random
from collections.abc import Callable
from typing import TYPE_CHECKING

from .models import (
    ArchetypeSpec,
    DepthSpec,
    MisconceptionCandidate,
    QuestionRequest,
    ReasoningKind,
    ResponseKind,
)
from .pilot_algebra import congruence, slope, systems, two_step
from .pilot_add_subtract import missing_addend, subtraction, word_problem
from .pilot_applied import finance, sample_inference
from .pilot_elementary import addition, equivalent_fractions, graphs
from .pilot_income_gifts import income_gifts_wants_needs
from .pilot_money import coin_values
from .pilot_place_value import compare_place_values, identify_place_value
from .pilot_specs import PILOT_TARGETS
from .pilot_problem import PilotProblem

if TYPE_CHECKING:
    from ..quiz_engine import Question


def generate_pilot_question(
    request: QuestionRequest, spec: DepthSpec, archetype: ArchetypeSpec
) -> "Question":
    from ..quiz_engine import Question

    builder = _BUILDERS.get((request.skill, str(request.subskill)))
    if builder is None:
        raise ValueError(f"No authored pilot generator for {request.skill}/{request.subskill}")
    problem = builder(archetype.reasoning_kind)
    misconceptions = tuple(
        MisconceptionCandidate(
            item.code,
            problem.wrong_answers[index],
            item.feedback,
            item.hint,
            item.recovery_archetype_id,
        )
        for index, item in enumerate(spec.misconceptions[:2])
    )
    choices = _choices(problem.answer, problem.wrong_answers) if request.question_type == "mc" else None
    return Question(
        skill=request.skill,
        prompt=problem.prompt,
        correct_answer=problem.answer,
        explanation=problem.explanation,
        choices=choices,
        visual=None,
        subskill=request.subskill,
        question_label=_LABELS[archetype.reasoning_kind],
        mode="word" if archetype.reasoning_kind is ReasoningKind.APPLICATION else "expression",
        archetype_id=archetype.archetype_id,
        reasoning_kind=archetype.reasoning_kind,
        response_kind=ResponseKind.CHOICE if choices is not None else ResponseKind.TYPED,
        misconceptions=misconceptions,
        worked_example=spec.worked_example,
        proof_spec=spec.proof if archetype.reasoning_kind is ReasoningKind.PROOF else None,
    )


def has_pilot_generator(skill: str, subskill: str | None) -> bool:
    return subskill is not None and (skill, subskill) in PILOT_TARGETS


def _choices(answer: str, wrong: tuple[str, str]) -> list[str]:
    values = list(dict.fromkeys((answer, *wrong, "not enough information")))
    while len(values) < 4:
        values.append(f"different result {len(values)}")
    random.shuffle(values)
    return values[:4]


_LABELS = {
    ReasoningKind.CONCEPTUAL: "Concept",
    ReasoningKind.PROCEDURAL: "Strategy",
    ReasoningKind.TRANSFER: "Error Analysis",
    ReasoningKind.APPLICATION: "Application",
    ReasoningKind.PROOF: "Proof",
}

_BUILDERS: dict[tuple[str, str], Callable[[ReasoningKind], PilotProblem]] = {
    ("place_value", "Ones, tens, and hundreds identification"): identify_place_value,
    ("place_value", "Compare numbers by place value"): compare_place_values,
    ("add_subtract", "Single-digit addition"): addition,
    ("add_subtract", "Single-digit subtraction"): subtraction,
    ("add_subtract", "Missing addends"): missing_addend,
    ("add_subtract", "Word problems"): word_problem,
    ("money", "Dollar-coin values"): coin_values,
    ("financial_literacy", "Income, gifts, wants, and needs"): income_gifts_wants_needs,
    ("fractions", "Equivalent fractions"): equivalent_fractions,
    ("data_displays", "Picture and bar graphs"): graphs,
    ("financial_literacy", "Budget percentages, net worth, interest, and incentives"): finance,
    ("pre_algebra", "Two-step equations and inequalities"): two_step,
    ("algebra_linear", "Slope from points"): slope,
    ("algebra_1", "Systems by elimination"): systems,
    ("geometry_area", "Triangle congruence criteria"): congruence,
    ("data_analysis", "Sample inferences from displays"): sample_inference,
}
