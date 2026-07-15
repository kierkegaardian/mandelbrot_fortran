from __future__ import annotations

from datetime import datetime, timezone

from ..models import DailyGoalHistory
from .connection import managed_connection
from ._util import _iso_day_utc, _parse_iso_utc


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
