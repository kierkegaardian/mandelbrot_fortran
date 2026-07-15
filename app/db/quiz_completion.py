"""Atomic persistence boundary for a completed quiz."""

from __future__ import annotations

from dataclasses import asdict
import json
import sqlite3
import uuid

from ._util import _iso_day_utc
from .connection import managed_connection
from .quiz_completion_types import (
    CompletionQuestion,
    CompletionRequest,
    CompletionWriteResult,
)


def record_completed_quiz_atomic(request: CompletionRequest) -> CompletionWriteResult:
    attempt_sync_id = _completion_sync_id(request)
    with managed_connection() as conn:
        existing = conn.execute(
            "SELECT id FROM quiz_attempts WHERE sync_id = ?",
            (attempt_sync_id,),
        ).fetchone()
        if existing is not None:
            completed_ids = _completed_assignments_at(
                conn, request.profile_id, request.created_at
            )
            return CompletionWriteResult(
                attempt_id=int(existing["id"]),
                completed_assignment_ids=completed_ids,
                already_recorded=True,
            )

        attempt_id = _insert_attempt(conn, request, attempt_sync_id)
        _enqueue_outbox(
            conn,
            entity_type="quiz_attempts",
            entity_sync_id=attempt_sync_id,
            local_id=attempt_id,
            occurred_at=request.created_at,
            extra={"profile_id": request.profile_id, "skill": request.skill},
        )
        question_namespace = uuid.UUID(attempt_sync_id)
        for index, item in enumerate(request.questions):
            if request.record_progress and item.subskill is not None:
                _upsert_subskill_progress(conn, request, item)
            question_sync_id = str(
                uuid.uuid5(question_namespace, f"question:{index}")
            )
            question_id = _insert_question_result(
                conn, attempt_id, item, question_sync_id, request.created_at
            )
            _enqueue_outbox(
                conn,
                entity_type="quiz_questions",
                entity_sync_id=question_sync_id,
                local_id=question_id,
                occurred_at=request.created_at,
                extra={"attempt_local_id": attempt_id, "profile_id": request.profile_id},
            )

        completed_ids = _evaluate_assignments(conn, request, attempt_id)
        for assignment_id in completed_ids:
            row = conn.execute(
                "SELECT sync_id FROM assignments WHERE id = ?",
                (assignment_id,),
            ).fetchone()
            if row is None:
                raise RuntimeError("Completed assignment disappeared during transaction.")
            _enqueue_outbox(
                conn,
                entity_type="assignments",
                entity_sync_id=str(row["sync_id"]),
                local_id=assignment_id,
                occurred_at=request.created_at,
                extra={"active": False, "completed_at": request.created_at},
            )
        if request.record_daily_review:
            _record_daily_goal(conn, request.profile_id, request.created_at)

    return CompletionWriteResult(
        attempt_id=attempt_id,
        completed_assignment_ids=completed_ids,
        already_recorded=False,
    )


def _completion_sync_id(request: CompletionRequest) -> str:
    stable = asdict(request)
    stable.pop("elapsed_seconds", None)
    payload = json.dumps(stable, sort_keys=True, separators=(",", ":"))
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f"mandelquest-completion:{payload}"))


def _insert_attempt(
    conn: sqlite3.Connection, request: CompletionRequest, sync_id: str
) -> int:
    cursor = conn.execute(
        """
        INSERT INTO quiz_attempts
        (profile_id, quiz_set_id, skill, question_type, num_questions, level,
         score, elapsed_seconds, created_at, sync_id, sync_updated_at, sync_deleted)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
        """,
        (
            request.profile_id,
            request.quiz_set_id,
            request.skill,
            request.question_type,
            request.num_questions,
            request.level,
            request.score,
            request.elapsed_seconds,
            request.created_at,
            sync_id,
            request.created_at,
        ),
    )
    return int(cursor.lastrowid)


def _insert_question_result(
    conn: sqlite3.Connection,
    attempt_id: int,
    item: CompletionQuestion,
    sync_id: str,
    updated_at: str,
) -> int:
    cursor = conn.execute(
        """
        INSERT INTO quiz_questions
        (attempt_id, skill, subskill, question_label, mode, prompt,
         correct_answer, user_answer, is_correct, explanation,
         sync_id, sync_updated_at, sync_deleted)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
        """,
        (
            attempt_id,
            item.skill,
            item.subskill,
            item.question_label,
            item.mode,
            item.prompt,
            item.correct_answer,
            item.user_answer,
            int(item.is_correct),
            item.explanation,
            sync_id,
            updated_at,
        ),
    )
    return int(cursor.lastrowid)


def _upsert_subskill_progress(
    conn: sqlite3.Connection,
    request: CompletionRequest,
    item: CompletionQuestion,
) -> None:
    row = conn.execute(
        """SELECT current_streak, best_streak, mastered
        FROM skill_subskill_progress
        WHERE profile_id = ? AND skill = ? AND subskill = ?""",
        (request.profile_id, item.skill, item.subskill),
    ).fetchone()
    previous = int(row["current_streak"]) if row is not None else 0
    current = previous + 1 if item.is_correct else 0
    best = max(int(row["best_streak"]) if row else 0, current)
    mastered = bool(row and row["mastered"]) or current >= request.streak_to_master
    conn.execute(
        """
        INSERT INTO skill_subskill_progress
        (profile_id, skill, subskill, current_streak, best_streak, mastered, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(profile_id, skill, subskill) DO UPDATE SET
          current_streak=excluded.current_streak, best_streak=excluded.best_streak,
          mastered=excluded.mastered, updated_at=excluded.updated_at
        """,
        (
            request.profile_id,
            item.skill,
            item.subskill,
            current,
            best,
            int(mastered),
            request.created_at,
        ),
    )


def _evaluate_assignments(
    conn: sqlite3.Connection, request: CompletionRequest, attempt_id: int
) -> tuple[int, ...]:
    del attempt_id
    rows = conn.execute(
        """SELECT id, skill, subskill, target_type, target_value
        FROM assignments
        WHERE profile_id = ? AND active = 1 AND sync_deleted = 0
        ORDER BY created_at, id""",
        (request.profile_id,),
    ).fetchall()
    completed: list[int] = []
    for row in rows:
        done = False
        if row["target_type"] == "quiz_score_pct" and row["skill"] == request.skill:
            score_pct = 100.0 * request.score / max(1, request.num_questions)
            done = score_pct >= max(100.0, float(row["target_value"]))
        elif row["target_type"] == "subskill_mastered" and row["subskill"]:
            progress = conn.execute(
                """SELECT mastered FROM skill_subskill_progress
                WHERE profile_id = ? AND skill = ? AND subskill = ?""",
                (request.profile_id, row["skill"], row["subskill"]),
            ).fetchone()
            done = bool(progress and progress["mastered"])
        if done:
            conn.execute(
                """UPDATE assignments SET active=0, completed_at=?,
                sync_updated_at=?, sync_deleted=0 WHERE id=?""",
                (request.created_at, request.created_at, int(row["id"])),
            )
            completed.append(int(row["id"]))
    return tuple(completed)


def _record_daily_goal(
    conn: sqlite3.Connection, profile_id: int, completed_at: str
) -> None:
    day = _iso_day_utc(completed_at)
    conn.execute(
        """INSERT INTO daily_goal_history
        (profile_id, day_utc, completions, last_completed_at) VALUES (?, ?, 1, ?)
        ON CONFLICT(profile_id, day_utc) DO UPDATE SET
          completions=daily_goal_history.completions + 1,
          last_completed_at=excluded.last_completed_at""",
        (profile_id, day, completed_at),
    )


def _enqueue_outbox(
    conn: sqlite3.Connection,
    *,
    entity_type: str,
    entity_sync_id: str,
    local_id: int,
    occurred_at: str,
    extra: dict[str, object],
) -> None:
    payload = json.dumps(
        {"local_id": local_id, **extra}, sort_keys=True, separators=(",", ":")
    )
    conn.execute(
        """INSERT INTO sync_outbox
        (entity_type, entity_sync_id, action, payload_json, created_at,
         last_attempt_at, attempt_count, last_error, synced_at)
        VALUES (?, ?, 'upsert', ?, ?, NULL, 0, NULL, NULL)""",
        (entity_type, entity_sync_id, payload, occurred_at),
    )


def _completed_assignments_at(
    conn: sqlite3.Connection, profile_id: int, completed_at: str
) -> tuple[int, ...]:
    rows = conn.execute(
        """SELECT id FROM assignments
        WHERE profile_id = ? AND completed_at = ? AND sync_deleted = 0
        ORDER BY id""",
        (profile_id, completed_at),
    ).fetchall()
    return tuple(int(row["id"]) for row in rows)
