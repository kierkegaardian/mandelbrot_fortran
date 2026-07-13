from __future__ import annotations

from datetime import datetime, timezone

from ..models import DailyGoalHistory, SubskillProgress
from ._util import _iso_day_utc, _parse_iso_utc
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


def rebuild_subskill_progress(profile_id: int, streak_to_master: int) -> None:
    with managed_connection() as conn:
        rows = conn.execute(
            """
            SELECT q.skill, q.subskill, q.is_correct, a.created_at
            FROM quiz_questions q
            JOIN quiz_attempts a ON a.id = q.attempt_id
            WHERE a.profile_id = ?
              AND a.sync_deleted = 0
              AND q.sync_deleted = 0
              AND q.subskill IS NOT NULL
            ORDER BY a.created_at ASC, a.id ASC, q.id ASC
            """,
            (int(profile_id),),
        ).fetchall()

        conn.execute(
            "DELETE FROM skill_subskill_progress WHERE profile_id = ?",
            (int(profile_id),),
        )

        state: dict[tuple[str, str], tuple[int, int, bool, str]] = {}
        for row in rows:
            key = (str(row["skill"]), str(row["subskill"]))
            current_streak, best_streak, mastered, _updated_at = state.get(key, (0, 0, False, ""))
            is_correct = bool(int(row["is_correct"]))
            current_streak = current_streak + 1 if is_correct else 0
            best_streak = max(best_streak, current_streak)
            mastered = mastered or current_streak >= int(streak_to_master)
            state[key] = (current_streak, best_streak, mastered, str(row["created_at"]))

        for (skill, subskill), (current_streak, best_streak, mastered, updated_at) in state.items():
            conn.execute(
                """
                INSERT INTO skill_subskill_progress
                (profile_id, skill, subskill, current_streak, best_streak, mastered, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    int(profile_id),
                    skill,
                    subskill,
                    int(current_streak),
                    int(best_streak),
                    1 if mastered else 0,
                    updated_at,
                ),
            )

def skill_progress_pipeline(profile_id: int) -> dict[str, dict[str, int]]:
    out: dict[str, dict[str, int]] = {}
    with managed_connection() as conn:
        attempt_rows = conn.execute(
            """
            SELECT skill, COUNT(*) AS attempts, SUM(num_questions) AS questions
            FROM quiz_attempts
            WHERE profile_id = ? AND sync_deleted = 0
            GROUP BY skill
            """,
            (int(profile_id),),
        ).fetchall()
        worksheet_rows = conn.execute(
            """
            SELECT skill, COUNT(*) AS worksheets
            FROM worksheets
            WHERE profile_id = ?
            GROUP BY skill
            """,
            (int(profile_id),),
        ).fetchall()
    for row in attempt_rows:
        skill = str(row["skill"])
        out[skill] = {
            "attempts": int(row["attempts"] or 0),
            "questions": int(row["questions"] or 0),
            "worksheets": 0,
        }
    for row in worksheet_rows:
        skill = str(row["skill"])
        if skill not in out:
            out[skill] = {"attempts": 0, "questions": 0, "worksheets": 0}
        out[skill]["worksheets"] = int(row["worksheets"] or 0)
    return out

def record_daily_review_completion(profile_id: int, completed_at: str) -> None:
    day_utc = _iso_day_utc(completed_at)
    with managed_connection() as conn:
        row = conn.execute(
            """
            SELECT completions
            FROM daily_goal_history
            WHERE profile_id = ? AND day_utc = ?
            """,
            (int(profile_id), day_utc),
        ).fetchone()
        if row is None:
            conn.execute(
                """
                INSERT INTO daily_goal_history (profile_id, day_utc, completions, last_completed_at)
                VALUES (?, ?, ?, ?)
                """,
                (int(profile_id), day_utc, 1, completed_at),
            )
            return
        conn.execute(
            """
            UPDATE daily_goal_history
            SET completions = ?, last_completed_at = ?
            WHERE profile_id = ? AND day_utc = ?
            """,
            (int(row["completions"]) + 1, completed_at, int(profile_id), day_utc),
        )


def list_daily_goal_history(profile_id: int, limit: int = 60) -> list[DailyGoalHistory]:
    with managed_connection() as conn:
        rows = conn.execute(
            """
            SELECT profile_id, day_utc, completions, last_completed_at
            FROM daily_goal_history
            WHERE profile_id = ?
            ORDER BY day_utc DESC
            LIMIT ?
            """,
            (int(profile_id), max(1, int(limit))),
        ).fetchall()
    return [
        DailyGoalHistory(
            profile_id=int(r["profile_id"]),
            day_utc=r["day_utc"],
            completions=int(r["completions"]),
            last_completed_at=r["last_completed_at"],
        )
        for r in rows
    ]


def daily_goal_status(profile_id: int, now_iso_text: str | None = None) -> tuple[int, int]:
    now = _parse_iso_utc(now_iso_text) if now_iso_text else datetime.now(timezone.utc)
    if now is None:
        now = datetime.now(timezone.utc)
    today = now.date()
    entries = list_daily_goal_history(profile_id, limit=365)
    by_day = {item.day_utc: item for item in entries}
    today_count = by_day.get(today.isoformat()).completions if today.isoformat() in by_day else 0

    streak = 0
    cursor = today
    while True:
        item = by_day.get(cursor.isoformat())
        if item is None or int(item.completions) <= 0:
            break
        streak += 1
        cursor = cursor.fromordinal(cursor.toordinal() - 1)
    return today_count, streak

