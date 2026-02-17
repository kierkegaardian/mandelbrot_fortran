from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from typing import Optional

from .models import (
    Assignment,
    Book,
    ExerciseCandidate,
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
                active INTEGER NOT NULL DEFAULT 1,
                notes TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL,
                completed_at TEXT,
                FOREIGN KEY(profile_id) REFERENCES profiles(id) ON DELETE CASCADE
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

    # Always ensure indexes exist (idempotent).
    _ensure_external_id_unique_index(conn)


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


def _ensure_column(conn: sqlite3.Connection, table: str, column: str, ddl: str) -> None:
    rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
    existing = {r["name"] for r in rows}
    if column in existing:
        return
    conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {ddl}")


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
            (book_id, external_id, skill, subskill, label, prompt_template, answer_expr, constraint_expr, explanation_template,
             min_level, max_level, choice_spread, active, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                book_id,
                external_id,
                skill,
                subskill,
                label,
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


def list_question_templates(skill: str, level: int, subskill: str | None = None) -> list[QuestionTemplate]:
    level = int(level)
    with connect() as conn:
        if subskill is None:
            rows = conn.execute(
                """
                SELECT id, book_id, external_id, skill, subskill, label, prompt_template, answer_expr, constraint_expr, explanation_template,
                       min_level, max_level, choice_spread, active
                FROM question_templates
                WHERE active = 1 AND skill = ? AND ? BETWEEN min_level AND max_level
                ORDER BY id DESC
                """,
                (skill, level),
            ).fetchall()
        else:
            rows = conn.execute(
                """
                SELECT id, book_id, external_id, skill, subskill, label, prompt_template, answer_expr, constraint_expr, explanation_template,
                       min_level, max_level, choice_spread, active
                FROM question_templates
                WHERE active = 1 AND skill = ? AND subskill = ? AND ? BETWEEN min_level AND max_level
                ORDER BY id DESC
                """,
                (skill, subskill, level),
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
            bool(r["active"]),
        )
        for r in rows
    ]


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
                       min_level, max_level, choice_spread, active
                FROM question_templates
                WHERE active = 1
                ORDER BY skill ASC, id ASC
                """
            ).fetchall()
        else:
            rows = conn.execute(
                """
                SELECT id, book_id, external_id, skill, subskill, label, prompt_template, answer_expr, constraint_expr, explanation_template,
                       min_level, max_level, choice_spread, active
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


def create_assignment(
    profile_id: int,
    skill: str,
    subskill: str | None,
    target_type: str,
    target_value: float,
    level: int,
    num_questions: int,
    question_type: str,
    notes: str,
    created_at: str,
) -> int:
    with connect() as conn:
        cur = conn.execute(
            """
            INSERT INTO assignments
            (profile_id, skill, subskill, target_type, target_value, level, num_questions, question_type, notes, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                notes,
                created_at,
            ),
        )
        return int(cur.lastrowid)


def list_assignments(profile_id: int, active_only: bool | None = True) -> list[Assignment]:
    with connect() as conn:
        if active_only is None:
            rows = conn.execute(
                """
                SELECT id, profile_id, skill, subskill, target_type, target_value, level, num_questions, question_type,
                       active, notes, created_at, completed_at
                FROM assignments
                WHERE profile_id = ?
                ORDER BY active DESC, created_at DESC, id DESC
                """,
                (int(profile_id),),
            ).fetchall()
        elif active_only:
            rows = conn.execute(
                """
                SELECT id, profile_id, skill, subskill, target_type, target_value, level, num_questions, question_type,
                       active, notes, created_at, completed_at
                FROM assignments
                WHERE profile_id = ? AND active = 1
                ORDER BY created_at ASC, id ASC
                """,
                (int(profile_id),),
            ).fetchall()
        else:
            rows = conn.execute(
                """
                SELECT id, profile_id, skill, subskill, target_type, target_value, level, num_questions, question_type,
                       active, notes, created_at, completed_at
                FROM assignments
                WHERE profile_id = ? AND active = 0
                ORDER BY completed_at DESC, id DESC
                """,
                (int(profile_id),),
            ).fetchall()
    return [_row_to_assignment(r) for r in rows]


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
                is_done = pct >= target_value
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
        active=bool(r["active"]),
        notes=r["notes"],
        created_at=r["created_at"],
        completed_at=r["completed_at"],
    )
