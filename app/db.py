from __future__ import annotations

from collections.abc import Callable, Iterator
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
import hashlib
import hmac
import os
import sqlite3
import uuid
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
    SchoolYearTarget,
    SummerAssessmentRun,
    SummerProgram,
    SummerProgramTask,
    SubskillProgress,
    TemplateVar,
    Worksheet,
)
from .paths import data_dir

__all__ = (
    "DbConfig",
    "PIN_HASH_ITERATIONS",
    "PIN_LOCK_MAX_ATTEMPTS",
    "PIN_LOCK_MINUTES",
    "PIN_MAX_LENGTH",
    "PIN_MIN_LENGTH",
    "add_exercise_candidate",
    "add_question_result",
    "add_template_var",
    "apply_historical_answer_key",
    "archive_summer_programs",
    "archive_worksheet",
    "assignment_completion_analytics",
    "clear_parent_lock",
    "clear_quiz_progress",
    "clear_quiz_progress_for_profile",
    "connect",
    "create_assignment",
    "create_attempt",
    "create_book",
    "create_profile",
    "create_question_template",
    "create_quiz_set",
    "create_summer_program",
    "create_summer_program_task",
    "create_worksheet",
    "daily_goal_status",
    "db_config",
    "delete_profile",
    "delete_quiz_set",
    "delete_template_by_external_id",
    "delete_templates_by_identity",
    "evaluate_assignments_for_attempt",
    "evaluate_assignments_for_attempt_ids",
    "get_active_summer_program",
    "get_db_config",
    "get_next_active_assignment",
    "get_school_year_target",
    "get_summer_assessment_run",
    "get_summer_program",
    "get_summer_program_task",
    "has_active_question_templates",
    "init_db",
    "list_all_question_templates",
    "list_assignments",
    "list_attempts",
    "list_books",
    "list_daily_goal_history",
    "list_exercise_candidates",
    "list_historical_questions",
    "list_historical_questions_for_test",
    "list_historical_tests",
    "list_profiles",
    "list_question_templates",
    "list_quiz_sets",
    "list_subskill_progress",
    "list_summer_assessment_runs",
    "list_summer_program_tasks",
    "list_summer_programs",
    "list_template_vars",
    "list_worksheets",
    "load_quiz_progress",
    "managed_connection",
    "mode_accuracy_by_skill",
    "override_db_config",
    "parent_pin_configured",
    "parent_pin_locked",
    "rebuild_subskill_progress",
    "record_daily_review_completion",
    "record_parent_auth_failure",
    "record_summer_assessment",
    "replace_historical_questions",
    "replace_summer_program_tasks",
    "reset_db_config",
    "save_quiz_progress",
    "save_school_year_target",
    "set_assignment_active",
    "set_db_config",
    "set_parent_pin",
    "shift_summer_program_task_sequences",
    "skill_progress_pipeline",
    "template_modes_for_skill",
    "update_quiz_set",
    "update_summer_program",
    "update_summer_program_task",
    "upsert_historical_test",
    "upsert_subskill_progress",
    "verify_parent_pin",
)

PIN_MIN_LENGTH = 4
PIN_MAX_LENGTH = 12
PIN_HASH_ITERATIONS = 200_000
PIN_LOCK_MAX_ATTEMPTS = 5
PIN_LOCK_MINUTES = 15


@dataclass(frozen=True)
class DbConfig:
    path: str


_DbConfigProvider = Callable[[], DbConfig]
_DbConfigSource = DbConfig | _DbConfigProvider


def _default_db_config() -> DbConfig:
    db_path = data_dir() / "app.db"
    return DbConfig(path=str(db_path))


_db_config_provider: _DbConfigProvider = _default_db_config


def get_db_config() -> DbConfig:
    config = _db_config_provider()
    if not isinstance(config, DbConfig):
        raise TypeError("DB config provider must return DbConfig")
    return config


def db_config() -> DbConfig:
    """Return the active config while preserving the existing public callable."""
    return get_db_config()


def set_db_config(config: _DbConfigSource) -> None:
    """Set the process-wide DB config source used by every connection."""
    global _db_config_provider
    if isinstance(config, DbConfig):
        _db_config_provider = lambda: config
        return
    if not callable(config):
        raise TypeError("DB config must be a DbConfig or callable provider")
    _db_config_provider = config


def reset_db_config() -> None:
    """Restore data-dir-based DB configuration."""
    global _db_config_provider
    _db_config_provider = _default_db_config


@contextmanager
def override_db_config(config: _DbConfigSource) -> Iterator[None]:
    """Temporarily replace the shared DB config source, including nested use."""
    global _db_config_provider
    previous_provider = _db_config_provider
    set_db_config(config)
    try:
        yield
    finally:
        _db_config_provider = previous_provider


def connect() -> sqlite3.Connection:
    cfg = get_db_config()
    conn = sqlite3.connect(cfg.path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


@contextmanager
def managed_connection() -> Iterator[sqlite3.Connection]:
    conn = connect()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db() -> None:
    with managed_connection() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS profiles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                role TEXT NOT NULL,
                created_at TEXT NOT NULL,
                sync_id TEXT NOT NULL,
                sync_updated_at TEXT NOT NULL,
                sync_deleted INTEGER NOT NULL DEFAULT 0
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
                created_at TEXT NOT NULL,
                sync_id TEXT NOT NULL,
                sync_updated_at TEXT NOT NULL,
                sync_deleted INTEGER NOT NULL DEFAULT 0
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
                sync_id TEXT NOT NULL,
                sync_updated_at TEXT NOT NULL,
                sync_deleted INTEGER NOT NULL DEFAULT 0,
                FOREIGN KEY(profile_id) REFERENCES profiles(id) ON DELETE CASCADE,
                FOREIGN KEY(quiz_set_id) REFERENCES quiz_sets(id) ON DELETE SET NULL
            );

            CREATE TABLE IF NOT EXISTS quiz_questions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                attempt_id INTEGER NOT NULL,
                skill TEXT NOT NULL,
                subskill TEXT,
                question_label TEXT NOT NULL DEFAULT 'Core',
                mode TEXT NOT NULL DEFAULT 'expression',
                prompt TEXT NOT NULL,
                correct_answer TEXT NOT NULL,
                user_answer TEXT NOT NULL,
                is_correct INTEGER NOT NULL,
                explanation TEXT NOT NULL,
                sync_id TEXT NOT NULL,
                sync_updated_at TEXT NOT NULL,
                sync_deleted INTEGER NOT NULL DEFAULT 0,
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
                archived_at TEXT,
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
                sync_id TEXT NOT NULL,
                sync_updated_at TEXT NOT NULL,
                sync_deleted INTEGER NOT NULL DEFAULT 0,
                FOREIGN KEY(profile_id) REFERENCES profiles(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS parent_auth (
                profile_id INTEGER PRIMARY KEY,
                pin_hash TEXT NOT NULL,
                pin_salt TEXT NOT NULL,
                failed_attempts INTEGER NOT NULL DEFAULT 0,
                locked_until TEXT,
                updated_at TEXT NOT NULL,
                FOREIGN KEY(profile_id) REFERENCES profiles(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS quiz_attempt_progress (
                attempt_id INTEGER PRIMARY KEY AUTOINCREMENT,
                profile_id INTEGER NOT NULL,
                question_index INTEGER NOT NULL DEFAULT 0,
                state_json TEXT NOT NULL,
                updated_at TEXT NOT NULL,
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

            CREATE TABLE IF NOT EXISTS school_year_targets (
                profile_id INTEGER PRIMARY KEY,
                grade INTEGER NOT NULL,
                stretch_enabled INTEGER NOT NULL DEFAULT 1,
                updated_at TEXT NOT NULL,
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

    # Always ensure indexes exist (idempotent).
    _ensure_sync_schema(conn)
    _ensure_external_id_unique_index(conn)
    _ensure_historical_indexes(conn)
    _ensure_parent_auth_indexes(conn)
    _ensure_quiz_progress_indexes(conn)
    _ensure_sync_indexes(conn)
    _ensure_summer_program_indexes(conn)
    _ensure_school_year_indexes(conn)
    from .summer_program_template_seed import ensure_summer_program_templates

    ensure_summer_program_templates(conn)


def _ensure_sync_schema(conn: sqlite3.Connection) -> None:
    _ensure_sync_columns(conn, "profiles", "created_at")
    _ensure_sync_columns(conn, "quiz_sets", "created_at")
    _ensure_sync_columns(conn, "quiz_attempts", "created_at")
    _ensure_sync_columns(conn, "quiz_questions", None)
    _ensure_sync_columns(conn, "assignments", "created_at")
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS sync_outbox (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            entity_type TEXT NOT NULL,
            entity_sync_id TEXT NOT NULL,
            action TEXT NOT NULL,
            payload_json TEXT NOT NULL DEFAULT '{}',
            created_at TEXT NOT NULL,
            last_attempt_at TEXT,
            attempt_count INTEGER NOT NULL DEFAULT 0,
            last_error TEXT,
            synced_at TEXT
        );
        """
    )


def _ensure_sync_columns(conn: sqlite3.Connection, table: str, source_timestamp_column: str | None) -> None:
    _ensure_column(conn, table, "sync_id", "TEXT NOT NULL DEFAULT ''")
    _ensure_column(conn, table, "sync_updated_at", "TEXT NOT NULL DEFAULT ''")
    _ensure_column(conn, table, "sync_deleted", "INTEGER NOT NULL DEFAULT 0")

    select_columns = "id, sync_id, sync_updated_at"
    if source_timestamp_column is not None:
        select_columns += f", {source_timestamp_column} AS source_ts"
    else:
        select_columns += ", NULL AS source_ts"
    rows = conn.execute(f"SELECT {select_columns} FROM {table}").fetchall()
    fallback_updated_at = _sync_now_text()
    for row in rows:
        assignments: list[str] = []
        params: list[object] = []
        if not row["sync_id"]:
            assignments.append("sync_id = ?")
            params.append(str(uuid.uuid4()))
        if not row["sync_updated_at"]:
            source_ts = row["source_ts"]
            assignments.append("sync_updated_at = ?")
            params.append(str(source_ts) if source_ts else fallback_updated_at)
        if assignments:
            params.append(int(row["id"]))
            conn.execute(
                f"UPDATE {table} SET {', '.join(assignments)} WHERE id = ?",
                tuple(params),
            )


def _enqueue_existing_sync_rows(conn: sqlite3.Connection) -> None:
    sync_entities: tuple[tuple[str, str], ...] = (
        ("profiles", "profiles"),
        ("quiz_sets", "quiz_sets"),
        ("assignments", "assignments"),
        ("quiz_attempts", "quiz_attempts"),
        ("quiz_questions", "quiz_questions"),
    )
    for entity_type, table in sync_entities:
        rows = conn.execute(
            f"""
            SELECT entity.id, entity.sync_id, entity.sync_updated_at
            FROM {table} AS entity
            WHERE entity.sync_deleted = 0
              AND entity.sync_id <> ''
              AND NOT EXISTS (
                  SELECT 1
                  FROM sync_outbox AS pending
                  WHERE pending.entity_type = ?
                    AND pending.entity_sync_id = entity.sync_id
              )
            ORDER BY entity.id ASC
            """,
            (entity_type,),
        ).fetchall()
        for row in rows:
            local_id = int(row["id"])
            conn.execute(
                """
                INSERT INTO sync_outbox
                (entity_type, entity_sync_id, action, payload_json, created_at,
                 last_attempt_at, attempt_count, last_error, synced_at)
                VALUES (?, ?, 'upsert', ?, ?, NULL, 0, NULL, NULL)
                """,
                (
                    entity_type,
                    str(row["sync_id"]),
                    f'{{"local_id": {local_id}}}',
                    str(row["sync_updated_at"]),
                ),
            )


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


def _ensure_parent_auth_indexes(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_parent_auth_locked_until
        ON parent_auth(locked_until);
        """
    )


def _ensure_quiz_progress_indexes(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_quiz_attempt_progress_profile_updated
        ON quiz_attempt_progress(profile_id, updated_at DESC);
        """
    )


def _ensure_sync_indexes(conn: sqlite3.Connection) -> None:
    for table in ("profiles", "quiz_sets", "quiz_attempts", "quiz_questions", "assignments"):
        conn.execute(
            f"""
            CREATE UNIQUE INDEX IF NOT EXISTS idx_{table}_sync_id
            ON {table}(sync_id);
            """
        )
        conn.execute(
            f"""
            CREATE INDEX IF NOT EXISTS idx_{table}_sync_updated_at
            ON {table}(sync_updated_at DESC);
            """
        )
        conn.execute(
            f"""
            CREATE INDEX IF NOT EXISTS idx_{table}_sync_deleted
            ON {table}(sync_deleted);
            """
        )
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_sync_outbox_pending
        ON sync_outbox(synced_at, id);
        """
    )
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_sync_outbox_entity
        ON sync_outbox(entity_type, entity_sync_id, id);
        """
    )


def _ensure_summer_program_indexes(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_summer_programs_profile_status
        ON summer_programs(profile_id, status, updated_at DESC);
        """
    )
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_summer_program_tasks_program_sequence
        ON summer_program_tasks(program_id, sequence_index ASC);
        """
    )
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_summer_assessment_runs_program_type
        ON summer_assessment_runs(program_id, assessment_type, completed_at DESC);
        """
    )


def _ensure_school_year_indexes(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_school_year_targets_grade
        ON school_year_targets(grade, updated_at DESC);
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
    with managed_connection() as conn:
        rows = conn.execute(
            "SELECT id, name, role FROM profiles WHERE sync_deleted = 0 ORDER BY role DESC, name ASC"
        ).fetchall()
    return [Profile(int(r["id"]), r["name"], r["role"]) for r in rows]


def create_profile(name: str, role: str, created_at: str) -> Profile:
    if role not in {"child", "parent"}:
        raise ValueError("role must be 'child' or 'parent'")
    sync_id = str(uuid.uuid4())
    with managed_connection() as conn:
        cur = conn.execute(
            """
            INSERT INTO profiles (name, role, created_at, sync_id, sync_updated_at, sync_deleted)
            VALUES (?, ?, ?, ?, ?, 0)
            """,
            (name, role, created_at, sync_id, created_at),
        )
        profile_id = int(cur.lastrowid)
    return Profile(profile_id, name, role)


def delete_profile(profile_id: int) -> None:
    with managed_connection() as conn:
        conn.execute("DELETE FROM profiles WHERE id = ?", (profile_id,))


def get_school_year_target(profile_id: int) -> SchoolYearTarget | None:
    with managed_connection() as conn:
        row = conn.execute(
            """
            SELECT profile_id, grade, stretch_enabled, updated_at
            FROM school_year_targets
            WHERE profile_id = ?
            """,
            (int(profile_id),),
        ).fetchone()
    if row is None:
        return None
    return SchoolYearTarget(
        profile_id=int(row["profile_id"]),
        grade=int(row["grade"]),
        stretch_enabled=bool(row["stretch_enabled"]),
        updated_at=str(row["updated_at"]),
    )


def save_school_year_target(profile_id: int, grade: int, stretch_enabled: bool, updated_at: str) -> SchoolYearTarget:
    grade = int(grade)
    if grade < 1 or grade > 7:
        raise ValueError("Texas school-year grade must be between 1 and 7.")
    with managed_connection() as conn:
        row = conn.execute(
            "SELECT role FROM profiles WHERE id = ?",
            (int(profile_id),),
        ).fetchone()
        if row is None:
            raise ValueError("Profile not found.")
        if str(row["role"]) != "child":
            raise ValueError("School-year targets can only be set for child profiles.")
        conn.execute(
            """
            INSERT INTO school_year_targets (profile_id, grade, stretch_enabled, updated_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(profile_id) DO UPDATE SET
                grade = excluded.grade,
                stretch_enabled = excluded.stretch_enabled,
                updated_at = excluded.updated_at
            """,
            (int(profile_id), grade, int(bool(stretch_enabled)), updated_at),
        )
    return SchoolYearTarget(
        profile_id=int(profile_id),
        grade=grade,
        stretch_enabled=bool(stretch_enabled),
        updated_at=updated_at,
    )


def parent_pin_configured() -> bool:
    with managed_connection() as conn:
        row = conn.execute("SELECT profile_id FROM parent_auth LIMIT 1").fetchone()
    return row is not None


def parent_pin_locked(now_iso_text: str | None = None) -> tuple[bool, str | None]:
    now = _parse_iso_utc(now_iso_text) if now_iso_text else datetime.now(timezone.utc)
    if now is None:
        now = datetime.now(timezone.utc)
    with managed_connection() as conn:
        row = conn.execute(
            "SELECT locked_until FROM parent_auth LIMIT 1",
        ).fetchone()
    if row is None or row["locked_until"] is None:
        return False, None
    locked_until = _parse_iso_utc(str(row["locked_until"]))
    if locked_until is None or locked_until <= now:
        return False, None
    return True, locked_until.isoformat()


def set_parent_pin(profile_id: int, pin: str, updated_at: str) -> None:
    cleaned = pin.strip()
    if not cleaned.isdigit() or not (PIN_MIN_LENGTH <= len(cleaned) <= PIN_MAX_LENGTH):
        raise ValueError(f"PIN must be {PIN_MIN_LENGTH}-{PIN_MAX_LENGTH} digits.")
    with managed_connection() as conn:
        row = conn.execute(
            "SELECT role FROM profiles WHERE id = ?",
            (int(profile_id),),
        ).fetchone()
        if row is None:
            raise ValueError("Profile not found.")
        if str(row["role"]) != "parent":
            raise ValueError("Only a parent profile can own the parent PIN.")

        conn.execute("DELETE FROM parent_auth")
        pin_salt = os.urandom(16).hex()
        pin_hash = _hash_pin(cleaned, pin_salt)
        conn.execute(
            """
            INSERT INTO parent_auth (profile_id, pin_hash, pin_salt, failed_attempts, locked_until, updated_at)
            VALUES (?, ?, ?, 0, NULL, ?)
            """,
            (int(profile_id), pin_hash, pin_salt, updated_at),
        )


def verify_parent_pin(pin: str, now_iso_text: str | None = None) -> bool:
    now = _parse_iso_utc(now_iso_text) if now_iso_text else datetime.now(timezone.utc)
    if now is None:
        now = datetime.now(timezone.utc)
    with managed_connection() as conn:
        row = conn.execute(
            "SELECT profile_id, pin_hash, pin_salt, locked_until FROM parent_auth LIMIT 1",
        ).fetchone()
    if row is None:
        return False
    if row["locked_until"]:
        locked_until = _parse_iso_utc(str(row["locked_until"]))
        if locked_until is not None and locked_until > now:
            return False
    computed = _hash_pin(pin.strip(), str(row["pin_salt"]))
    return hmac.compare_digest(computed, str(row["pin_hash"]))


def record_parent_auth_failure(now_iso_text: str) -> str | None:
    now = _parse_iso_utc(now_iso_text)
    if now is None:
        now = datetime.now(timezone.utc)
    with managed_connection() as conn:
        row = conn.execute(
            "SELECT profile_id, failed_attempts FROM parent_auth LIMIT 1",
        ).fetchone()
        if row is None:
            return None
        failures = int(row["failed_attempts"]) + 1
        locked_until = None
        if failures >= PIN_LOCK_MAX_ATTEMPTS:
            failures = 0
            locked_until = (now + timedelta(minutes=PIN_LOCK_MINUTES)).isoformat()
        conn.execute(
            """
            UPDATE parent_auth
            SET failed_attempts = ?, locked_until = ?, updated_at = ?
            WHERE profile_id = ?
            """,
            (failures, locked_until, now.isoformat(), int(row["profile_id"])),
        )
    return locked_until


def clear_parent_lock(now_iso_text: str | None = None) -> None:
    updated_at = now_iso_text or datetime.now(timezone.utc).isoformat()
    with managed_connection() as conn:
        conn.execute(
            """
            UPDATE parent_auth
            SET failed_attempts = 0, locked_until = NULL, updated_at = ?
            """,
            (updated_at,),
        )


def save_quiz_progress(
    profile_id: int,
    attempt_id: int | None,
    question_index: int,
    state_json: str,
    updated_at: str,
) -> int:
    with managed_connection() as conn:
        if attempt_id is None:
            cur = conn.execute(
                """
                INSERT INTO quiz_attempt_progress (profile_id, question_index, state_json, updated_at)
                VALUES (?, ?, ?, ?)
                """,
                (int(profile_id), max(0, int(question_index)), state_json, updated_at),
            )
            return int(cur.lastrowid)
        conn.execute(
            """
            UPDATE quiz_attempt_progress
            SET question_index = ?, state_json = ?, updated_at = ?
            WHERE attempt_id = ? AND profile_id = ?
            """,
            (max(0, int(question_index)), state_json, updated_at, int(attempt_id), int(profile_id)),
        )
        return int(attempt_id)


def load_quiz_progress(profile_id: int) -> tuple[int, int, str] | None:
    with managed_connection() as conn:
        row = conn.execute(
            """
            SELECT attempt_id, question_index, state_json
            FROM quiz_attempt_progress
            WHERE profile_id = ?
            ORDER BY updated_at DESC, attempt_id DESC
            LIMIT 1
            """,
            (int(profile_id),),
        ).fetchone()
    if row is None:
        return None
    return (int(row["attempt_id"]), int(row["question_index"]), str(row["state_json"]))


def clear_quiz_progress(attempt_id: int) -> None:
    with managed_connection() as conn:
        conn.execute("DELETE FROM quiz_attempt_progress WHERE attempt_id = ?", (int(attempt_id),))


def clear_quiz_progress_for_profile(profile_id: int) -> None:
    with managed_connection() as conn:
        conn.execute("DELETE FROM quiz_attempt_progress WHERE profile_id = ?", (int(profile_id),))


def list_quiz_sets() -> list[QuizSet]:
    with managed_connection() as conn:
        rows = conn.execute(
            """
            SELECT id, name, skill, question_type, num_questions, level,
                   mode_intuition_pct, mode_expression_pct, mode_word_pct
            FROM quiz_sets
            WHERE sync_deleted = 0
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
    sync_id = str(uuid.uuid4())
    with managed_connection() as conn:
        cur = conn.execute(
            """
            INSERT INTO quiz_sets
            (name, skill, question_type, num_questions, level, mode_intuition_pct, mode_expression_pct, mode_word_pct,
             created_at, sync_id, sync_updated_at, sync_deleted)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
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
                sync_id,
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
    updated_at: str | None = None,
) -> None:
    sync_updated_at = updated_at or _sync_now_text()
    with managed_connection() as conn:
        conn.execute(
            """
            UPDATE quiz_sets
            SET name = ?, skill = ?, question_type = ?, num_questions = ?, level = ?,
                mode_intuition_pct = ?, mode_expression_pct = ?, mode_word_pct = ?,
                sync_updated_at = ?, sync_deleted = 0
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
                sync_updated_at,
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
    sync_id = str(uuid.uuid4())
    with managed_connection() as conn:
        cur = conn.execute(
            """
            INSERT INTO quiz_attempts
            (profile_id, quiz_set_id, skill, question_type, num_questions, level, score, elapsed_seconds, created_at,
             sync_id, sync_updated_at, sync_deleted)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
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
                sync_id,
                created_at,
            ),
        )
        return int(cur.lastrowid)


def add_question_result(
    attempt_id: int,
    skill: str,
    subskill: str | None,
    question_label: str,
    mode: str,
    prompt: str,
    correct_answer: str,
    user_answer: str,
    is_correct: bool,
    explanation: str,
    sync_updated_at: str | None = None,
) -> int:
    row_sync_id = str(uuid.uuid4())
    updated_at = sync_updated_at or _sync_now_text()
    with managed_connection() as conn:
        cur = conn.execute(
            """
            INSERT INTO quiz_questions
            (attempt_id, skill, subskill, question_label, mode, prompt, correct_answer, user_answer, is_correct, explanation,
             sync_id, sync_updated_at, sync_deleted)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
            """,
            (
                attempt_id,
                skill,
                subskill,
                question_label,
                mode,
                prompt,
                correct_answer,
                user_answer,
                int(is_correct),
                explanation,
                row_sync_id,
                updated_at,
            ),
        )
        return int(cur.lastrowid)


def has_active_question_templates(skill: str, *, subskill: str | None = None, mode: str | None = None) -> bool:
    with managed_connection() as conn:
        clauses = ["active = 1", "skill = ?"]
        params: list[object] = [skill]
        if subskill is not None:
            clauses.append("subskill = ?")
            params.append(subskill)
        if mode is not None:
            clauses.append("mode = ?")
            params.append(mode)
        query = "SELECT 1 FROM question_templates WHERE " + " AND ".join(clauses) + " LIMIT 1"
        row = conn.execute(query, tuple(params)).fetchone()
    return row is not None


def template_modes_for_skill(skill: str, *, subskill: str | None = None) -> tuple[str, ...]:
    with managed_connection() as conn:
        if subskill is None:
            rows = conn.execute(
                """
                SELECT DISTINCT mode
                FROM question_templates
                WHERE active = 1 AND skill = ?
                ORDER BY mode ASC
                """,
                (skill,),
            ).fetchall()
        else:
            rows = conn.execute(
                """
                SELECT DISTINCT mode
                FROM question_templates
                WHERE active = 1 AND skill = ? AND subskill = ?
                ORDER BY mode ASC
                """,
                (skill, subskill),
            ).fetchall()
    return tuple(str(row["mode"]) for row in rows if row["mode"])


def list_attempts(profile_id: int) -> list[QuizAttempt]:
    with managed_connection() as conn:
        rows = conn.execute(
            """
            SELECT id, profile_id, quiz_set_id, skill, question_type, num_questions, level, score, elapsed_seconds, created_at
            FROM quiz_attempts
            WHERE profile_id = ? AND sync_deleted = 0
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
    with managed_connection() as conn:
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
    with managed_connection() as conn:
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


def rebuild_subskill_progress(profile_id: int, streak_to_master: int) -> None:
    with managed_connection() as conn:
        rows = conn.execute(
            """
            SELECT q.skill, q.subskill, q.is_correct, a.created_at
            FROM quiz_questions q
            JOIN quiz_attempts a ON a.id = q.attempt_id
            WHERE a.profile_id = ?
              AND a.sync_deleted = 0
              AND q.sync_deleted = 0
              AND q.subskill IS NOT NULL
            ORDER BY a.created_at ASC, a.id ASC, q.id ASC
            """,
            (int(profile_id),),
        ).fetchall()

        conn.execute(
            "DELETE FROM skill_subskill_progress WHERE profile_id = ?",
            (int(profile_id),),
        )

        state: dict[tuple[str, str], tuple[int, int, bool, str]] = {}
        for row in rows:
            key = (str(row["skill"]), str(row["subskill"]))
            current_streak, best_streak, mastered, _updated_at = state.get(key, (0, 0, False, ""))
            is_correct = bool(int(row["is_correct"]))
            current_streak = current_streak + 1 if is_correct else 0
            best_streak = max(best_streak, current_streak)
            mastered = mastered or current_streak >= int(streak_to_master)
            state[key] = (current_streak, best_streak, mastered, str(row["created_at"]))

        for (skill, subskill), (current_streak, best_streak, mastered, updated_at) in state.items():
            conn.execute(
                """
                INSERT INTO skill_subskill_progress
                (profile_id, skill, subskill, current_streak, best_streak, mastered, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    int(profile_id),
                    skill,
                    subskill,
                    int(current_streak),
                    int(best_streak),
                    1 if mastered else 0,
                    updated_at,
                ),
            )


def create_book(title: str, source: str, pdf_filename: str, created_at: str) -> Book:
    with managed_connection() as conn:
        cur = conn.execute(
            "INSERT INTO books (title, source, pdf_filename, created_at) VALUES (?, ?, ?, ?)",
            (title, source, pdf_filename, created_at),
        )
        book_id = int(cur.lastrowid)
    return Book(book_id, title, source, pdf_filename)


def list_books() -> list[Book]:
    with managed_connection() as conn:
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
    with managed_connection() as conn:
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
    with managed_connection() as conn:
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
    with managed_connection() as conn:
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
    with managed_connection() as conn:
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
    with managed_connection() as conn:
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
    with managed_connection() as conn:
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
    with managed_connection() as conn:
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
    with managed_connection() as conn:
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
    with managed_connection() as conn:
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
    with managed_connection() as conn:
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
    with managed_connection() as conn:
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


def delete_templates_by_identity(*, skill: str, subskill: str, label: str) -> int:
    with managed_connection() as conn:
        cur = conn.execute(
            """
            DELETE FROM question_templates
            WHERE skill = ? AND subskill = ? AND label = ?
            """,
            (skill, subskill, label),
        )
        return int(cur.rowcount)


def delete_template_by_external_id(external_id: str) -> int:
    with managed_connection() as conn:
        cur = conn.execute("DELETE FROM question_templates WHERE external_id = ?", (external_id,))
        return int(cur.rowcount)


def list_template_vars(template_id: int) -> list[TemplateVar]:
    with managed_connection() as conn:
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
    with managed_connection() as conn:
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


def skill_progress_pipeline(profile_id: int) -> dict[str, dict[str, int]]:
    out: dict[str, dict[str, int]] = {}
    with managed_connection() as conn:
        attempt_rows = conn.execute(
            """
            SELECT skill, COUNT(*) AS attempts, SUM(num_questions) AS questions
            FROM quiz_attempts
            WHERE profile_id = ? AND sync_deleted = 0
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
    sync_id = str(uuid.uuid4())
    with managed_connection() as conn:
        cur = conn.execute(
            """
            INSERT INTO assignments
            (profile_id, skill, subskill, target_type, target_value, level, num_questions, question_type,
             mode_intuition_pct, mode_expression_pct, mode_word_pct, notes, created_at,
             sync_id, sync_updated_at, sync_deleted)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
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
                sync_id,
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
    clauses: list[str] = ["profile_id = ?", "sync_deleted = 0"]
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
    with managed_connection() as conn:
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


def assignment_completion_analytics(
    profile_id: int,
    recent_days: int = 30,
    now_iso_text: str | None = None,
) -> dict[str, object]:
    recent_days = max(1, int(recent_days))
    active_items = list_assignments(profile_id, active_only=True)
    done_items = list_assignments(profile_id, active_only=False)
    now = _parse_iso_utc(now_iso_text) if now_iso_text else datetime.now(timezone.utc)
    if now is None:
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
    sync_updated_at = completed_at or _sync_now_text()
    with managed_connection() as conn:
        conn.execute(
            """
            UPDATE assignments
            SET active = ?, completed_at = ?, sync_updated_at = ?, sync_deleted = 0
            WHERE id = ?
            """,
            (
                1 if active else 0,
                completed_at if not active else None,
                sync_updated_at,
                int(assignment_id),
            ),
        )


def get_next_active_assignment(profile_id: int) -> Assignment | None:
    items = list_assignments(profile_id, active_only=True)
    return items[0] if items else None


def evaluate_assignments_for_attempt(profile_id: int, attempt_id: int, completed_at: str) -> int:
    return len(evaluate_assignments_for_attempt_ids(profile_id, attempt_id, completed_at))


def evaluate_assignments_for_attempt_ids(profile_id: int, attempt_id: int, completed_at: str) -> list[int]:
    completed_ids: list[int] = []
    with managed_connection() as conn:
        attempt = conn.execute(
            """
            SELECT id, profile_id, skill, score, num_questions
            FROM quiz_attempts
            WHERE id = ? AND profile_id = ? AND sync_deleted = 0
            """,
            (int(attempt_id), int(profile_id)),
        ).fetchone()
        if attempt is None:
            return []

        assignments = conn.execute(
            """
            SELECT id, skill, subskill, target_type, target_value
            FROM assignments
            WHERE profile_id = ? AND active = 1 AND sync_deleted = 0
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
                    """
                    UPDATE assignments
                    SET active = 0, completed_at = ?, sync_updated_at = ?, sync_deleted = 0
                    WHERE id = ?
                    """,
                    (completed_at, completed_at, int(item["id"])),
                )
                completed_ids.append(int(item["id"]))
    return completed_ids


def create_summer_program(
    *,
    profile_id: int,
    lane: str,
    start_date: str,
    end_date: str,
    days_per_week: int,
    minutes_per_session: int,
    status: str,
    finish_definition: str,
    placement_recommendation: str | None,
    placement_review_status: str,
    placement_reviewed_at: str | None,
    student_age_years: int | None,
    created_at: str,
    updated_at: str,
) -> SummerProgram:
    with managed_connection() as conn:
        cur = conn.execute(
            """
            INSERT INTO summer_programs
            (profile_id, lane, start_date, end_date, days_per_week, minutes_per_session, status,
             finish_definition, placement_recommendation, placement_review_status, placement_reviewed_at,
             student_age_years, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                int(profile_id),
                lane,
                start_date,
                end_date,
                int(days_per_week),
                int(minutes_per_session),
                status,
                finish_definition,
                placement_recommendation,
                placement_review_status,
                placement_reviewed_at,
                int(student_age_years) if student_age_years is not None else None,
                created_at,
                updated_at,
            ),
        )
        program_id = int(cur.lastrowid)
    program = get_summer_program(program_id)
    assert program is not None
    return program


_SUMMER_PROGRAM_UNSET = object()


def update_summer_program(
    program_id: int,
    *,
    lane: str | object = _SUMMER_PROGRAM_UNSET,
    status: str | object = _SUMMER_PROGRAM_UNSET,
    placement_recommendation: str | None | object = _SUMMER_PROGRAM_UNSET,
    placement_review_status: str | object = _SUMMER_PROGRAM_UNSET,
    placement_reviewed_at: str | None | object = _SUMMER_PROGRAM_UNSET,
    updated_at: str,
) -> None:
    assignments = ["updated_at = ?"]
    params: list[object] = [updated_at]
    if lane is not _SUMMER_PROGRAM_UNSET:
        assignments.append("lane = ?")
        params.append(lane)
    if status is not _SUMMER_PROGRAM_UNSET:
        assignments.append("status = ?")
        params.append(status)
    if placement_recommendation is not _SUMMER_PROGRAM_UNSET:
        assignments.append("placement_recommendation = ?")
        params.append(placement_recommendation)
    if placement_review_status is not _SUMMER_PROGRAM_UNSET:
        assignments.append("placement_review_status = ?")
        params.append(placement_review_status)
    if placement_reviewed_at is not _SUMMER_PROGRAM_UNSET:
        assignments.append("placement_reviewed_at = ?")
        params.append(placement_reviewed_at)
    params.append(int(program_id))
    with managed_connection() as conn:
        conn.execute(
            f"UPDATE summer_programs SET {', '.join(assignments)} WHERE id = ?",
            tuple(params),
        )


def archive_summer_programs(profile_id: int, *, archived_at: str) -> None:
    with managed_connection() as conn:
        conn.execute(
            """
            UPDATE summer_programs
            SET status = 'archived', updated_at = ?
            WHERE profile_id = ? AND status IN ('active', 'completed')
            """,
            (archived_at, int(profile_id)),
        )


def get_summer_program(program_id: int) -> SummerProgram | None:
    with managed_connection() as conn:
        row = conn.execute(
            """
            SELECT id, profile_id, lane, start_date, end_date, days_per_week, minutes_per_session,
                   status, finish_definition, placement_recommendation, placement_review_status,
                   placement_reviewed_at, student_age_years, created_at, updated_at
            FROM summer_programs
            WHERE id = ?
            """,
            (int(program_id),),
        ).fetchone()
    return _row_to_summer_program(row) if row is not None else None


def get_active_summer_program(profile_id: int) -> SummerProgram | None:
    with managed_connection() as conn:
        row = conn.execute(
            """
            SELECT id, profile_id, lane, start_date, end_date, days_per_week, minutes_per_session,
                   status, finish_definition, placement_recommendation, placement_review_status,
                   placement_reviewed_at, student_age_years, created_at, updated_at
            FROM summer_programs
            WHERE profile_id = ? AND status IN ('active', 'completed')
            ORDER BY updated_at DESC, id DESC
            LIMIT 1
            """,
            (int(profile_id),),
        ).fetchone()
    return _row_to_summer_program(row) if row is not None else None


def list_summer_programs(profile_id: int, *, include_inactive: bool = False) -> list[SummerProgram]:
    where_sql = "profile_id = ?" if include_inactive else "profile_id = ? AND status IN ('active', 'completed')"
    with managed_connection() as conn:
        rows = conn.execute(
            f"""
            SELECT id, profile_id, lane, start_date, end_date, days_per_week, minutes_per_session,
                   status, finish_definition, placement_recommendation, placement_review_status,
                   placement_reviewed_at, student_age_years, created_at, updated_at
            FROM summer_programs
            WHERE {where_sql}
            ORDER BY updated_at DESC, id DESC
            """,
            (int(profile_id),),
        ).fetchall()
    return [_row_to_summer_program(row) for row in rows]


def replace_summer_program_tasks(program_id: int, payloads: list[dict[str, object]], *, updated_at: str) -> None:
    with managed_connection() as conn:
        conn.execute("DELETE FROM summer_program_tasks WHERE program_id = ?", (int(program_id),))
        for item in payloads:
            conn.execute(
                """
                INSERT INTO summer_program_tasks
                (program_id, unit_code, task_kind, skill, subskill, sequence_index, status,
                 target_score_pct, scheduled_date, notes_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    int(program_id),
                    str(item["unit_code"]),
                    str(item["task_kind"]),
                    str(item["skill"]),
                    item.get("subskill"),
                    int(item["sequence_index"]),
                    str(item["status"]),
                    float(item["target_score_pct"]) if item.get("target_score_pct") is not None else None,
                    str(item["scheduled_date"]),
                    str(item.get("notes_json", "{}")),
                ),
            )
        conn.execute(
            "UPDATE summer_programs SET updated_at = ? WHERE id = ?",
            (updated_at, int(program_id)),
        )


def create_summer_program_task(
    *,
    program_id: int,
    unit_code: str,
    task_kind: str,
    skill: str,
    subskill: str | None,
    sequence_index: int,
    status: str,
    target_score_pct: float | None,
    scheduled_date: str,
    notes_json: str = "{}",
) -> SummerProgramTask:
    with managed_connection() as conn:
        cur = conn.execute(
            """
            INSERT INTO summer_program_tasks
            (program_id, unit_code, task_kind, skill, subskill, sequence_index, status,
             target_score_pct, scheduled_date, notes_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                int(program_id),
                unit_code,
                task_kind,
                skill,
                subskill,
                int(sequence_index),
                status,
                float(target_score_pct) if target_score_pct is not None else None,
                scheduled_date,
                notes_json,
            ),
        )
        task_id = int(cur.lastrowid)
    task = get_summer_program_task(task_id)
    assert task is not None
    return task


def shift_summer_program_task_sequences(program_id: int, *, starting_from: int, delta: int) -> None:
    if delta == 0:
        return
    with managed_connection() as conn:
        conn.execute(
            """
            UPDATE summer_program_tasks
            SET sequence_index = sequence_index + ?
            WHERE program_id = ? AND sequence_index >= ?
            """,
            (int(delta), int(program_id), int(starting_from)),
        )


def get_summer_program_task(task_id: int) -> SummerProgramTask | None:
    with managed_connection() as conn:
        row = conn.execute(
            """
            SELECT id, program_id, unit_code, task_kind, skill, subskill, sequence_index, status,
                   target_score_pct, scheduled_date, notes_json
            FROM summer_program_tasks
            WHERE id = ?
            """,
            (int(task_id),),
        ).fetchone()
    return _row_to_summer_program_task(row) if row is not None else None


def list_summer_program_tasks(program_id: int) -> list[SummerProgramTask]:
    with managed_connection() as conn:
        rows = conn.execute(
            """
            SELECT id, program_id, unit_code, task_kind, skill, subskill, sequence_index, status,
                   target_score_pct, scheduled_date, notes_json
            FROM summer_program_tasks
            WHERE program_id = ?
            ORDER BY sequence_index ASC, id ASC
            """,
            (int(program_id),),
        ).fetchall()
    return [_row_to_summer_program_task(row) for row in rows]


_SUMMER_PROGRAM_TASK_UNSET = object()


def update_summer_program_task(
    task_id: int,
    *,
    status: str | object = _SUMMER_PROGRAM_TASK_UNSET,
    notes_json: str | object = _SUMMER_PROGRAM_TASK_UNSET,
    scheduled_date: str | object = _SUMMER_PROGRAM_TASK_UNSET,
) -> None:
    assignments: list[str] = []
    params: list[object] = []
    if status is not _SUMMER_PROGRAM_TASK_UNSET:
        assignments.append("status = ?")
        params.append(status)
    if notes_json is not _SUMMER_PROGRAM_TASK_UNSET:
        assignments.append("notes_json = ?")
        params.append(notes_json)
    if scheduled_date is not _SUMMER_PROGRAM_TASK_UNSET:
        assignments.append("scheduled_date = ?")
        params.append(scheduled_date)
    if not assignments:
        return
    params.append(int(task_id))
    with managed_connection() as conn:
        conn.execute(
            """
            UPDATE summer_program_tasks
            SET {assignments}
            WHERE id = ?
            """.replace("{assignments}", ", ".join(assignments)),
            tuple(params),
        )


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


def record_daily_review_completion(profile_id: int, completed_at: str) -> None:
    day_utc = _iso_day_utc(completed_at)
    with managed_connection() as conn:
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
    with managed_connection() as conn:
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


def _row_to_summer_program(r: sqlite3.Row) -> SummerProgram:
    return SummerProgram(
        id=int(r["id"]),
        profile_id=int(r["profile_id"]),
        lane=str(r["lane"]),
        start_date=str(r["start_date"]),
        end_date=str(r["end_date"]),
        days_per_week=int(r["days_per_week"]),
        minutes_per_session=int(r["minutes_per_session"]),
        status=str(r["status"]),
        finish_definition=str(r["finish_definition"]),
        placement_recommendation=str(r["placement_recommendation"]) if r["placement_recommendation"] is not None else None,
        placement_review_status=str(r["placement_review_status"] or "accepted"),
        placement_reviewed_at=str(r["placement_reviewed_at"]) if r["placement_reviewed_at"] is not None else None,
        student_age_years=int(r["student_age_years"]) if r["student_age_years"] is not None else None,
        created_at=str(r["created_at"]),
        updated_at=str(r["updated_at"]),
    )


def _row_to_summer_program_task(r: sqlite3.Row) -> SummerProgramTask:
    return SummerProgramTask(
        id=int(r["id"]),
        program_id=int(r["program_id"]),
        unit_code=str(r["unit_code"]),
        task_kind=str(r["task_kind"]),
        skill=str(r["skill"]),
        subskill=str(r["subskill"]) if r["subskill"] is not None else None,
        sequence_index=int(r["sequence_index"]),
        status=str(r["status"]),
        target_score_pct=float(r["target_score_pct"]) if r["target_score_pct"] is not None else None,
        scheduled_date=str(r["scheduled_date"]),
        notes_json=str(r["notes_json"]),
    )


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


def _hash_pin(pin: str, salt_hex: str) -> str:
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        pin.encode("utf-8"),
        bytes.fromhex(salt_hex),
        PIN_HASH_ITERATIONS,
    )
    return digest.hex()


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


def _sync_now_text() -> str:
    return datetime.now(timezone.utc).isoformat()
