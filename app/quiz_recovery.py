from __future__ import annotations

from dataclasses import dataclass

from .explanations import Explanation
from .quiz_engine import Question
from .content_depth.models import MisconceptionCandidate


@dataclass
class MistakeRecoveryState:
    phase: str
    source_question: Question
    incorrect_answer: str
    followup_question: Question | None = None
    misconception: MisconceptionCandidate | None = None


def should_offer_mistake_recovery(
    *, summer_mode: bool, curriculum_depth_beta: bool = False, strategy: str, question: Question
) -> bool:
    enabled = summer_mode or curriculum_depth_beta
    return enabled and strategy != "historical_practice" and bool(question.correct_answer)


def build_mistake_recovery_text(
    explanation: Explanation,
    *,
    phase: str,
    misconception: MisconceptionCandidate | None = None,
) -> str:
    if phase == "redo":
        if misconception is not None:
            return "\n".join(
                (
                    f"What happened: {misconception.feedback}",
                    f"Targeted hint: {misconception.hint}",
                    f"Mental model: {explanation.mental_model}",
                )
            )
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
