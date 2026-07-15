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
        None,
    )


def list_worksheets(
    profile_id: int | None = None,
    *,
    skill_prefix: str | None = None,
    include_archived: bool = False,
    limit: int = 100,
) -> list[Worksheet]:
    clauses: list[str] = []
    params: list[object] = []
    if profile_id is not None:
        clauses.append("profile_id = ?")
        params.append(int(profile_id))
    if skill_prefix is not None:
        clauses.append("skill LIKE ?")
        params.append(f"{skill_prefix}%")
    if not include_archived:
        clauses.append("archived_at IS NULL")
    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    params.append(max(1, int(limit)))
    with managed_connection() as conn:
        rows = conn.execute(
            f"""
            SELECT id, profile_id, quiz_set_id, skill, question_type, num_questions, level, file_path, created_at, archived_at
            FROM worksheets
            {where}
            ORDER BY created_at DESC, id DESC
            LIMIT ?
            """,
            tuple(params),
        ).fetchall()
    return [
        Worksheet(
            int(r["id"]),
            int(r["profile_id"]),
            int(r["quiz_set_id"]) if r["quiz_set_id"] is not None else None,
            str(r["skill"]),
            str(r["question_type"]),
            int(r["num_questions"]),
            int(r["level"]),
            str(r["file_path"]),
            str(r["created_at"]),
            str(r["archived_at"]) if r["archived_at"] is not None else None,
        )
        for r in rows
    ]


def archive_worksheet(
    worksheet_id: int,
    *,
    profile_id: int | None = None,
    archived_at: str,
) -> bool:
    clauses = ["id = ?", "archived_at IS NULL"]
    params: list[object] = [int(worksheet_id)]
    if profile_id is not None:
        clauses.append("profile_id = ?")
        params.append(int(profile_id))
    params.insert(0, archived_at)
    with managed_connection() as conn:
        cur = conn.execute(
            f"""
            UPDATE worksheets
            SET archived_at = ?
            WHERE {' AND '.join(clauses)}
            """,
            tuple(params),
        )
        return int(cur.rowcount) > 0
