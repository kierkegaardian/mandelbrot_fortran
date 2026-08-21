from __future__ import annotations

import sqlite3

from ..models import SummerAssessmentRun
from .connection import managed_connection

def record_summer_assessment(
    *,
    program_id: int,
    assessment_type: str,
    score_pct: float,
    passed: bool,
    strand_results_json: str,
    completed_at: str,
) -> SummerAssessmentRun:
    with managed_connection() as conn:
        cur = conn.execute(
            """
            INSERT INTO summer_assessment_runs
            (program_id, assessment_type, score_pct, passed, strand_results_json, completed_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                int(program_id),
                assessment_type,
                float(score_pct),
                1 if passed else 0,
                strand_results_json,
                completed_at,
            ),
        )
        assessment_id = int(cur.lastrowid)
    run = get_summer_assessment_run(assessment_id)
    assert run is not None
    return run


def get_summer_assessment_run(assessment_id: int) -> SummerAssessmentRun | None:
    with managed_connection() as conn:
        row = conn.execute(
            """
            SELECT id, program_id, assessment_type, score_pct, passed, strand_results_json, completed_at
            FROM summer_assessment_runs
            WHERE id = ?
            """,
            (int(assessment_id),),
        ).fetchone()
    return _row_to_summer_assessment_run(row) if row is not None else None


def list_summer_assessment_runs(program_id: int) -> list[SummerAssessmentRun]:
    with managed_connection() as conn:
        rows = conn.execute(
            """
            SELECT id, program_id, assessment_type, score_pct, passed, strand_results_json, completed_at
            FROM summer_assessment_runs
            WHERE program_id = ?
            ORDER BY completed_at ASC, id ASC
            """,
            (int(program_id),),
        ).fetchall()
    return [_row_to_summer_assessment_run(row) for row in rows]

def _row_to_summer_assessment_run(r: sqlite3.Row) -> SummerAssessmentRun:
    return SummerAssessmentRun(
        id=int(r["id"]),
        program_id=int(r["program_id"]),
        assessment_type=str(r["assessment_type"]),
        score_pct=float(r["score_pct"]),
        passed=bool(r["passed"]),
        strand_results_json=str(r["strand_results_json"]),
        completed_at=str(r["completed_at"]),
    )
