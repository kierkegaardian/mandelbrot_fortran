from __future__ import annotations

from .connection import managed_connection


def add_quiz_recovery(
    quiz_question_id: int,
    misconception_code: str | None,
    corrected_answer: str,
    transfer_archetype_id: str | None,
    transfer_answer: str | None,
    transfer_correct: bool | None,
    created_at: str,
) -> int:
    with managed_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO quiz_recoveries
            (quiz_question_id, misconception_code, corrected_answer, transfer_archetype_id,
             transfer_answer, transfer_correct, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                int(quiz_question_id),
                misconception_code,
                corrected_answer,
                transfer_archetype_id,
                transfer_answer,
                None if transfer_correct is None else int(transfer_correct),
                created_at,
            ),
        )
        return int(cursor.lastrowid)
