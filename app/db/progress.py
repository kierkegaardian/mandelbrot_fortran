from __future__ import annotations

from ..models import SubskillProgress
from .connection import managed_connection


def upsert_subskill_progress(
    profile_id: int, skill: str, subskill: str, is_correct: bool, updated_at: str, streak_to_master: int
) -> None:
    with managed_connection() as conn:
        row = conn.execute(
            """
            SELECT current_streak, best_streak, mastered
            FROM skill_subskill_progress
            WHERE profile_id = ? AND skill = ? AND subskill = ?
            """,
            (profile_id, skill, subskill),
        ).fetchone()
        if row is None:
            current_streak = 1 if is_correct else 0
            best_streak = current_streak
            mastered = 1 if is_correct and current_streak >= streak_to_master else 0
            conn.execute(
                """
                INSERT INTO skill_subskill_progress
                (profile_id, skill, subskill, current_streak, best_streak, mastered, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    profile_id,
                    skill,
                    subskill,
                    current_streak,
                    best_streak,
                    mastered,
                    updated_at,
                ),
            )
            return

        current_streak = row["current_streak"] + 1 if is_correct else 0
        best_streak = max(row["best_streak"], current_streak)
        mastered = 1 if row["mastered"] or current_streak >= streak_to_master else 0
        conn.execute(
            """
            UPDATE skill_subskill_progress
            SET current_streak = ?, best_streak = ?, mastered = ?, updated_at = ?
            WHERE profile_id = ? AND skill = ? AND subskill = ?
            """,
            (
                current_streak,
                best_streak,
                mastered,
                updated_at,
                profile_id,
                skill,
                subskill,
            ),
        )

def list_subskill_progress(profile_id: int, skill: str | None = None) -> list[SubskillProgress]:
    with managed_connection() as conn:
        if skill is None:
            rows = conn.execute(
                """
                SELECT profile_id, skill, subskill, current_streak, best_streak, mastered, updated_at
                FROM skill_subskill_progress
                WHERE profile_id = ?
                ORDER BY skill ASC, subskill ASC
                """,
                (profile_id,),
            ).fetchall()
        else:
            rows = conn.execute(
                """
                SELECT profile_id, skill, subskill, current_streak, best_streak, mastered, updated_at
                FROM skill_subskill_progress
                WHERE profile_id = ? AND skill = ?
                ORDER BY subskill ASC
                """,
                (profile_id, skill),
            ).fetchall()
    return [
        SubskillProgress(
            int(r["profile_id"]),
            r["skill"],
            r["subskill"],
            int(r["current_streak"]),
            int(r["best_streak"]),
            bool(r["mastered"]),
            r["updated_at"],
        )
        for r in rows
    ]
