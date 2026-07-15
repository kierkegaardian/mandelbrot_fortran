from __future__ import annotations

from .connection import managed_connection
from .migrations import _run_migrations

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
