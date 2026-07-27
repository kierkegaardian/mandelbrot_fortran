from __future__ import annotations

from ..quiz_engine import Question
from .models import MisconceptionCandidate, ReasoningKind
from .registry import depth_spec_for


def transfer_request(question: Question) -> tuple[str | None, frozenset[str]]:
    spec = depth_spec_for(question.skill, question.subskill)
    preferred_id = None
    if spec is not None:
        preferred_kind = (
            ReasoningKind.APPLICATION
            if question.reasoning_kind is ReasoningKind.TRANSFER
            else ReasoningKind.TRANSFER
        )
        preferred_id = next(
            (item.archetype_id for item in spec.archetypes if item.reasoning_kind is preferred_kind),
            None,
        )
    exclusions = frozenset({question.archetype_id}) if question.archetype_id else frozenset()
    return preferred_id, exclusions


def record_transfer(
    source: Question, followup: Question | None, answer: str | None, correct: bool
) -> None:
    if followup is None:
        return
    source.recovery_transfer_archetype_id = followup.archetype_id
    source.recovery_transfer_answer = answer
    source.recovery_transfer_correct = correct


def resume_source(questions: list[Question], restored: Question) -> Question:
    return next(
        (
            question for question in questions
            if question.prompt == restored.prompt and question.archetype_id == restored.archetype_id
        ),
        restored,
    )


def misconception_by_code(question: Question, code: str) -> MisconceptionCandidate | None:
    return next((item for item in question.misconceptions if item.code == code), None)
