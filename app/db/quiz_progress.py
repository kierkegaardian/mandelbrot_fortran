from __future__ import annotations

from .connection import managed_connection

def save_quiz_progress(
    profile_id: int,
    attempt_id: int | None,
    question_index: int,
    state_json: str,
    updated_at: str,
) -> int:
    with managed_connection() as conn:
        if attempt_id is None:
            cur = conn.execute(
                """
                INSERT INTO quiz_attempt_progress (profile_id, question_index, state_json, updated_at)
                VALUES (?, ?, ?, ?)
                """,
                (int(profile_id), max(0, int(question_index)), state_json, updated_at),
            )
            return int(cur.lastrowid)
        conn.execute(
            """
            UPDATE quiz_attempt_progress
            SET question_index = ?, state_json = ?, updated_at = ?
            WHERE attempt_id = ? AND profile_id = ?
            """,
            (max(0, int(question_index)), state_json, updated_at, int(attempt_id), int(profile_id)),
        )
        return int(attempt_id)


def load_quiz_progress(profile_id: int) -> tuple[int, int, str] | None:
    with managed_connection() as conn:
        row = conn.execute(
            """
            SELECT attempt_id, question_index, state_json
            FROM quiz_attempt_progress
            WHERE profile_id = ?
            ORDER BY updated_at DESC, attempt_id DESC
            LIMIT 1
            """,
            (int(profile_id),),
        ).fetchone()
    if row is None:
        return None
    return (int(row["attempt_id"]), int(row["question_index"]), str(row["state_json"]))


def clear_quiz_progress(attempt_id: int) -> None:
    with managed_connection() as conn:
        conn.execute("DELETE FROM quiz_attempt_progress WHERE attempt_id = ?", (int(attempt_id),))


def clear_quiz_progress_for_profile(profile_id: int) -> None:
    with managed_connection() as conn:
        conn.execute("DELETE FROM quiz_attempt_progress WHERE profile_id = ?", (int(profile_id),))

