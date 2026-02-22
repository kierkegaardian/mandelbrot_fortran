from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from dataclasses import dataclass
from typing import Optional

from .models import (
    Assignment,
    Book,
    DailyGoalHistory,
    ExerciseCandidate,
    HistoricalQuestion,
    HistoricalTest,
    Profile,
    QuestionTemplate,
    QuizAttempt,
    QuizSet,
    SubskillProgress,
    TemplateVar,
    Worksheet,
)
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
                mode_intuition_pct INTEGER,
                mode_expression_pct INTEGER,
                mode_word_pct INTEGER,
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
                elapsed_seconds REAL,
                created_at TEXT NOT NULL,
                FOREIGN KEY(profile_id) REFERENCES profiles(id) ON DELETE CASCADE,
                FOREIGN KEY(quiz_set_id) REFERENCES quiz_sets(id) ON DELETE SET NULL
            );

            CREATE TABLE IF NOT EXISTS quiz_questions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                attempt_id INTEGER NOT NULL,
                skill TEXT NOT NULL,
                question_label TEXT NOT NULL DEFAULT 'Core',
                mode TEXT NOT NULL DEFAULT 'expression',
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

            CREATE TABLE IF NOT EXISTS books (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                source TEXT NOT NULL,
                pdf_filename TEXT NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS exercise_candidates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                book_id INTEGER NOT NULL,
                location TEXT NOT NULL,
                text TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'new',
                created_at TEXT NOT NULL,
                FOREIGN KEY(book_id) REFERENCES books(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS question_templates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                book_id INTEGER,
                external_id TEXT,
                skill TEXT NOT NULL,
                subskill TEXT NOT NULL,
                label TEXT NOT NULL,
                mode TEXT NOT NULL DEFAULT 'expression',
                prompt_template TEXT NOT NULL,
                answer_expr TEXT NOT NULL,
                constraint_expr TEXT NOT NULL DEFAULT '',
                explanation_template TEXT NOT NULL,
                min_level INTEGER NOT NULL DEFAULT 1,
                max_level INTEGER NOT NULL DEFAULT 3,
                choice_spread REAL NOT NULL DEFAULT 4.0,
                active INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL,
                FOREIGN KEY(book_id) REFERENCES books(id) ON DELETE SET NULL
            );

            CREATE TABLE IF NOT EXISTS template_vars (
                template_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                kind TEXT NOT NULL,
                min_value REAL NOT NULL,
                max_value REAL NOT NULL,
                step REAL NOT NULL DEFAULT 1,
                PRIMARY KEY (template_id, name),
                FOREIGN KEY(template_id) REFERENCES question_templates(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS assignments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                profile_id INTEGER NOT NULL,
                skill TEXT NOT NULL,
                subskill TEXT,
                target_type TEXT NOT NULL,
                target_value REAL NOT NULL DEFAULT 0,
                level INTEGER NOT NULL DEFAULT 1,
                num_questions INTEGER NOT NULL DEFAULT 5,
                question_type TEXT NOT NULL DEFAULT 'both',
                mode_intuition_pct INTEGER,
                mode_expression_pct INTEGER,
                mode_word_pct INTEGER,
                active INTEGER NOT NULL DEFAULT 1,
                notes TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL,
                completed_at TEXT,
                FOREIGN KEY(profile_id) REFERENCES profiles(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS daily_goal_history (
                profile_id INTEGER NOT NULL,
                day_utc TEXT NOT NULL,
                completions INTEGER NOT NULL DEFAULT 0,
                last_completed_at TEXT NOT NULL,
                PRIMARY KEY (profile_id, day_utc),
                FOREIGN KEY(profile_id) REFERENCES profiles(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS historical_tests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                exam_code TEXT NOT NULL UNIQUE,
                title TEXT NOT NULL,
                exam_type TEXT NOT NULL,
                year INTEGER,
                pdf_path TEXT NOT NULL,
                source TEXT NOT NULL DEFAULT 'historical_pdf',
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS historical_questions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                test_id INTEGER NOT NULL,
                question_number INTEGER NOT NULL,
                section TEXT NOT NULL DEFAULT 'General',
                category TEXT NOT NULL DEFAULT 'unknown',
                prompt TEXT NOT NULL,
                choice_a TEXT,
                choice_b TEXT,
                choice_c TEXT,
                choice_d TEXT,
                choice_e TEXT,
                correct_answer TEXT,
                explanation TEXT NOT NULL DEFAULT '',
                source_page INTEGER,
                FOREIGN KEY(test_id) REFERENCES historical_tests(id) ON DELETE CASCADE
            );
            """
        )
        _run_migrations(conn)


def _run_migrations(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS schema_version (
            id INTEGER PRIMARY KEY CHECK(id = 1),
            version INTEGER NOT NULL
        );
        """
    )
    row = conn.execute("SELECT version FROM schema_version WHERE id = 1").fetchone()
    if row is None:
        conn.execute("INSERT INTO schema_version (id, version) VALUES (1, 0)")
        version = 0
    else:
        version = int(row["version"])

    # v1: ensure constraint_expr exists
    if version < 1:
        _ensure_column(conn, "question_templates", "constraint_expr", "TEXT NOT NULL DEFAULT ''")
        conn.execute("UPDATE schema_version SET version = 1 WHERE id = 1")
        version = 1

    # v2: ensure external_id exists
    if version < 2:
        _ensure_column(conn, "question_templates", "external_id", "TEXT")
        _ensure_external_id_unique_index(conn)
        conn.execute("UPDATE schema_version SET version = 2 WHERE id = 1")
        version = 2

    # v3: assignments table
    if version < 3:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS assignments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                profile_id INTEGER NOT NULL,
                skill TEXT NOT NULL,
                subskill TEXT,
                target_type TEXT NOT NULL,
                target_value REAL NOT NULL DEFAULT 0,
                level INTEGER NOT NULL DEFAULT 1,
                num_questions INTEGER NOT NULL DEFAULT 5,
                question_type TEXT NOT NULL DEFAULT 'both',
                mode_intuition_pct INTEGER,
                mode_expression_pct INTEGER,
                mode_word_pct INTEGER,
                active INTEGER NOT NULL DEFAULT 1,
                notes TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL,
                completed_at TEXT,
                FOREIGN KEY(profile_id) REFERENCES profiles(id) ON DELETE CASCADE
            );
            """
        )
        conn.execute("UPDATE schema_version SET version = 3 WHERE id = 1")
        version = 3

    # v4: learning engine metadata columns
    if version < 4:
        _ensure_column(conn, "question_templates", "mode", "TEXT NOT NULL DEFAULT 'expression'")
        _ensure_column(conn, "quiz_questions", "question_label", "TEXT NOT NULL DEFAULT 'Core'")
        _ensure_column(conn, "quiz_questions", "mode", "TEXT NOT NULL DEFAULT 'expression'")
        conn.execute("UPDATE schema_version SET version = 4 WHERE id = 1")
        version = 4

    # v5: mode mix override columns for quiz sets and assignments
    if version < 5:
        _ensure_column(conn, "quiz_sets", "mode_intuition_pct", "INTEGER")
        _ensure_column(conn, "quiz_sets", "mode_expression_pct", "INTEGER")
        _ensure_column(conn, "quiz_sets", "mode_word_pct", "INTEGER")
        _ensure_column(conn, "assignments", "mode_intuition_pct", "INTEGER")
        _ensure_column(conn, "assignments", "mode_expression_pct", "INTEGER")
        _ensure_column(conn, "assignments", "mode_word_pct", "INTEGER")
        conn.execute("UPDATE schema_version SET version = 5 WHERE id = 1")
        version = 5

    # v6: quiz attempt timing for mastery speed signals
    if version < 6:
        _ensure_column(conn, "quiz_attempts", "elapsed_seconds", "REAL")
        conn.execute("UPDATE schema_version SET version = 6 WHERE id = 1")
        version = 6

    # v7: daily review completion history/streak tracking
    if version < 7:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS daily_goal_history (
                profile_id INTEGER NOT NULL,
                day_utc TEXT NOT NULL,
                completions INTEGER NOT NULL DEFAULT 0,
                last_completed_at TEXT NOT NULL,
                PRIMARY KEY (profile_id, day_utc),
                FOREIGN KEY(profile_id) REFERENCES profiles(id) ON DELETE CASCADE
            );
            """
        )
        conn.execute("UPDATE schema_version SET version = 7 WHERE id = 1")
        version = 7

    # v8: historical tests/question bank tables for SAT/PSAT/GRE practice mode
    if version < 8:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS historical_tests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                exam_code TEXT NOT NULL UNIQUE,
                title TEXT NOT NULL,
                exam_type TEXT NOT NULL,
                year INTEGER,
                pdf_path TEXT NOT NULL,
                source TEXT NOT NULL DEFAULT 'historical_pdf',
                created_at TEXT NOT NULL
            );
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS historical_questions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                test_id INTEGER NOT NULL,
                question_number INTEGER NOT NULL,
                section TEXT NOT NULL DEFAULT 'General',
                category TEXT NOT NULL DEFAULT 'unknown',
                prompt TEXT NOT NULL,
                choice_a TEXT,
                choice_b TEXT,
                choice_c TEXT,
                choice_d TEXT,
                choice_e TEXT,
                correct_answer TEXT,
                explanation TEXT NOT NULL DEFAULT '',
                source_page INTEGER,
                FOREIGN KEY(test_id) REFERENCES historical_tests(id) ON DELETE CASCADE
            );
            """
        )
        conn.execute("UPDATE schema_version SET version = 8 WHERE id = 1")
        version = 8

    # v9: migrate legacy calculus_slope skill ids to calculus_1
    if version < 9:
        _rewrite_skill_id(conn, "quiz_sets", "skill", "calculus_slope", "calculus_1")
        _rewrite_skill_id(conn, "quiz_attempts", "skill", "calculus_slope", "calculus_1")
        _rewrite_skill_id(conn, "quiz_questions", "skill", "calculus_slope", "calculus_1")
        _rewrite_skill_id(conn, "worksheets", "skill", "calculus_slope", "calculus_1")
        _rewrite_skill_id(conn, "question_templates", "skill", "calculus_slope", "calculus_1")
        _rewrite_skill_id(conn, "assignments", "skill", "calculus_slope", "calculus_1")
        _rewrite_skill_id(conn, "skill_subskill_progress", "skill", "calculus_slope", "calculus_1")
        conn.execute("UPDATE schema_version SET version = 9 WHERE id = 1")
        version = 9

    # Always ensure indexes exist (idempotent).
    _ensure_external_id_unique_index(conn)
    _ensure_historical_indexes(conn)


def _ensure_external_id_unique_index(conn: sqlite3.Connection) -> None:
    # Enforce uniqueness without requiring ALTER TABLE to add a UNIQUE column.
    # Multiple NULL values are allowed; empty strings should be avoided by the loader.
    conn.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS idx_question_templates_external_id
        ON question_templates(external_id)
        WHERE external_id IS NOT NULL;
        """
    )


def _ensure_historical_indexes(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_historical_questions_test_qnum
        ON historical_questions(test_id, question_number);
        """
    )
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_historical_questions_category
        ON historical_questions(category);
        """
    )


def _ensure_column(conn: sqlite3.Connection, table: str, column: str, ddl: str) -> None:
    rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
    existing = {r["name"] for r in rows}
    if column in existing:
        return
    conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {ddl}")


def _rewrite_skill_id(
    conn: sqlite3.Connection,
    table: str,
    column: str,
    old_skill: str,
    new_skill: str,
) -> None:
    conn.execute(
        f"UPDATE {table} SET {column} = ? WHERE {column} = ?",
        (new_skill, old_skill),
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
    with connect() as conn:
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
    with connect() as conn:
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
    with connect() as conn:
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
    with connect() as conn:
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
    with connect() as conn:
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
    with connect() as conn:
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
                SELECT profile_id, skill, subskill, current_streak, best_streak, mastered, updated_at
                FROM skill_subskill_progress
                WHERE profile_id = ?
                ORDER BY skill ASC, subskill ASC
                """,
                (profile_id,),
            ).fetchall()
        else:
            rows = conn.execute(
                """
                SELECT profile_id, skill, subskill, current_streak, best_streak, mastered, updated_at
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
            r["updated_at"],
        )
        for r in rows
    ]


def create_book(title: str, source: str, pdf_filename: str, created_at: str) -> Book:
    with connect() as conn:
        cur = conn.execute(
            "INSERT INTO books (title, source, pdf_filename, created_at) VALUES (?, ?, ?, ?)",
            (title, source, pdf_filename, created_at),
        )
        book_id = int(cur.lastrowid)
    return Book(book_id, title, source, pdf_filename)


def list_books() -> list[Book]:
    with connect() as conn:
        rows = conn.execute("SELECT id, title, source, pdf_filename FROM books ORDER BY id DESC").fetchall()
    return [Book(int(r["id"]), r["title"], r["source"], r["pdf_filename"]) for r in rows]


def upsert_historical_test(
    *,
    exam_code: str,
    title: str,
    exam_type: str,
    year: int | None,
    pdf_path: str,
    source: str,
    created_at: str,
) -> int:
    with connect() as conn:
        row = conn.execute(
            "SELECT id FROM historical_tests WHERE exam_code = ?",
            (exam_code,),
        ).fetchone()
        if row is None:
            cur = conn.execute(
                """
                INSERT INTO historical_tests (exam_code, title, exam_type, year, pdf_path, source, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (exam_code, title, exam_type, year, pdf_path, source, created_at),
            )
            return int(cur.lastrowid)
        test_id = int(row["id"])
        conn.execute(
            """
            UPDATE historical_tests
            SET title = ?, exam_type = ?, year = ?, pdf_path = ?, source = ?
            WHERE id = ?
            """,
            (title, exam_type, year, pdf_path, source, test_id),
        )
        return test_id


def replace_historical_questions(
    test_id: int,
    questions: list[dict[str, object]],
) -> int:
    with connect() as conn:
        conn.execute("DELETE FROM historical_questions WHERE test_id = ?", (int(test_id),))
        inserted = 0
        for q in questions:
            conn.execute(
                """
                INSERT INTO historical_questions
                (test_id, question_number, section, category, prompt, choice_a, choice_b, choice_c, choice_d, choice_e,
                 correct_answer, explanation, source_page)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    int(test_id),
                    int(q.get("question_number", inserted + 1)),
                    str(q.get("section", "General")),
                    str(q.get("category", "unknown")),
                    str(q.get("prompt", "")).strip(),
                    q.get("choice_a"),
                    q.get("choice_b"),
                    q.get("choice_c"),
                    q.get("choice_d"),
                    q.get("choice_e"),
                    q.get("correct_answer"),
                    str(q.get("explanation", "")),
                    q.get("source_page"),
                ),
            )
            inserted += 1
        return inserted


def list_historical_tests(
    exam_type: str | None = None,
) -> list[HistoricalTest]:
    with connect() as conn:
        if exam_type is None or exam_type == "all":
            rows = conn.execute(
                """
                SELECT id, exam_code, title, exam_type, year, pdf_path, source
                FROM historical_tests
                ORDER BY COALESCE(year, 0) DESC, title ASC
                """
            ).fetchall()
        else:
            rows = conn.execute(
                """
                SELECT id, exam_code, title, exam_type, year, pdf_path, source
                FROM historical_tests
                WHERE exam_type = ?
                ORDER BY COALESCE(year, 0) DESC, title ASC
                """,
                (exam_type,),
            ).fetchall()
    return [
        HistoricalTest(
            int(r["id"]),
            str(r["exam_code"]),
            str(r["title"]),
            str(r["exam_type"]),
            int(r["year"]) if r["year"] is not None else None,
            str(r["pdf_path"]),
            str(r["source"]),
        )
        for r in rows
    ]


def list_historical_questions(
    *,
    exam_type: str = "all",
    category: str = "all",
    limit: int = 50,
) -> list[HistoricalQuestion]:
    limit = max(1, int(limit))
    params: list[object] = []
    where: list[str] = []
    if exam_type != "all":
        where.append("ht.exam_type = ?")
        params.append(exam_type)
    if category != "all":
        where.append("hq.category = ?")
        params.append(category)
    where_sql = f"WHERE {' AND '.join(where)}" if where else ""
    with connect() as conn:
        rows = conn.execute(
            f"""
            SELECT hq.id, hq.test_id, hq.question_number, hq.section, hq.category, hq.prompt,
                   hq.choice_a, hq.choice_b, hq.choice_c, hq.choice_d, hq.choice_e,
                   hq.correct_answer, hq.explanation, hq.source_page
            FROM historical_questions hq
            JOIN historical_tests ht ON ht.id = hq.test_id
            {where_sql}
            ORDER BY RANDOM()
            LIMIT ?
            """,
            (*params, limit),
        ).fetchall()
    return [
        HistoricalQuestion(
            int(r["id"]),
            int(r["test_id"]),
            int(r["question_number"]),
            str(r["section"]),
            str(r["category"]),
            str(r["prompt"]),
            r["choice_a"],
            r["choice_b"],
            r["choice_c"],
            r["choice_d"],
            r["choice_e"],
            r["correct_answer"],
            str(r["explanation"] or ""),
            int(r["source_page"]) if r["source_page"] is not None else None,
        )
        for r in rows
    ]


def list_historical_questions_for_test(test_id: int) -> list[HistoricalQuestion]:
    with connect() as conn:
        rows = conn.execute(
            """
            SELECT id, test_id, question_number, section, category, prompt,
                   choice_a, choice_b, choice_c, choice_d, choice_e,
                   correct_answer, explanation, source_page
            FROM historical_questions
            WHERE test_id = ?
            ORDER BY question_number ASC, id ASC
            """,
            (int(test_id),),
        ).fetchall()
    return [
        HistoricalQuestion(
            int(r["id"]),
            int(r["test_id"]),
            int(r["question_number"]),
            str(r["section"]),
            str(r["category"]),
            str(r["prompt"]),
            r["choice_a"],
            r["choice_b"],
            r["choice_c"],
            r["choice_d"],
            r["choice_e"],
            r["correct_answer"],
            str(r["explanation"] or ""),
            int(r["source_page"]) if r["source_page"] is not None else None,
        )
        for r in rows
    ]


def apply_historical_answer_key(*, exam_code: str, answers: dict[int, str]) -> int:
    if not answers:
        return 0
    with connect() as conn:
        row = conn.execute(
            "SELECT id FROM historical_tests WHERE exam_code = ?",
            (str(exam_code),),
        ).fetchone()
        if row is None:
            return 0
        test_id = int(row["id"])
        updated = 0
        for qnum, answer in answers.items():
            ans = str(answer).strip().upper()
            if ans not in {"A", "B", "C", "D", "E"}:
                continue
            cur = conn.execute(
                """
                UPDATE historical_questions
                SET correct_answer = ?
                WHERE test_id = ? AND question_number = ?
                """,
                (ans, test_id, int(qnum)),
            )
            updated += int(cur.rowcount)
        return updated


def add_exercise_candidate(book_id: int, location: str, text: str, status: str, created_at: str) -> int:
    with connect() as conn:
        cur = conn.execute(
            """
            INSERT INTO exercise_candidates (book_id, location, text, status, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (book_id, location, text, status, created_at),
        )
        return int(cur.lastrowid)


def list_exercise_candidates(book_id: int, status: str = "new", limit: int = 200) -> list[ExerciseCandidate]:
    limit = max(1, int(limit))
    with connect() as conn:
        rows = conn.execute(
            """
            SELECT id, book_id, location, text, status
            FROM exercise_candidates
            WHERE book_id = ? AND status = ?
            ORDER BY id ASC
            LIMIT ?
            """,
            (book_id, status, limit),
        ).fetchall()
    return [
        ExerciseCandidate(int(r["id"]), int(r["book_id"]), r["location"], r["text"], r["status"]) for r in rows
    ]


def create_question_template(
    *,
    book_id: int | None,
    external_id: str | None,
    skill: str,
    subskill: str,
    label: str,
    mode: str,
    prompt_template: str,
    answer_expr: str,
    constraint_expr: str,
    explanation_template: str,
    min_level: int,
    max_level: int,
    choice_spread: float,
    active: bool,
    created_at: str,
) -> int:
    with connect() as conn:
        cur = conn.execute(
            """
            INSERT INTO question_templates
            (book_id, external_id, skill, subskill, label, mode, prompt_template, answer_expr, constraint_expr, explanation_template,
             min_level, max_level, choice_spread, active, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                book_id,
                external_id,
                skill,
                subskill,
                label,
                mode,
                prompt_template,
                answer_expr,
                constraint_expr,
                explanation_template,
                int(min_level),
                int(max_level),
                float(choice_spread),
                int(bool(active)),
                created_at,
            ),
        )
        return int(cur.lastrowid)


def add_template_var(
    template_id: int, name: str, kind: str, min_value: float, max_value: float, step: float
) -> None:
    if kind not in {"int", "float"}:
        raise ValueError("kind must be 'int' or 'float'")
    with connect() as conn:
        conn.execute(
            """
            INSERT INTO template_vars (template_id, name, kind, min_value, max_value, step)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (template_id, name, kind, float(min_value), float(max_value), float(step)),
        )


def list_question_templates(
    skill: str,
    level: int,
    subskill: str | None = None,
    mode: str | None = None,
) -> list[QuestionTemplate]:
    level = int(level)
    with connect() as conn:
        if subskill is None and mode is None:
            rows = conn.execute(
                """
                SELECT id, book_id, external_id, skill, subskill, label, prompt_template, answer_expr, constraint_expr, explanation_template,
                       min_level, max_level, choice_spread, mode, active
                FROM question_templates
                WHERE active = 1 AND skill = ? AND ? BETWEEN min_level AND max_level
                ORDER BY id DESC
                """,
                (skill, level),
            ).fetchall()
        elif subskill is None and mode is not None:
            rows = conn.execute(
                """
                SELECT id, book_id, external_id, skill, subskill, label, prompt_template, answer_expr, constraint_expr, explanation_template,
                       min_level, max_level, choice_spread, mode, active
                FROM question_templates
                WHERE active = 1 AND skill = ? AND ? BETWEEN min_level AND max_level AND mode = ?
                ORDER BY id DESC
                """,
                (skill, level, mode),
            ).fetchall()
        elif subskill is not None and mode is None:
            rows = conn.execute(
                """
                SELECT id, book_id, external_id, skill, subskill, label, prompt_template, answer_expr, constraint_expr, explanation_template,
                       min_level, max_level, choice_spread, mode, active
                FROM question_templates
                WHERE active = 1 AND skill = ? AND subskill = ? AND ? BETWEEN min_level AND max_level
                ORDER BY id DESC
                """,
                (skill, subskill, level),
            ).fetchall()
        else:
            rows = conn.execute(
                """
                SELECT id, book_id, external_id, skill, subskill, label, prompt_template, answer_expr, constraint_expr, explanation_template,
                       min_level, max_level, choice_spread, mode, active
                FROM question_templates
                WHERE active = 1 AND skill = ? AND subskill = ? AND ? BETWEEN min_level AND max_level AND mode = ?
                ORDER BY id DESC
                """,
                (skill, subskill, level, mode),
            ).fetchall()
    return [
        QuestionTemplate(
            int(r["id"]),
            int(r["book_id"]) if r["book_id"] is not None else None,
            r["external_id"],
            r["skill"],
            r["subskill"],
            r["label"],
            r["prompt_template"],
            r["answer_expr"],
            r["constraint_expr"],
            r["explanation_template"],
            int(r["min_level"]),
            int(r["max_level"]),
            float(r["choice_spread"]),
            r["mode"],
            bool(r["active"]),
        )
        for r in rows
    ]


def mode_accuracy_by_skill(profile_id: int, skill: str) -> dict[str, float]:
    with connect() as conn:
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


def delete_templates_by_identity(*, skill: str, subskill: str, label: str) -> int:
    with connect() as conn:
        cur = conn.execute(
            """
            DELETE FROM question_templates
            WHERE skill = ? AND subskill = ? AND label = ?
            """,
            (skill, subskill, label),
        )
        return int(cur.rowcount)


def delete_template_by_external_id(external_id: str) -> int:
    with connect() as conn:
        cur = conn.execute("DELETE FROM question_templates WHERE external_id = ?", (external_id,))
        return int(cur.rowcount)


def list_template_vars(template_id: int) -> list[TemplateVar]:
    with connect() as conn:
        rows = conn.execute(
            """
            SELECT template_id, name, kind, min_value, max_value, step
            FROM template_vars
            WHERE template_id = ?
            ORDER BY name ASC
            """,
            (int(template_id),),
        ).fetchall()
    return [
        TemplateVar(
            int(r["template_id"]),
            r["name"],
            r["kind"],
            float(r["min_value"]),
            float(r["max_value"]),
            float(r["step"]),
        )
        for r in rows
    ]


def list_all_question_templates(active_only: bool = True) -> list[QuestionTemplate]:
    with connect() as conn:
        if active_only:
            rows = conn.execute(
                """
                SELECT id, book_id, external_id, skill, subskill, label, prompt_template, answer_expr, constraint_expr, explanation_template,
                       min_level, max_level, choice_spread, mode, active
                FROM question_templates
                WHERE active = 1
                ORDER BY skill ASC, id ASC
                """
            ).fetchall()
        else:
            rows = conn.execute(
                """
                SELECT id, book_id, external_id, skill, subskill, label, prompt_template, answer_expr, constraint_expr, explanation_template,
                       min_level, max_level, choice_spread, mode, active
                FROM question_templates
                ORDER BY skill ASC, id ASC
                """
            ).fetchall()
    return [
        QuestionTemplate(
            int(r["id"]),
            int(r["book_id"]) if r["book_id"] is not None else None,
            r["external_id"],
            r["skill"],
            r["subskill"],
            r["label"],
            r["prompt_template"],
            r["answer_expr"],
            r["constraint_expr"],
            r["explanation_template"],
            int(r["min_level"]),
            int(r["max_level"]),
            float(r["choice_spread"]),
            r["mode"],
            bool(r["active"]),
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


def skill_progress_pipeline(profile_id: int) -> dict[str, dict[str, int]]:
    out: dict[str, dict[str, int]] = {}
    with connect() as conn:
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
    with connect() as conn:
        cur = conn.execute(
            """
            INSERT INTO assignments
            (profile_id, skill, subskill, target_type, target_value, level, num_questions, question_type,
             mode_intuition_pct, mode_expression_pct, mode_word_pct, notes, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
    clauses: list[str] = ["profile_id = ?"]
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
    with connect() as conn:
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


def assignment_completion_analytics(profile_id: int, recent_days: int = 30) -> dict[str, object]:
    recent_days = max(1, int(recent_days))
    active_items = list_assignments(profile_id, active_only=True)
    done_items = list_assignments(profile_id, active_only=False)
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
    with connect() as conn:
        conn.execute(
            "UPDATE assignments SET active = ?, completed_at = ? WHERE id = ?",
            (1 if active else 0, completed_at if not active else None, int(assignment_id)),
        )


def get_next_active_assignment(profile_id: int) -> Assignment | None:
    items = list_assignments(profile_id, active_only=True)
    return items[0] if items else None


def evaluate_assignments_for_attempt(profile_id: int, attempt_id: int, completed_at: str) -> int:
    completed = 0
    with connect() as conn:
        attempt = conn.execute(
            """
            SELECT id, profile_id, skill, score, num_questions
            FROM quiz_attempts
            WHERE id = ? AND profile_id = ?
            """,
            (int(attempt_id), int(profile_id)),
        ).fetchone()
        if attempt is None:
            return 0

        assignments = conn.execute(
            """
            SELECT id, skill, subskill, target_type, target_value
            FROM assignments
            WHERE profile_id = ? AND active = 1
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
                    "UPDATE assignments SET active = 0, completed_at = ? WHERE id = ?",
                    (completed_at, int(item["id"])),
                )
                completed += 1
    return completed


def record_daily_review_completion(profile_id: int, completed_at: str) -> None:
    day_utc = _iso_day_utc(completed_at)
    with connect() as conn:
        row = conn.execute(
            """
            SELECT completions
            FROM daily_goal_history
            WHERE profile_id = ? AND day_utc = ?
            """,
            (int(profile_id), day_utc),
        ).fetchone()
        if row is None:
            conn.execute(
                """
                INSERT INTO daily_goal_history (profile_id, day_utc, completions, last_completed_at)
                VALUES (?, ?, ?, ?)
                """,
                (int(profile_id), day_utc, 1, completed_at),
            )
            return
        conn.execute(
            """
            UPDATE daily_goal_history
            SET completions = ?, last_completed_at = ?
            WHERE profile_id = ? AND day_utc = ?
            """,
            (int(row["completions"]) + 1, completed_at, int(profile_id), day_utc),
        )


def list_daily_goal_history(profile_id: int, limit: int = 60) -> list[DailyGoalHistory]:
    with connect() as conn:
        rows = conn.execute(
            """
            SELECT profile_id, day_utc, completions, last_completed_at
            FROM daily_goal_history
            WHERE profile_id = ?
            ORDER BY day_utc DESC
            LIMIT ?
            """,
            (int(profile_id), max(1, int(limit))),
        ).fetchall()
    return [
        DailyGoalHistory(
            profile_id=int(r["profile_id"]),
            day_utc=r["day_utc"],
            completions=int(r["completions"]),
            last_completed_at=r["last_completed_at"],
        )
        for r in rows
    ]


def daily_goal_status(profile_id: int, now_iso_text: str | None = None) -> tuple[int, int]:
    now = _parse_iso_utc(now_iso_text) if now_iso_text else datetime.now(timezone.utc)
    if now is None:
        now = datetime.now(timezone.utc)
    today = now.date()
    entries = list_daily_goal_history(profile_id, limit=365)
    by_day = {item.day_utc: item for item in entries}
    today_count = by_day.get(today.isoformat()).completions if today.isoformat() in by_day else 0

    streak = 0
    cursor = today
    while True:
        item = by_day.get(cursor.isoformat())
        if item is None or int(item.completions) <= 0:
            break
        streak += 1
        cursor = cursor.fromordinal(cursor.toordinal() - 1)
    return today_count, streak


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
