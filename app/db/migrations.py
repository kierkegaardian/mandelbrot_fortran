from __future__ import annotations

import sqlite3


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
