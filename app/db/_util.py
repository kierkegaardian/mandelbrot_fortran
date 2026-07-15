from __future__ import annotations

from datetime import datetime, timezone
import sqlite3

from ..models import Assignment


def _row_to_assignment(r: sqlite3.Row) -> Assignment:
    return Assignment(
        id=int(r["id"]),
        profile_id=int(r["profile_id"]),
        skill=r["skill"],
        subskill=r["subskill"],
        target_type=r["target_type"],
        target_value=float(r["target_value"]),
        level=int(r["level"]),
        num_questions=int(r["num_questions"]),
        question_type=r["question_type"],
        mode_intuition_pct=int(r["mode_intuition_pct"]) if r["mode_intuition_pct"] is not None else None,
        mode_expression_pct=int(r["mode_expression_pct"]) if r["mode_expression_pct"] is not None else None,
        mode_word_pct=int(r["mode_word_pct"]) if r["mode_word_pct"] is not None else None,
        active=bool(r["active"]),
        notes=r["notes"],
        created_at=r["created_at"],
        completed_at=r["completed_at"],
    )

def _parse_iso_utc(value: str | None) -> datetime | None:
    if value is None:
        return None
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)

def _iso_day_utc(value: str) -> str:
    parsed = _parse_iso_utc(value)
    if parsed is None:
        return datetime.now(timezone.utc).date().isoformat()
    return parsed.date().isoformat()
