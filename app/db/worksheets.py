from __future__ import annotations

from typing import Optional

from ..models import Worksheet
from .connection import managed_connection


def create_worksheet(
    profile_id: int,
    quiz_set_id: Optional[int],
    skill: str,
    question_type: str,
    num_questions: int,
    level: int,
    file_path: str,
    created_at: str,
) -> Worksheet:
    with managed_connection() as conn:
        cur = conn.execute(
            """
            INSERT INTO worksheets
            (profile_id, quiz_set_id, skill, question_type, num_questions, level, file_path, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (profile_id, quiz_set_id, skill, question_type, num_questions, level, file_path, created_at),
        )
        worksheet_id = int(cur.lastrowid)
    return Worksheet(
        worksheet_id,
        profile_id,
        quiz_set_id,
        skill,
        question_type,
        num_questions,
        level,
        file_path,
        created_at,
    )

def skill_progress_pipeline(profile_id: int) -> dict[str, dict[str, int]]:
    out: dict[str, dict[str, int]] = {}
    with managed_connection() as conn:
        attempt_rows = conn.execute(
            """
            SELECT skill, COUNT(*) AS attempts, SUM(num_questions) AS questions
            FROM quiz_attempts
            WHERE profile_id = ?
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
