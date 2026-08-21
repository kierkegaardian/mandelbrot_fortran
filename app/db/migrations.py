from __future__ import annotations

import sqlite3

from .migration_helpers import (
    _enqueue_existing_sync_rows,
    _ensure_column,
    _ensure_external_id_unique_index,
    _ensure_schema_support,
    _ensure_sync_schema,
    _rewrite_skill_id,
    _schema_version,
)

def _run_migrations(conn: sqlite3.Connection) -> None:
    version = _schema_version(conn)

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

    # v10: parent auth pin + in-progress quiz resume persistence
    if version < 10:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS parent_auth (
                profile_id INTEGER PRIMARY KEY,
                pin_hash TEXT NOT NULL,
                pin_salt TEXT NOT NULL,
                failed_attempts INTEGER NOT NULL DEFAULT 0,
                locked_until TEXT,
                updated_at TEXT NOT NULL,
                FOREIGN KEY(profile_id) REFERENCES profiles(id) ON DELETE CASCADE
            );
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS quiz_attempt_progress (
                attempt_id INTEGER PRIMARY KEY AUTOINCREMENT,
                profile_id INTEGER NOT NULL,
                question_index INTEGER NOT NULL DEFAULT 0,
                state_json TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY(profile_id) REFERENCES profiles(id) ON DELETE CASCADE
            );
            """
        )
        conn.execute("UPDATE schema_version SET version = 10 WHERE id = 1")
        version = 10

    # v11: persist credited subskill for quiz history rows
    if version < 11:
        _ensure_column(conn, "quiz_questions", "subskill", "TEXT")
        conn.execute("UPDATE schema_version SET version = 11 WHERE id = 1")
        version = 11

    # v12: sync metadata + local outbox for optional family sync
    if version < 12:
        _ensure_sync_schema(conn)
        conn.execute("UPDATE schema_version SET version = 12 WHERE id = 1")
        version = 12

    # v13: local-only Summer Program planning tables
    if version < 13:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS summer_programs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                profile_id INTEGER NOT NULL,
                lane TEXT NOT NULL,
                start_date TEXT NOT NULL,
                end_date TEXT NOT NULL,
                days_per_week INTEGER NOT NULL,
                minutes_per_session INTEGER NOT NULL,
                status TEXT NOT NULL,
                finish_definition TEXT NOT NULL,
                placement_recommendation TEXT,
                placement_review_status TEXT NOT NULL DEFAULT 'accepted',
                placement_reviewed_at TEXT,
                student_age_years INTEGER,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY(profile_id) REFERENCES profiles(id) ON DELETE CASCADE
            );
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS summer_program_tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                program_id INTEGER NOT NULL,
                unit_code TEXT NOT NULL,
                task_kind TEXT NOT NULL,
                skill TEXT NOT NULL,
                subskill TEXT,
                sequence_index INTEGER NOT NULL,
                status TEXT NOT NULL,
                target_score_pct REAL,
                scheduled_date TEXT NOT NULL,
                notes_json TEXT NOT NULL DEFAULT '{}',
                FOREIGN KEY(program_id) REFERENCES summer_programs(id) ON DELETE CASCADE
            );
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS summer_assessment_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                program_id INTEGER NOT NULL,
                assessment_type TEXT NOT NULL,
                score_pct REAL NOT NULL,
                passed INTEGER NOT NULL,
                strand_results_json TEXT NOT NULL,
                completed_at TEXT NOT NULL,
                FOREIGN KEY(program_id) REFERENCES summer_programs(id) ON DELETE CASCADE
            );
            """
        )
        conn.execute("UPDATE schema_version SET version = 13 WHERE id = 1")
        version = 13

    # v14: Summer Program placement review state
    if version < 14:
        _ensure_column(conn, "summer_programs", "placement_review_status", "TEXT NOT NULL DEFAULT 'accepted'")
        _ensure_column(conn, "summer_programs", "placement_reviewed_at", "TEXT")
        conn.execute("UPDATE schema_version SET version = 14 WHERE id = 1")
        version = 14

    # v15: per-child Texas school-year grade targets
    if version < 15:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS school_year_targets (
                profile_id INTEGER PRIMARY KEY,
                grade INTEGER NOT NULL,
                stretch_enabled INTEGER NOT NULL DEFAULT 1,
                updated_at TEXT NOT NULL,
                FOREIGN KEY(profile_id) REFERENCES profiles(id) ON DELETE CASCADE
            );
            """
        )
        conn.execute("UPDATE schema_version SET version = 15 WHERE id = 1")
        version = 15

    # v16: archived worksheet rows for parent packet management
    if version < 16:
        _ensure_column(conn, "worksheets", "archived_at", "TEXT")
        conn.execute("UPDATE schema_version SET version = 16 WHERE id = 1")
        version = 16

    # v17: queue canonical rows created before the sync-aware service existed
    if version < 17:
        _ensure_sync_schema(conn)
        _enqueue_existing_sync_rows(conn)
        conn.execute("UPDATE schema_version SET version = 17 WHERE id = 1")
        version = 17
    _ensure_schema_support(conn)
