from __future__ import annotations

import sqlite3

from ..models import SummerProgram
from .connection import managed_connection

def create_summer_program(
    *,
    profile_id: int,
    lane: str,
    start_date: str,
    end_date: str,
    days_per_week: int,
    minutes_per_session: int,
    status: str,
    finish_definition: str,
    placement_recommendation: str | None,
    placement_review_status: str,
    placement_reviewed_at: str | None,
    student_age_years: int | None,
    created_at: str,
    updated_at: str,
) -> SummerProgram:
    with managed_connection() as conn:
        cur = conn.execute(
            """
            INSERT INTO summer_programs
            (profile_id, lane, start_date, end_date, days_per_week, minutes_per_session, status,
             finish_definition, placement_recommendation, placement_review_status, placement_reviewed_at,
             student_age_years, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                int(profile_id),
                lane,
                start_date,
                end_date,
                int(days_per_week),
                int(minutes_per_session),
                status,
                finish_definition,
                placement_recommendation,
                placement_review_status,
                placement_reviewed_at,
                int(student_age_years) if student_age_years is not None else None,
                created_at,
                updated_at,
            ),
        )
        program_id = int(cur.lastrowid)
    program = get_summer_program(program_id)
    assert program is not None
    return program


_SUMMER_PROGRAM_UNSET = object()


def update_summer_program(
    program_id: int,
    *,
    lane: str | object = _SUMMER_PROGRAM_UNSET,
    status: str | object = _SUMMER_PROGRAM_UNSET,
    placement_recommendation: str | None | object = _SUMMER_PROGRAM_UNSET,
    placement_review_status: str | object = _SUMMER_PROGRAM_UNSET,
    placement_reviewed_at: str | None | object = _SUMMER_PROGRAM_UNSET,
    updated_at: str,
) -> None:
    assignments = ["updated_at = ?"]
    params: list[object] = [updated_at]
    if lane is not _SUMMER_PROGRAM_UNSET:
        assignments.append("lane = ?")
        params.append(lane)
    if status is not _SUMMER_PROGRAM_UNSET:
        assignments.append("status = ?")
        params.append(status)
    if placement_recommendation is not _SUMMER_PROGRAM_UNSET:
        assignments.append("placement_recommendation = ?")
        params.append(placement_recommendation)
    if placement_review_status is not _SUMMER_PROGRAM_UNSET:
        assignments.append("placement_review_status = ?")
        params.append(placement_review_status)
    if placement_reviewed_at is not _SUMMER_PROGRAM_UNSET:
        assignments.append("placement_reviewed_at = ?")
        params.append(placement_reviewed_at)
    params.append(int(program_id))
    with managed_connection() as conn:
        conn.execute(
            f"UPDATE summer_programs SET {', '.join(assignments)} WHERE id = ?",
            tuple(params),
        )


def archive_summer_programs(profile_id: int, *, archived_at: str) -> None:
    with managed_connection() as conn:
        conn.execute(
            """
            UPDATE summer_programs
            SET status = 'archived', updated_at = ?
            WHERE profile_id = ? AND status IN ('active', 'completed')
            """,
            (archived_at, int(profile_id)),
        )


def get_summer_program(program_id: int) -> SummerProgram | None:
    with managed_connection() as conn:
        row = conn.execute(
            """
            SELECT id, profile_id, lane, start_date, end_date, days_per_week, minutes_per_session,
                   status, finish_definition, placement_recommendation, placement_review_status,
                   placement_reviewed_at, student_age_years, created_at, updated_at
            FROM summer_programs
            WHERE id = ?
            """,
            (int(program_id),),
        ).fetchone()
    return _row_to_summer_program(row) if row is not None else None


def get_active_summer_program(profile_id: int) -> SummerProgram | None:
    with managed_connection() as conn:
        row = conn.execute(
            """
            SELECT id, profile_id, lane, start_date, end_date, days_per_week, minutes_per_session,
                   status, finish_definition, placement_recommendation, placement_review_status,
                   placement_reviewed_at, student_age_years, created_at, updated_at
            FROM summer_programs
            WHERE profile_id = ? AND status IN ('active', 'completed')
            ORDER BY updated_at DESC, id DESC
            LIMIT 1
            """,
            (int(profile_id),),
        ).fetchone()
    return _row_to_summer_program(row) if row is not None else None


def list_summer_programs(profile_id: int, *, include_inactive: bool = False) -> list[SummerProgram]:
    where_sql = "profile_id = ?" if include_inactive else "profile_id = ? AND status IN ('active', 'completed')"
    with managed_connection() as conn:
        rows = conn.execute(
            f"""
            SELECT id, profile_id, lane, start_date, end_date, days_per_week, minutes_per_session,
                   status, finish_definition, placement_recommendation, placement_review_status,
                   placement_reviewed_at, student_age_years, created_at, updated_at
            FROM summer_programs
            WHERE {where_sql}
            ORDER BY updated_at DESC, id DESC
            """,
            (int(profile_id),),
        ).fetchall()
    return [_row_to_summer_program(row) for row in rows]

def _row_to_summer_program(r: sqlite3.Row) -> SummerProgram:
    return SummerProgram(
        id=int(r["id"]),
        profile_id=int(r["profile_id"]),
        lane=str(r["lane"]),
        start_date=str(r["start_date"]),
        end_date=str(r["end_date"]),
        days_per_week=int(r["days_per_week"]),
        minutes_per_session=int(r["minutes_per_session"]),
        status=str(r["status"]),
        finish_definition=str(r["finish_definition"]),
        placement_recommendation=str(r["placement_recommendation"]) if r["placement_recommendation"] is not None else None,
        placement_review_status=str(r["placement_review_status"] or "accepted"),
        placement_reviewed_at=str(r["placement_reviewed_at"]) if r["placement_reviewed_at"] is not None else None,
        student_age_years=int(r["student_age_years"]) if r["student_age_years"] is not None else None,
        created_at=str(r["created_at"]),
        updated_at=str(r["updated_at"]),
    )

