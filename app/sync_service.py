"""Stable application service boundary for canonical sync-aware mutations."""

from __future__ import annotations

from dataclasses import dataclass
import json
from typing import Sequence

from . import db, summer_program, sync_client, sync_runner, sync_state, sync_store
from .db.quiz_completion import (
    CompletionQuestion,
    CompletionRequest,
    record_completed_quiz_atomic,
)
from .models import Assignment, Profile, QuizAttempt, QuizSet
from .sync_mutations_assignments import (
    complete_assignment,
    create_assignment,
)
from .sync_mutations_profiles import (
    create_profile,
    delete_profile as _delete_profile,
)
from .sync_mutations_quiz_sets import (
    create_quiz_set,
    delete_quiz_set as _delete_quiz_set,
    update_quiz_set as _update_quiz_set,
)
from .sync_service_types import PairingActionResult, SyncRunResult
from .time_utils import now_iso


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
    strand_scores = _summer_program_strand_scores(question_results)
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
        summer_program_task_id=summer_program_task_id,
        summer_strand_scores_json=json.dumps(
            strand_scores, ensure_ascii=True, sort_keys=True
        ),
    )
    result = record_completed_quiz_atomic(request)
    summer_program_note = None
    if result.summer_program_id is not None:
        summer_program.refresh_program_plan(
            result.summer_program_id, today_iso=created_at[:10]
        )
        program = db.get_summer_program(result.summer_program_id)
        if program is not None:
            finish = summer_program.finish_status(profile_id, program.id)
            db.update_summer_program(
                program.id, status=finish, updated_at=created_at
            )
            summer_program_note = summer_program.program_finish_summary(
                profile_id, program.id
            )
    return RecordCompletedQuizResult(
        attempt_id=result.attempt_id,
        completed_assignments=len(result.completed_assignment_ids),
        completed_summer_task=result.completed_summer_task,
        summer_program_note=summer_program_note,
    )


def _summer_program_strand_scores(
    question_results: Sequence[QuestionResultInput],
) -> dict[str, float]:
    buckets: dict[str, list[bool]] = {}
    for item in question_results:
        if "•" not in item.question_label:
            continue
        _prefix, strand = [
            part.strip() for part in item.question_label.split("•", 1)
        ]
        if strand:
            buckets.setdefault(strand, []).append(bool(item.is_correct))
    return {
        strand: 100.0 * sum(values) / len(values)
        for strand, values in buckets.items()
        if values
    }


def list_profiles() -> list[Profile]:
    return db.list_profiles()


def delete_profile(profile_id: int, deleted_at: str | None = None) -> None:
    _delete_profile(profile_id, deleted_at or now_iso())


def list_quiz_sets() -> list[QuizSet]:
    return db.list_quiz_sets()


def update_quiz_set(
    quiz_set_id: int,
    name: str,
    skill: str,
    question_type: str,
    num_questions: int,
    level: int,
    mode_intuition_pct: int | None = None,
    mode_expression_pct: int | None = None,
    mode_word_pct: int | None = None,
    updated_at: str | None = None,
) -> None:
    _update_quiz_set(
        quiz_set_id,
        name,
        skill,
        question_type,
        num_questions,
        level,
        mode_intuition_pct,
        mode_expression_pct,
        mode_word_pct,
        updated_at or now_iso(),
    )


def delete_quiz_set(quiz_set_id: int, deleted_at: str | None = None) -> None:
    _delete_quiz_set(quiz_set_id, deleted_at or now_iso())


def list_assignments(
    profile_id: int,
    active_only: bool | None = True,
    *,
    skill: str | None = None,
    target_type: str | None = None,
    limit: int | None = None,
) -> list[Assignment]:
    return db.list_assignments(
        profile_id,
        active_only=active_only,
        skill=skill,
        target_type=target_type,
        limit=limit,
    )


def assignment_completion_analytics(
    profile_id: int, recent_days: int = 30
) -> dict[str, object]:
    return db.assignment_completion_analytics(profile_id, recent_days=recent_days)


def get_next_active_assignment(profile_id: int) -> Assignment | None:
    return db.get_next_active_assignment(profile_id)


def list_attempts(profile_id: int) -> list[QuizAttempt]:
    return db.list_attempts(profile_id)


def sync_now(parent_profile_id: int | None = None) -> SyncRunResult:
    return sync_runner.sync_now(parent_profile_id)


def start_family_sync(parent_profile_id: int | None = None) -> PairingActionResult:
    return sync_runner.start_family_sync(parent_profile_id)


def join_family_sync(
    pairing_token: str, parent_profile_id: int | None = None
) -> PairingActionResult:
    return sync_runner.join_family_sync(pairing_token, parent_profile_id)


__all__ = (
    "PairingActionResult",
    "QuestionResultInput",
    "RecordCompletedQuizResult",
    "SyncRunResult",
    "assignment_completion_analytics",
    "complete_assignment",
    "create_assignment",
    "create_profile",
    "create_quiz_set",
    "delete_profile",
    "delete_quiz_set",
    "get_next_active_assignment",
    "join_family_sync",
    "list_assignments",
    "list_attempts",
    "list_profiles",
    "list_quiz_sets",
    "record_completed_quiz",
    "start_family_sync",
    "sync_now",
    "update_quiz_set",
)
