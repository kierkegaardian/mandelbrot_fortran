from __future__ import annotations

import sqlite3

from ..models import SummerProgramTask
from .connection import managed_connection

def replace_summer_program_tasks(program_id: int, payloads: list[dict[str, object]], *, updated_at: str) -> None:
    with managed_connection() as conn:
        conn.execute("DELETE FROM summer_program_tasks WHERE program_id = ?", (int(program_id),))
        for item in payloads:
            conn.execute(
                """
                INSERT INTO summer_program_tasks
                (program_id, unit_code, task_kind, skill, subskill, sequence_index, status,
                 target_score_pct, scheduled_date, notes_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    int(program_id),
                    str(item["unit_code"]),
                    str(item["task_kind"]),
                    str(item["skill"]),
                    item.get("subskill"),
                    int(item["sequence_index"]),
                    str(item["status"]),
                    float(item["target_score_pct"]) if item.get("target_score_pct") is not None else None,
                    str(item["scheduled_date"]),
                    str(item.get("notes_json", "{}")),
                ),
            )
        conn.execute(
            "UPDATE summer_programs SET updated_at = ? WHERE id = ?",
            (updated_at, int(program_id)),
        )


def create_summer_program_task(
    *,
    program_id: int,
    unit_code: str,
    task_kind: str,
    skill: str,
    subskill: str | None,
    sequence_index: int,
    status: str,
    target_score_pct: float | None,
    scheduled_date: str,
    notes_json: str = "{}",
) -> SummerProgramTask:
    with managed_connection() as conn:
        cur = conn.execute(
            """
            INSERT INTO summer_program_tasks
            (program_id, unit_code, task_kind, skill, subskill, sequence_index, status,
             target_score_pct, scheduled_date, notes_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                int(program_id),
                unit_code,
                task_kind,
                skill,
                subskill,
                int(sequence_index),
                status,
                float(target_score_pct) if target_score_pct is not None else None,
                scheduled_date,
                notes_json,
            ),
        )
        task_id = int(cur.lastrowid)
    task = get_summer_program_task(task_id)
    assert task is not None
    return task


def shift_summer_program_task_sequences(program_id: int, *, starting_from: int, delta: int) -> None:
    if delta == 0:
        return
    with managed_connection() as conn:
        conn.execute(
            """
            UPDATE summer_program_tasks
            SET sequence_index = sequence_index + ?
            WHERE program_id = ? AND sequence_index >= ?
            """,
            (int(delta), int(program_id), int(starting_from)),
        )


def get_summer_program_task(task_id: int) -> SummerProgramTask | None:
    with managed_connection() as conn:
        row = conn.execute(
            """
            SELECT id, program_id, unit_code, task_kind, skill, subskill, sequence_index, status,
                   target_score_pct, scheduled_date, notes_json
            FROM summer_program_tasks
            WHERE id = ?
            """,
            (int(task_id),),
        ).fetchone()
    return _row_to_summer_program_task(row) if row is not None else None


def list_summer_program_tasks(program_id: int) -> list[SummerProgramTask]:
    with managed_connection() as conn:
        rows = conn.execute(
            """
            SELECT id, program_id, unit_code, task_kind, skill, subskill, sequence_index, status,
                   target_score_pct, scheduled_date, notes_json
            FROM summer_program_tasks
            WHERE program_id = ?
            ORDER BY sequence_index ASC, id ASC
            """,
            (int(program_id),),
        ).fetchall()
    return [_row_to_summer_program_task(row) for row in rows]


_SUMMER_PROGRAM_TASK_UNSET = object()


def update_summer_program_task(
    task_id: int,
    *,
    status: str | object = _SUMMER_PROGRAM_TASK_UNSET,
    notes_json: str | object = _SUMMER_PROGRAM_TASK_UNSET,
    scheduled_date: str | object = _SUMMER_PROGRAM_TASK_UNSET,
) -> None:
    assignments: list[str] = []
    params: list[object] = []
    if status is not _SUMMER_PROGRAM_TASK_UNSET:
        assignments.append("status = ?")
        params.append(status)
    if notes_json is not _SUMMER_PROGRAM_TASK_UNSET:
        assignments.append("notes_json = ?")
        params.append(notes_json)
    if scheduled_date is not _SUMMER_PROGRAM_TASK_UNSET:
        assignments.append("scheduled_date = ?")
        params.append(scheduled_date)
    if not assignments:
        return
    params.append(int(task_id))
    with managed_connection() as conn:
        conn.execute(
            """
            UPDATE summer_program_tasks
            SET {assignments}
            WHERE id = ?
            """.replace("{assignments}", ", ".join(assignments)),
            tuple(params),
        )

def _row_to_summer_program_task(r: sqlite3.Row) -> SummerProgramTask:
    return SummerProgramTask(
        id=int(r["id"]),
        program_id=int(r["program_id"]),
        unit_code=str(r["unit_code"]),
        task_kind=str(r["task_kind"]),
        skill=str(r["skill"]),
        subskill=str(r["subskill"]) if r["subskill"] is not None else None,
        sequence_index=int(r["sequence_index"]),
        status=str(r["status"]),
        target_score_pct=float(r["target_score_pct"]) if r["target_score_pct"] is not None else None,
        scheduled_date=str(r["scheduled_date"]),
        notes_json=str(r["notes_json"]),
    )
