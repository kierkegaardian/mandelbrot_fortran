from __future__ import annotations

import json
from dataclasses import dataclass
from typing import TYPE_CHECKING

from .models import ProofSpec

if TYPE_CHECKING:
    from ..quiz_engine import Question


@dataclass(frozen=True)
class ProofGrade:
    correct: bool
    missing_step_ids: tuple[str, ...]
    distractor_step_ids: tuple[str, ...]
    dependency_errors: tuple[tuple[str, str], ...]


def grade_proof(spec: ProofSpec, ordered_step_ids: tuple[str, ...]) -> ProofGrade:
    required_ids = {step.step_id for step in spec.required_steps}
    distractor_ids = {step.step_id for step in spec.distractor_steps}
    submitted = set(ordered_step_ids)
    has_duplicates = len(submitted) != len(ordered_step_ids)
    missing = tuple(sorted(required_ids - submitted))
    distractors = tuple(step_id for step_id in ordered_step_ids if step_id in distractor_ids)
    positions = {step_id: index for index, step_id in enumerate(ordered_step_ids)}
    dependency_errors: list[tuple[str, str]] = []
    for step in spec.required_steps:
        if step.step_id not in positions:
            continue
        for dependency in step.depends_on:
            if dependency not in positions or positions[dependency] >= positions[step.step_id]:
                dependency_errors.append((step.step_id, dependency))
    extra = submitted - required_ids - distractor_ids
    correct = not has_duplicates and not missing and not distractors and not dependency_errors and not extra
    return ProofGrade(correct, missing, distractors, tuple(dependency_errors))


def encode_proof_answer(step_ids: tuple[str, ...]) -> str:
    return json.dumps(list(step_ids), ensure_ascii=True, separators=(",", ":"))


def decode_proof_answer(value: str) -> tuple[str, ...]:
    try:
        raw = json.loads(value)
    except json.JSONDecodeError:
        return ()
    if not isinstance(raw, list):
        return ()
    return tuple(str(item) for item in raw)


def is_question_answer_correct(
    question: "Question", answer: str, *, repeating: bool = False
) -> bool:
    if question.proof_spec is not None:
        return grade_proof(question.proof_spec, decode_proof_answer(answer)).correct
    from ..quiz_answers import is_correct_answer

    return is_correct_answer(question.correct_answer, answer, repeating)
