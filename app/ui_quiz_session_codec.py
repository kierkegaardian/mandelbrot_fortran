"""Strict JSON codec helpers for resumable quiz state."""

from __future__ import annotations

from .models import ScaffoldStep
from .quiz_engine import Question


class InvalidQuizProgress(ValueError):
    """A saved quiz cannot be reconstructed safely."""


def question_to_payload(question: Question) -> dict[str, object]:
    return {
        "skill": question.skill,
        "prompt": question.prompt,
        "correct_answer": question.correct_answer,
        "explanation": question.explanation,
        "choices": question.choices,
        "visual": question.visual,
        "template_id": question.template_id,
        "template_external_id": question.template_external_id,
        "subskill": question.subskill,
        "question_label": question.question_label,
        "mode": question.mode,
        "scaffold_steps": [
            {
                "prompt": step.prompt,
                "expected_answer": step.expected_answer,
                "hint": step.hint,
            }
            for step in (question.scaffold_steps or [])
        ],
    }


def question_from_payload(raw: object) -> Question:
    if not isinstance(raw, dict):
        raise InvalidQuizProgress("Question entry is not an object.")
    required = ("skill", "prompt", "correct_answer", "explanation")
    if any(not isinstance(raw.get(key), str) for key in required):
        raise InvalidQuizProgress("Question text fields are invalid.")
    if not str(raw["skill"]).strip() or not str(raw["prompt"]).strip():
        raise InvalidQuizProgress("Question is missing a skill or prompt.")
    raw_choices = raw.get("choices")
    if raw_choices is not None and (
        not isinstance(raw_choices, list)
        or not all(isinstance(item, str) for item in raw_choices)
    ):
        raise InvalidQuizProgress("Question choices are invalid.")
    raw_visual = raw.get("visual")
    if raw_visual is not None and not isinstance(raw_visual, dict):
        raise InvalidQuizProgress("Question visual is invalid.")
    raw_template_id = raw.get("template_id")
    if raw_template_id is not None and (
        isinstance(raw_template_id, bool) or not isinstance(raw_template_id, int)
    ):
        raise InvalidQuizProgress("Question template ID is invalid.")
    raw_steps = raw.get("scaffold_steps", [])
    if not isinstance(raw_steps, list):
        raise InvalidQuizProgress("Question scaffold is invalid.")
    scaffold_steps: list[ScaffoldStep] = []
    for step in raw_steps:
        if not isinstance(step, dict) or not all(
            isinstance(step.get(key), str)
            for key in ("prompt", "expected_answer", "hint")
        ):
            raise InvalidQuizProgress("Question scaffold step is invalid.")
        scaffold_steps.append(
            ScaffoldStep(
                prompt=str(step["prompt"]),
                expected_answer=str(step["expected_answer"]),
                hint=str(step["hint"]),
            )
        )
    return Question(
        skill=str(raw["skill"]),
        prompt=str(raw["prompt"]),
        correct_answer=str(raw["correct_answer"]),
        explanation=str(raw["explanation"]),
        choices=list(raw_choices) if isinstance(raw_choices, list) else None,
        visual=dict(raw_visual) if isinstance(raw_visual, dict) else None,
        template_id=raw_template_id,
        template_external_id=optional_text(raw.get("template_external_id")),
        subskill=optional_text(raw.get("subskill")),
        question_label=text_or(raw.get("question_label"), "Core"),
        mode=text_or(raw.get("mode"), "expression"),
        scaffold_steps=scaffold_steps or None,
    )


def optional_text(value: object) -> str | None:
    return value if isinstance(value, str) and value else None


def text_or(value: object, default: str) -> str:
    return value if isinstance(value, str) and value else default


def bounded_int(value: object, minimum: int, maximum: int, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise InvalidQuizProgress(f"Saved {label} is not an integer.")
    if value < minimum or value > maximum:
        raise InvalidQuizProgress(f"Saved {label} is out of bounds.")
    return value
