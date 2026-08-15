"""Typed inputs and result for atomic quiz completion persistence."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CompletionQuestion:
    skill: str
    subskill: str | None
    question_label: str
    mode: str
    prompt: str
    correct_answer: str
    user_answer: str
    is_correct: bool
    explanation: str


@dataclass(frozen=True, slots=True)
class CompletionRequest:
    profile_id: int
    quiz_set_id: int | None
    skill: str
    question_type: str
    num_questions: int
    level: int
    score: int
    created_at: str
    elapsed_seconds: float | None
    questions: tuple[CompletionQuestion, ...]
    record_progress: bool
    streak_to_master: int
    record_daily_review: bool
    summer_program_task_id: int | None = None
    summer_strand_scores_json: str = "{}"


@dataclass(frozen=True, slots=True)
class CompletionWriteResult:
    attempt_id: int
    completed_assignment_ids: tuple[int, ...]
    already_recorded: bool
    completed_summer_task: bool = False
    summer_program_id: int | None = None


__all__ = (
    "CompletionQuestion",
    "CompletionRequest",
    "CompletionWriteResult",
)
