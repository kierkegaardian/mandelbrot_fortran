"""Pure state and copy helpers for guided mistake recovery."""

from __future__ import annotations

from dataclasses import dataclass

from .explanations import Explanation
from .quiz_engine import Question


@dataclass
class MistakeRecoveryState:
    phase: str
    source_question: Question
    incorrect_answer: str
    followup_question: Question | None = None


def should_offer_mistake_recovery(
    *, summer_mode: bool, strategy: str, question: Question
) -> bool:
    return (
        summer_mode
        and strategy != "historical_practice"
        and bool(question.correct_answer)
    )


def build_mistake_recovery_text(
    explanation: Explanation, *, phase: str
) -> str:
    if phase == "redo":
        return "\n".join(
            (
                f"Why this mistake happens: {explanation.common_mistake}",
                f"Guided redo: {explanation.try_this}",
                f"Mental model: {explanation.mental_model}",
            )
        )
    if phase == "followup":
        return "\n".join(
            (
                "Nice correction. Try one like it on your own now.",
                f"Mental model: {explanation.mental_model}",
            )
        )
    return "\n".join(
        (
            "Recovery complete. Carry the same idea into the next question.",
            f"Mental model: {explanation.mental_model}",
        )
    )


__all__ = (
    "MistakeRecoveryState",
    "build_mistake_recovery_text",
    "should_offer_mistake_recovery",
)
