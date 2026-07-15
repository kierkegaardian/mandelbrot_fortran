"""Stable application service boundary; Family Sync is added in the next slice."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from .db.quiz_completion import (
    CompletionQuestion,
    CompletionRequest,
    record_completed_quiz_atomic,
)


@dataclass(frozen=True)
class QuestionResultInput:
    skill: str
    subskill: str | None
    question_label: str
    mode: str
    prompt: str
    correct_answer: str
    user_answer: str
    is_correct: bool
    explanation: str


@dataclass(frozen=True)
class RecordCompletedQuizResult:
    attempt_id: int
    completed_assignments: int
    completed_summer_task: bool
    summer_program_note: str | None


def record_completed_quiz(
    *,
    profile_id: int,
    quiz_set_id: int | None,
    skill: str,
    question_type: str,
    num_questions: int,
    level: int,
    score: int,
    created_at: str,
    elapsed_seconds: float | None,
    question_results: Sequence[QuestionResultInput],
    record_progress: bool,
    streak_to_master: int,
    record_daily_review: bool,
    summer_program_task_id: int | None = None,
) -> RecordCompletedQuizResult:
    if summer_program_task_id is not None:
        raise ValueError("Summer Program completion is not available in this stack slice.")
    request = CompletionRequest(
        profile_id=profile_id,
        quiz_set_id=quiz_set_id,
        skill=skill,
        question_type=question_type,
        num_questions=num_questions,
        level=level,
        score=score,
        created_at=created_at,
        elapsed_seconds=elapsed_seconds,
        questions=tuple(
            CompletionQuestion(
                skill=item.skill,
                subskill=item.subskill,
                question_label=item.question_label,
                mode=item.mode,
                prompt=item.prompt,
                correct_answer=item.correct_answer,
                user_answer=item.user_answer,
                is_correct=item.is_correct,
                explanation=item.explanation,
            )
            for item in question_results
        ),
        record_progress=record_progress,
        streak_to_master=streak_to_master,
        record_daily_review=record_daily_review,
    )
    result = record_completed_quiz_atomic(request)
    return RecordCompletedQuizResult(
        attempt_id=result.attempt_id,
        completed_assignments=len(result.completed_assignment_ids),
        completed_summer_task=False,
        summer_program_note=None,
    )


__all__ = (
    "QuestionResultInput",
    "RecordCompletedQuizResult",
    "record_completed_quiz",
)
