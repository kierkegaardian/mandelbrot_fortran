"""Atomic quiz-set mutations paired with sync outbox entries."""

from __future__ import annotations

import uuid

from . import db
from .models import QuizSet
from .sync_store import enqueue_change_on, soft_delete_entity_on


def create_quiz_set(
    name: str,
    skill: str,
    question_type: str,
    num_questions: int,
    level: int,
    created_at: str,
    mode_intuition_pct: int | None = None,
    mode_expression_pct: int | None = None,
    mode_word_pct: int | None = None,
) -> QuizSet:
    sync_id = str(uuid.uuid4())
    values = (
        name,
        skill,
        question_type,
        int(num_questions),
        int(level),
        mode_intuition_pct,
        mode_expression_pct,
        mode_word_pct,
        created_at,
        sync_id,
        created_at,
    )
    with db.managed_connection() as conn:
        cursor = conn.execute(
            """INSERT INTO quiz_sets
            (name, skill, question_type, num_questions, level,
             mode_intuition_pct, mode_expression_pct, mode_word_pct,
             created_at, sync_id, sync_updated_at, sync_deleted)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)""",
            values,
        )
        local_id = int(cursor.lastrowid)
        enqueue_change_on(
            conn,
            entity_type="quiz_sets",
            local_id=local_id,
            action="upsert",
            occurred_at=created_at,
            known_sync_id=sync_id,
        )
    return QuizSet(local_id, *values[:8])


def update_quiz_set(
    quiz_set_id: int,
    name: str,
    skill: str,
    question_type: str,
    num_questions: int,
    level: int,
    mode_intuition_pct: int | None,
    mode_expression_pct: int | None,
    mode_word_pct: int | None,
    updated_at: str,
) -> None:
    with db.managed_connection() as conn:
        cursor = conn.execute(
            """UPDATE quiz_sets SET name=?, skill=?, question_type=?,
            num_questions=?, level=?, mode_intuition_pct=?,
            mode_expression_pct=?, mode_word_pct=?, sync_updated_at=?,
            sync_deleted=0 WHERE id=?""",
            (
                name,
                skill,
                question_type,
                int(num_questions),
                int(level),
                mode_intuition_pct,
                mode_expression_pct,
                mode_word_pct,
                updated_at,
                int(quiz_set_id),
            ),
        )
        if cursor.rowcount != 1:
            raise ValueError("Quiz set not found.")
        enqueue_change_on(
            conn,
            entity_type="quiz_sets",
            local_id=quiz_set_id,
            action="upsert",
            occurred_at=updated_at,
        )


def delete_quiz_set(quiz_set_id: int, deleted_at: str) -> None:
    with db.managed_connection() as conn:
        row = conn.execute(
            "SELECT sync_id FROM quiz_sets WHERE id = ?", (int(quiz_set_id),)
        ).fetchone()
        if row is None:
            return
        soft_delete_entity_on(
            conn,
            entity_type="quiz_sets",
            local_id=quiz_set_id,
            entity_sync_id=str(row["sync_id"]),
            deleted_at=deleted_at,
        )
