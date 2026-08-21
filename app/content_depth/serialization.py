from __future__ import annotations

from typing import TYPE_CHECKING

from .models import (
    MisconceptionCandidate,
    ProofSpec,
    ProofStep,
    ReasoningKind,
    ResponseKind,
    WorkedExample,
    WorkedExampleStep,
)

if TYPE_CHECKING:
    from ..quiz_engine import Question


def question_depth_payload(question: "Question") -> dict[str, object]:
    return {
        "archetype_id": question.archetype_id,
        "reasoning_kind": question.reasoning_kind.value,
        "response_kind": question.response_kind.value,
        "matched_misconception_code": question.matched_misconception_code,
        "recovery_corrected_answer": question.recovery_corrected_answer,
        "recovery_transfer_archetype_id": question.recovery_transfer_archetype_id,
        "recovery_transfer_answer": question.recovery_transfer_answer,
        "recovery_transfer_correct": question.recovery_transfer_correct,
        "misconceptions": [
            {
                "code": item.code,
                "expected_answer": item.expected_answer,
                "feedback": item.feedback,
                "hint": item.hint,
                "recovery_archetype_id": item.recovery_archetype_id,
            }
            for item in question.misconceptions
        ],
        "worked_example": _worked_example_payload(question.worked_example),
        "proof_spec": _proof_payload(question.proof_spec),
    }


def question_depth_kwargs(payload: dict[str, object]) -> dict[str, object]:
    reasoning = _enum_or_default(ReasoningKind, payload.get("reasoning_kind"), ReasoningKind.LEGACY)
    response = _enum_or_default(ResponseKind, payload.get("response_kind"), ResponseKind.TYPED)
    misconceptions: list[MisconceptionCandidate] = []
    raw_misconceptions = payload.get("misconceptions")
    if isinstance(raw_misconceptions, list):
        for raw in raw_misconceptions:
            if not isinstance(raw, dict):
                continue
            misconceptions.append(
                MisconceptionCandidate(
                    str(raw.get("code", "")),
                    str(raw.get("expected_answer", "")),
                    str(raw.get("feedback", "")),
                    str(raw.get("hint", "")),
                    str(raw.get("recovery_archetype_id", "")),
                )
            )
    return {
        "archetype_id": str(payload["archetype_id"]) if payload.get("archetype_id") else None,
        "reasoning_kind": reasoning,
        "response_kind": response,
        "misconceptions": tuple(misconceptions),
        "worked_example": _worked_example_from_payload(payload.get("worked_example")),
        "proof_spec": _proof_from_payload(payload.get("proof_spec")),
        "matched_misconception_code": (
            str(payload["matched_misconception_code"]) if payload.get("matched_misconception_code") else None
        ),
        "recovery_corrected_answer": (
            str(payload["recovery_corrected_answer"]) if payload.get("recovery_corrected_answer") is not None else None
        ),
        "recovery_transfer_archetype_id": (
            str(payload["recovery_transfer_archetype_id"])
            if payload.get("recovery_transfer_archetype_id") is not None else None
        ),
        "recovery_transfer_answer": (
            str(payload["recovery_transfer_answer"]) if payload.get("recovery_transfer_answer") is not None else None
        ),
        "recovery_transfer_correct": (
            bool(payload["recovery_transfer_correct"])
            if payload.get("recovery_transfer_correct") is not None else None
        ),
    }


def _worked_example_payload(example: WorkedExample | None) -> object:
    if example is None:
        return None
    return {
        "title": example.title,
        "steps": [
            {
                "stage": step.stage,
                "prompt": step.prompt,
                "explanation": step.explanation,
                "expected_answer": step.expected_answer,
            }
            for step in example.steps
        ],
    }


def _worked_example_from_payload(raw: object) -> WorkedExample | None:
    if not isinstance(raw, dict):
        return None
    raw_steps = raw.get("steps")
    if not isinstance(raw_steps, list):
        return None
    steps = tuple(
        WorkedExampleStep(
            str(item.get("stage", "")),
            str(item.get("prompt", "")),
            str(item.get("explanation", "")),
            None if item.get("expected_answer") is None else str(item.get("expected_answer")),
        )
        for item in raw_steps
        if isinstance(item, dict)
    )
    return WorkedExample(str(raw.get("title", "Worked example")), steps)


def _proof_payload(spec: ProofSpec | None) -> object:
    if spec is None:
        return None
    return {
        "prompt": spec.prompt,
        "required_steps": [_proof_step_payload(step) for step in spec.required_steps],
        "distractor_steps": [_proof_step_payload(step) for step in spec.distractor_steps],
    }


def _proof_step_payload(step: ProofStep) -> dict[str, object]:
    return {
        "step_id": step.step_id,
        "statement": step.statement,
        "reason": step.reason,
        "depends_on": list(step.depends_on),
    }


def _proof_from_payload(raw: object) -> ProofSpec | None:
    if not isinstance(raw, dict):
        return None
    return ProofSpec(
        str(raw.get("prompt", "")),
        _proof_steps_from_payload(raw.get("required_steps")),
        _proof_steps_from_payload(raw.get("distractor_steps")),
    )


def _proof_steps_from_payload(raw: object) -> tuple[ProofStep, ...]:
    if not isinstance(raw, list):
        return ()
    steps: list[ProofStep] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        depends = item.get("depends_on")
        steps.append(
            ProofStep(
                str(item.get("step_id", "")),
                str(item.get("statement", "")),
                str(item.get("reason", "")),
                tuple(str(dep) for dep in depends) if isinstance(depends, list) else (),
            )
        )
    return tuple(steps)


def _enum_or_default(enum_type, raw: object, default):
    try:
        return enum_type(str(raw))
    except ValueError:
        return default
