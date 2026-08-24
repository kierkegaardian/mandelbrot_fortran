from __future__ import annotations

from datetime import datetime, timezone
import sqlite3
import uuid

from ..models import Assignment
from ._util import _parse_iso_utc, _sync_now_text
from .connection import managed_connection

def create_assignment(
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
    with managed_connection() as conn:
        cur = conn.execute(
            """
            INSERT INTO assignments
            (profile_id, skill, subskill, target_type, target_value, level, num_questions, question_type,
             mode_intuition_pct, mode_expression_pct, mode_word_pct, notes, created_at,
             sync_id, sync_updated_at, sync_deleted)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
            """,
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
        return int(cur.lastrowid)


def list_assignments(
    profile_id: int,
    active_only: bool | None = True,
    *,
    skill: str | None = None,
    target_type: str | None = None,
    limit: int | None = None,
) -> list[Assignment]:
    clauses: list[str] = ["profile_id = ?", "sync_deleted = 0"]
    params: list[object] = [int(profile_id)]
    if active_only is True:
        clauses.append("active = 1")
    elif active_only is False:
        clauses.append("active = 0")
    if skill is not None:
        clauses.append("skill = ?")
        params.append(str(skill))
    if target_type is not None:
        clauses.append("target_type = ?")
        params.append(str(target_type))
    where_sql = " AND ".join(clauses)
    if active_only is True:
        order_sql = "created_at ASC, id ASC"
    elif active_only is False:
        order_sql = "completed_at DESC, id DESC"
    else:
        order_sql = "active DESC, created_at DESC, id DESC"
    limit_sql = ""
    if limit is not None:
        limit_sql = " LIMIT ?"
        params.append(max(1, int(limit)))
    with managed_connection() as conn:
        rows = conn.execute(
            f"""
            SELECT id, profile_id, skill, subskill, target_type, target_value, level, num_questions, question_type,
                   mode_intuition_pct, mode_expression_pct, mode_word_pct,
                   active, notes, created_at, completed_at
            FROM assignments
            WHERE {where_sql}
            ORDER BY {order_sql}{limit_sql}
            """,
            tuple(params),
        ).fetchall()
    return [_row_to_assignment(r) for r in rows]


def assignment_completion_analytics(
    profile_id: int,
    recent_days: int = 30,
    now_iso_text: str | None = None,
) -> dict[str, object]:
    recent_days = max(1, int(recent_days))
    active_items = list_assignments(profile_id, active_only=True)
    done_items = list_assignments(profile_id, active_only=False)
    now = _parse_iso_utc(now_iso_text) if now_iso_text else datetime.now(timezone.utc)
    if now is None:
        now = datetime.now(timezone.utc)

    completed_recent = 0
    duration_hours: list[float] = []
    by_skill: dict[str, int] = {}
    for item in done_items:
        by_skill[item.skill] = by_skill.get(item.skill, 0) + 1
        if item.completed_at:
            completed_at = _parse_iso_utc(item.completed_at)
            if completed_at is not None:
                age_days = (now - completed_at).total_seconds() / 86400.0
                if age_days <= float(recent_days):
                    completed_recent += 1
        created_at = _parse_iso_utc(item.created_at)
        completed_at = _parse_iso_utc(item.completed_at)
        if created_at is not None and completed_at is not None and completed_at >= created_at:
            duration_hours.append((completed_at - created_at).total_seconds() / 3600.0)

    avg_completion_hours = sum(duration_hours) / float(len(duration_hours)) if duration_hours else None
    top_skills = sorted(by_skill.items(), key=lambda kv: (-kv[1], kv[0]))[:5]
    return {
        "active_count": len(active_items),
        "completed_count": len(done_items),
        "completed_recent_count": completed_recent,
        "avg_completion_hours": avg_completion_hours,
        "top_completed_skills": top_skills,
    }


def set_assignment_active(assignment_id: int, active: bool, completed_at: str | None = None) -> None:
    sync_updated_at = completed_at or _sync_now_text()
    with managed_connection() as conn:
        conn.execute(
            """
            UPDATE assignments
            SET active = ?, completed_at = ?, sync_updated_at = ?, sync_deleted = 0
            WHERE id = ?
            """,
            (
                1 if active else 0,
                completed_at if not active else None,
                sync_updated_at,
                int(assignment_id),
            ),
        )


def get_next_active_assignment(profile_id: int) -> Assignment | None:
    items = list_assignments(profile_id, active_only=True)
    return items[0] if items else None


def evaluate_assignments_for_attempt(profile_id: int, attempt_id: int, completed_at: str) -> int:
    return len(evaluate_assignments_for_attempt_ids(profile_id, attempt_id, completed_at))


def evaluate_assignments_for_attempt_ids(profile_id: int, attempt_id: int, completed_at: str) -> list[int]:
    completed_ids: list[int] = []
    with managed_connection() as conn:
        attempt = conn.execute(
            """
            SELECT id, profile_id, skill, score, num_questions
            FROM quiz_attempts
            WHERE id = ? AND profile_id = ? AND sync_deleted = 0
            """,
            (int(attempt_id), int(profile_id)),
        ).fetchone()
        if attempt is None:
            return []

        assignments = conn.execute(
            """
            SELECT id, skill, subskill, target_type, target_value
            FROM assignments
            WHERE profile_id = ? AND active = 1 AND sync_deleted = 0
            ORDER BY created_at ASC, id ASC
            """,
            (int(profile_id),),
        ).fetchall()

        for item in assignments:
            target_type = item["target_type"]
            skill = item["skill"]
            subskill = item["subskill"]
            target_value = float(item["target_value"])
            is_done = False
            if target_type == "quiz_score_pct":
                if skill != attempt["skill"]:
                    continue
                total = max(1, int(attempt["num_questions"]))
                pct = (float(attempt["score"]) / float(total)) * 100.0
                required_pct = max(100.0, target_value)
                is_done = pct >= required_pct
            elif target_type == "subskill_mastered":
                if not subskill:
                    continue
                row = conn.execute(
                    """
                    SELECT mastered
                    FROM skill_subskill_progress
                    WHERE profile_id = ? AND skill = ? AND subskill = ?
                    """,
                    (int(profile_id), skill, subskill),
                ).fetchone()
                is_done = bool(row and int(row["mastered"]) == 1)
            if is_done:
                conn.execute(
                    """
                    UPDATE assignments
                    SET active = 0, completed_at = ?, sync_updated_at = ?, sync_deleted = 0
                    WHERE id = ?
                    """,
                    (completed_at, completed_at, int(item["id"])),
                )
                completed_ids.append(int(item["id"]))
    return completed_ids

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
