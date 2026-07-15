from __future__ import annotations

from ..models import QuizSet
from .connection import managed_connection


def list_quiz_sets() -> list[QuizSet]:
    with managed_connection() as conn:
        rows = conn.execute(
            """
            SELECT id, name, skill, question_type, num_questions, level,
                   mode_intuition_pct, mode_expression_pct, mode_word_pct
            FROM quiz_sets
            ORDER BY name
            """
        ).fetchall()
    return [
        QuizSet(
            int(r["id"]),
            r["name"],
            r["skill"],
            r["question_type"],
            int(r["num_questions"]),
            int(r["level"]),
            int(r["mode_intuition_pct"]) if r["mode_intuition_pct"] is not None else None,
            int(r["mode_expression_pct"]) if r["mode_expression_pct"] is not None else None,
            int(r["mode_word_pct"]) if r["mode_word_pct"] is not None else None,
        )
        for r in rows
    ]

def create_quiz_set(
    name: str,
    skill: str,
    question_type: str,
    num_questions: int,
    level: int,
    created_at: str,
    mode_intuition_pct: int | None = None,
    mode_expression_pct: int | None = None,
    mode_word_pct: int | None = None,
) -> QuizSet:
    with managed_connection() as conn:
        cur = conn.execute(
            """
            INSERT INTO quiz_sets
            (name, skill, question_type, num_questions, level, mode_intuition_pct, mode_expression_pct, mode_word_pct, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                name,
                skill,
                question_type,
                num_questions,
                level,
                mode_intuition_pct,
                mode_expression_pct,
                mode_word_pct,
                created_at,
            ),
        )
        quiz_set_id = int(cur.lastrowid)
    return QuizSet(
        quiz_set_id,
        name,
        skill,
        question_type,
        num_questions,
        level,
        mode_intuition_pct,
        mode_expression_pct,
        mode_word_pct,
    )

def delete_quiz_set(quiz_set_id: int) -> None:
    with managed_connection() as conn:
        conn.execute("DELETE FROM quiz_sets WHERE id = ?", (quiz_set_id,))

def update_quiz_set(
    quiz_set_id: int,
    name: str,
    skill: str,
    question_type: str,
    num_questions: int,
    level: int,
    mode_intuition_pct: int | None = None,
    mode_expression_pct: int | None = None,
    mode_word_pct: int | None = None,
) -> None:
    with managed_connection() as conn:
        conn.execute(
            """
            UPDATE quiz_sets
            SET name = ?, skill = ?, question_type = ?, num_questions = ?, level = ?,
                mode_intuition_pct = ?, mode_expression_pct = ?, mode_word_pct = ?
            WHERE id = ?
            """,
            (
                name,
                skill,
                question_type,
                num_questions,
                level,
                mode_intuition_pct,
                mode_expression_pct,
                mode_word_pct,
                quiz_set_id,
            ),
        )
