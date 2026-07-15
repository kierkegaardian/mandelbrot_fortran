from __future__ import annotations

from typing import Optional

from ..models import QuizAttempt
from .connection import managed_connection


def create_attempt(
    profile_id: int,
    quiz_set_id: Optional[int],
    skill: str,
    question_type: str,
    num_questions: int,
    level: int,
    score: int,
    created_at: str,
    elapsed_seconds: float | None = None,
) -> int:
    with managed_connection() as conn:
        cur = conn.execute(
            """
            INSERT INTO quiz_attempts
            (profile_id, quiz_set_id, skill, question_type, num_questions, level, score, elapsed_seconds, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                profile_id,
                quiz_set_id,
                skill,
                question_type,
                num_questions,
                level,
                score,
                None if elapsed_seconds is None else float(elapsed_seconds),
                created_at,
            ),
        )
        return int(cur.lastrowid)

def add_question_result(
    attempt_id: int,
    skill: str,
    question_label: str,
    mode: str,
    prompt: str,
    correct_answer: str,
    user_answer: str,
    is_correct: bool,
    explanation: str,
) -> None:
    with managed_connection() as conn:
        conn.execute(
            """
            INSERT INTO quiz_questions
            (attempt_id, skill, question_label, mode, prompt, correct_answer, user_answer, is_correct, explanation)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                attempt_id,
                skill,
                question_label,
                mode,
                prompt,
                correct_answer,
                user_answer,
                int(is_correct),
                explanation,
            ),
        )

def list_attempts(profile_id: int) -> list[QuizAttempt]:
    with managed_connection() as conn:
        rows = conn.execute(
            """
            SELECT id, profile_id, quiz_set_id, skill, question_type, num_questions, level, score, elapsed_seconds, created_at
            FROM quiz_attempts
            WHERE profile_id = ?
            ORDER BY created_at DESC
            """,
            (profile_id,),
        ).fetchall()
    return [
        QuizAttempt(
            int(r["id"]),
            int(r["profile_id"]),
            int(r["quiz_set_id"]) if r["quiz_set_id"] is not None else None,
            r["skill"],
            r["question_type"],
            int(r["num_questions"]),
            int(r["level"]),
            int(r["score"]),
            r["created_at"],
            float(r["elapsed_seconds"]) if r["elapsed_seconds"] is not None else None,
        )
        for r in rows
    ]

def mode_accuracy_by_skill(profile_id: int, skill: str) -> dict[str, float]:
    with managed_connection() as conn:
        rows = conn.execute(
            """
            SELECT qq.mode AS mode, COUNT(*) AS total, SUM(qq.is_correct) AS correct
            FROM quiz_questions qq
            JOIN quiz_attempts qa ON qa.id = qq.attempt_id
            WHERE qa.profile_id = ? AND qq.skill = ?
            GROUP BY qq.mode
            """,
            (int(profile_id), skill),
        ).fetchall()
    out: dict[str, float] = {}
    for row in rows:
        total = max(1, int(row["total"]))
        correct = int(row["correct"] or 0)
        out[str(row["mode"])] = (float(correct) / float(total)) * 100.0
    return out
