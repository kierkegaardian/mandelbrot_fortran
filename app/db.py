from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from typing import Optional

from .models import Profile, QuizAttempt, QuizSet, SubskillProgress, Worksheet
from .paths import data_dir


@dataclass(frozen=True)
class DbConfig:
    path: str


def db_config() -> DbConfig:
    db_path = data_dir() / "app.db"
    return DbConfig(path=str(db_path))


def connect() -> sqlite3.Connection:
    cfg = db_config()
    conn = sqlite3.connect(cfg.path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db() -> None:
    with connect() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS profiles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                role TEXT NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS quiz_sets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                skill TEXT NOT NULL,
                question_type TEXT NOT NULL,
                num_questions INTEGER NOT NULL,
                level INTEGER NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS quiz_attempts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                profile_id INTEGER NOT NULL,
                quiz_set_id INTEGER,
                skill TEXT NOT NULL,
                question_type TEXT NOT NULL,
                num_questions INTEGER NOT NULL,
                level INTEGER NOT NULL,
                score INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY(profile_id) REFERENCES profiles(id) ON DELETE CASCADE,
                FOREIGN KEY(quiz_set_id) REFERENCES quiz_sets(id) ON DELETE SET NULL
            );

            CREATE TABLE IF NOT EXISTS quiz_questions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                attempt_id INTEGER NOT NULL,
                skill TEXT NOT NULL,
                prompt TEXT NOT NULL,
                correct_answer TEXT NOT NULL,
                user_answer TEXT NOT NULL,
                is_correct INTEGER NOT NULL,
                explanation TEXT NOT NULL,
                FOREIGN KEY(attempt_id) REFERENCES quiz_attempts(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS worksheets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                profile_id INTEGER NOT NULL,
                quiz_set_id INTEGER,
                skill TEXT NOT NULL,
                question_type TEXT NOT NULL,
                num_questions INTEGER NOT NULL,
                level INTEGER NOT NULL,
                file_path TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY(profile_id) REFERENCES profiles(id) ON DELETE CASCADE,
                FOREIGN KEY(quiz_set_id) REFERENCES quiz_sets(id) ON DELETE SET NULL
            );

            CREATE TABLE IF NOT EXISTS skill_subskill_progress (
                profile_id INTEGER NOT NULL,
                skill TEXT NOT NULL,
                subskill TEXT NOT NULL,
                current_streak INTEGER NOT NULL DEFAULT 0,
                best_streak INTEGER NOT NULL DEFAULT 0,
                mastered INTEGER NOT NULL DEFAULT 0,
                updated_at TEXT NOT NULL,
                PRIMARY KEY (profile_id, skill, subskill),
                FOREIGN KEY(profile_id) REFERENCES profiles(id) ON DELETE CASCADE
            );
            """
        )


def list_profiles() -> list[Profile]:
    with connect() as conn:
        rows = conn.execute(
            "SELECT id, name, role FROM profiles ORDER BY role DESC, name ASC"
        ).fetchall()
    return [Profile(int(r["id"]), r["name"], r["role"]) for r in rows]


def create_profile(name: str, role: str, created_at: str) -> Profile:
    if role not in {"child", "parent"}:
        raise ValueError("role must be 'child' or 'parent'")
    with connect() as conn:
        cur = conn.execute(
            "INSERT INTO profiles (name, role, created_at) VALUES (?, ?, ?)",
            (name, role, created_at),
        )
        profile_id = int(cur.lastrowid)
    return Profile(profile_id, name, role)


def delete_profile(profile_id: int) -> None:
    with connect() as conn:
        conn.execute("DELETE FROM profiles WHERE id = ?", (profile_id,))


def list_quiz_sets() -> list[QuizSet]:
    with connect() as conn:
        rows = conn.execute(
            "SELECT id, name, skill, question_type, num_questions, level FROM quiz_sets ORDER BY name"
        ).fetchall()
    return [
        QuizSet(
            int(r["id"]),
            r["name"],
            r["skill"],
            r["question_type"],
            int(r["num_questions"]),
            int(r["level"]),
        )
        for r in rows
    ]


def create_quiz_set(
    name: str, skill: str, question_type: str, num_questions: int, level: int, created_at: str
) -> QuizSet:
    with connect() as conn:
        cur = conn.execute(
            """
            INSERT INTO quiz_sets (name, skill, question_type, num_questions, level, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (name, skill, question_type, num_questions, level, created_at),
        )
        quiz_set_id = int(cur.lastrowid)
    return QuizSet(quiz_set_id, name, skill, question_type, num_questions, level)


def delete_quiz_set(quiz_set_id: int) -> None:
    with connect() as conn:
        conn.execute("DELETE FROM quiz_sets WHERE id = ?", (quiz_set_id,))


def update_quiz_set(
    quiz_set_id: int,
    name: str,
    skill: str,
    question_type: str,
    num_questions: int,
    level: int,
) -> None:
    with connect() as conn:
        conn.execute(
            """
            UPDATE quiz_sets
            SET name = ?, skill = ?, question_type = ?, num_questions = ?, level = ?
            WHERE id = ?
            """,
            (name, skill, question_type, num_questions, level, quiz_set_id),
        )


def create_attempt(
    profile_id: int,
    quiz_set_id: Optional[int],
    skill: str,
    question_type: str,
    num_questions: int,
    level: int,
    score: int,
    created_at: str,
) -> int:
    with connect() as conn:
        cur = conn.execute(
            """
            INSERT INTO quiz_attempts
            (profile_id, quiz_set_id, skill, question_type, num_questions, level, score, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (profile_id, quiz_set_id, skill, question_type, num_questions, level, score, created_at),
        )
        return int(cur.lastrowid)


def add_question_result(
    attempt_id: int,
    skill: str,
    prompt: str,
    correct_answer: str,
    user_answer: str,
    is_correct: bool,
    explanation: str,
) -> None:
    with connect() as conn:
        conn.execute(
            """
            INSERT INTO quiz_questions
            (attempt_id, skill, prompt, correct_answer, user_answer, is_correct, explanation)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (attempt_id, skill, prompt, correct_answer, user_answer, int(is_correct), explanation),
        )


def list_attempts(profile_id: int) -> list[QuizAttempt]:
    with connect() as conn:
        rows = conn.execute(
            """
            SELECT id, profile_id, quiz_set_id, skill, question_type, num_questions, level, score, created_at
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
        )
        for r in rows
    ]


def upsert_subskill_progress(
    profile_id: int, skill: str, subskill: str, is_correct: bool, updated_at: str, streak_to_master: int
) -> None:
    with connect() as conn:
        row = conn.execute(
            """
            SELECT current_streak, best_streak, mastered
            FROM skill_subskill_progress
            WHERE profile_id = ? AND skill = ? AND subskill = ?
            """,
            (profile_id, skill, subskill),
        ).fetchone()
        if row is None:
            current_streak = 1 if is_correct else 0
            best_streak = current_streak
            mastered = 1 if is_correct and current_streak >= streak_to_master else 0
            conn.execute(
                """
                INSERT INTO skill_subskill_progress
                (profile_id, skill, subskill, current_streak, best_streak, mastered, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    profile_id,
                    skill,
                    subskill,
                    current_streak,
                    best_streak,
                    mastered,
                    updated_at,
                ),
            )
            return

        current_streak = row["current_streak"] + 1 if is_correct else 0
        best_streak = max(row["best_streak"], current_streak)
        mastered = 1 if row["mastered"] or current_streak >= streak_to_master else 0
        conn.execute(
            """
            UPDATE skill_subskill_progress
            SET current_streak = ?, best_streak = ?, mastered = ?, updated_at = ?
            WHERE profile_id = ? AND skill = ? AND subskill = ?
            """,
            (
                current_streak,
                best_streak,
                mastered,
                updated_at,
                profile_id,
                skill,
                subskill,
            ),
        )


def list_subskill_progress(profile_id: int, skill: str | None = None) -> list[SubskillProgress]:
    with connect() as conn:
        if skill is None:
            rows = conn.execute(
                """
                SELECT profile_id, skill, subskill, current_streak, best_streak, mastered
                FROM skill_subskill_progress
                WHERE profile_id = ?
                ORDER BY skill ASC, subskill ASC
                """,
                (profile_id,),
            ).fetchall()
        else:
            rows = conn.execute(
                """
                SELECT profile_id, skill, subskill, current_streak, best_streak, mastered
                FROM skill_subskill_progress
                WHERE profile_id = ? AND skill = ?
                ORDER BY subskill ASC
                """,
                (profile_id, skill),
            ).fetchall()
    return [
        SubskillProgress(
            int(r["profile_id"]),
            r["skill"],
            r["subskill"],
            int(r["current_streak"]),
            int(r["best_streak"]),
            bool(r["mastered"]),
        )
        for r in rows
    ]


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
    with connect() as conn:
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
