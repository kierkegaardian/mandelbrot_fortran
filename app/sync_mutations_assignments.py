"""Atomic assignment mutations paired with sync outbox entries."""

from __future__ import annotations

import uuid

from . import db
from .sync_store import enqueue_change_on


def create_assignment(
    *,
    profile_id: int,
    skill: str,
    subskill: str | None,
    target_type: str,
    target_value: float,
    level: int,
    num_questions: int,
    question_type: str,
    mode_intuition_pct: int | None,
    mode_expression_pct: int | None,
    mode_word_pct: int | None,
    notes: str,
    created_at: str,
) -> int:
    sync_id = str(uuid.uuid4())
    with db.managed_connection() as conn:
        cursor = conn.execute(
            """INSERT INTO assignments
            (profile_id, skill, subskill, target_type, target_value, level,
             num_questions, question_type, mode_intuition_pct,
             mode_expression_pct, mode_word_pct, notes, created_at,
             sync_id, sync_updated_at, sync_deleted)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)""",
            (
                int(profile_id),
                skill,
                subskill,
                target_type,
                float(target_value),
                int(level),
                int(num_questions),
                question_type,
                mode_intuition_pct,
                mode_expression_pct,
                mode_word_pct,
                notes,
                created_at,
                sync_id,
                created_at,
            ),
        )
        local_id = int(cursor.lastrowid)
        enqueue_change_on(
            conn,
            entity_type="assignments",
            local_id=local_id,
            action="upsert",
            occurred_at=created_at,
            known_sync_id=sync_id,
        )
    return local_id


def complete_assignment(assignment_id: int, completed_at: str) -> None:
    with db.managed_connection() as conn:
        cursor = conn.execute(
            """UPDATE assignments SET active=0, completed_at=?,
            sync_updated_at=?, sync_deleted=0 WHERE id=?""",
            (completed_at, completed_at, int(assignment_id)),
        )
        if cursor.rowcount != 1:
            raise ValueError("Assignment not found.")
        enqueue_change_on(
            conn,
            entity_type="assignments",
            local_id=assignment_id,
            action="upsert",
            occurred_at=completed_at,
            extra={"active": False, "completed_at": completed_at},
        )
