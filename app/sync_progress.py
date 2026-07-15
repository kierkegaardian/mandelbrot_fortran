"""Rebuild derived mastery after canonical sync changes."""

from __future__ import annotations

import sqlite3


def rebuild_subskill_progress(
    conn: sqlite3.Connection, streak_to_master: int
) -> None:
    conn.execute("DELETE FROM skill_subskill_progress")
    rows = conn.execute(
        """
        SELECT qa.profile_id, qq.skill, qq.subskill, qq.is_correct,
               qa.created_at, qq.id
        FROM quiz_questions qq
        JOIN quiz_attempts qa ON qa.id = qq.attempt_id
        WHERE qq.subskill IS NOT NULL
          AND qq.sync_deleted = 0
          AND qa.sync_deleted = 0
        ORDER BY qa.created_at ASC, qq.id ASC
        """
    ).fetchall()
    state: dict[tuple[int, str, str], tuple[int, int, bool, str]] = {}
    for row in rows:
        key = (int(row["profile_id"]), str(row["skill"]), str(row["subskill"]))
        current, best, mastered, _updated = state.get(
            key, (0, 0, False, str(row["created_at"]))
        )
        next_streak = current + 1 if bool(row["is_correct"]) else 0
        state[key] = (
            next_streak,
            max(best, next_streak),
            bool(mastered or next_streak >= streak_to_master),
            str(row["created_at"]),
        )
    for (profile_id, skill, subskill), values in state.items():
        current, best, mastered, updated_at = values
        conn.execute(
            """INSERT INTO skill_subskill_progress
            (profile_id, skill, subskill, current_streak, best_streak,
             mastered, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (profile_id, skill, subskill, current, best, int(mastered), updated_at),
        )
