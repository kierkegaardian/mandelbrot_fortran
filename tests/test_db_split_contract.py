from __future__ import annotations

import importlib
from pathlib import Path
import tempfile
import unittest

from app import db, quiz_engine, sync_store


EXPECTED_DB_EXPORTS = (
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

EXPECTED_QUIZ_ENGINE_EXPORTS = (
    "ALGEBRA_LINEAR_SUBSKILLS",
    "ContentUnavailableError",
    "GEOMETRY_AREA_SUBSKILLS",
    "LEGACY_SKILL_ALIASES",
    "MEASUREMENT_SUBSKILLS",
    "PLACE_VALUE_SUBSKILLS",
    "QUESTION_TYPES",
    "Question",
    "RIGHT_TRIANGLE_TRIPLES",
    "SKILLS",
    "TRIG_PRECALCULUS_SUBSKILLS",
    "generate_question",
)

DB_CONSUMER_MODULES = (
    "app.content_audit",
    "app.fall_readiness_audit",
    "app.school_year",
    "app.summer_program",
    "app.sync_service",
    "app.sync_store",
    "app.ui_dashboard",
    "app.ui_skill_map",
    "scripts.import_template_manifest",
    "scripts.ingest_textbook",
    "scripts.template_catalog",
)


def _file_state(path: Path) -> tuple[int, int] | None:
    if not path.exists():
        return None
    stat = path.stat()
    return (stat.st_size, stat.st_mtime_ns)


class DbSplitContractTests(unittest.TestCase):
    def test_public_export_inventories_are_frozen_and_importable(self) -> None:
        self.assertEqual(EXPECTED_DB_EXPORTS, db.__all__)
        self.assertEqual(EXPECTED_QUIZ_ENGINE_EXPORTS, quiz_engine.__all__)
        for module, expected in ((db, EXPECTED_DB_EXPORTS), (quiz_engine, EXPECTED_QUIZ_ENGINE_EXPORTS)):
            with self.subTest(module=module.__name__):
                missing = [name for name in expected if not hasattr(module, name)]
                self.assertEqual([], missing)

    def test_broad_db_consumers_and_scripts_import(self) -> None:
        for module_name in DB_CONSUMER_MODULES:
            with self.subTest(module=module_name):
                self.assertIsNotNone(importlib.import_module(module_name))

    def test_shared_override_routes_schema_and_consumer_writes_to_temp_db(self) -> None:
        original_config = db.get_db_config()
        original_path = Path(original_config.path)
        original_state = _file_state(original_path)

        with tempfile.TemporaryDirectory() as tmp_dir:
            test_path = Path(tmp_dir) / "override.db"
            self.assertNotEqual(original_path.resolve(), test_path.resolve())

            with db.override_db_config(db.DbConfig(path=str(test_path))):
                self.assertEqual(test_path, Path(db.db_config().path))
                db.init_db()
                profile = db.create_profile("Contract Child", "child", "2026-07-13T00:00:00+00:00")
                self.assertIsNotNone(sync_store.entity_sync_id("profiles", profile.id))
                with db.managed_connection() as conn:
                    row = conn.execute("SELECT name FROM profiles WHERE id = ?", (profile.id,)).fetchone()
                self.assertIsNotNone(row)
                assert row is not None
                self.assertEqual("Contract Child", str(row["name"]))

            self.assertTrue(test_path.exists())

        self.assertEqual(original_config, db.get_db_config())
        self.assertEqual(original_state, _file_state(original_path))


if __name__ == "__main__":
    unittest.main()
