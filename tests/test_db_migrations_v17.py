from __future__ import annotations

from collections import Counter
from contextlib import contextmanager
from pathlib import Path
import sqlite3
import tempfile
from typing import Iterator
import unittest
from unittest.mock import patch
import uuid

from app import db


FIXTURE_DIR = Path(__file__).parent / "fixtures"
SYNC_TABLES = ("profiles", "quiz_sets", "assignments", "quiz_attempts", "quiz_questions")
V17_TABLES = {
    "parent_auth",
    "quiz_attempt_progress",
    "school_year_targets",
    "summer_assessment_runs",
    "summer_program_tasks",
    "summer_programs",
    "sync_outbox",
}


@contextmanager
def _upgraded_fixture(filename: str) -> Iterator[Path]:
    with tempfile.TemporaryDirectory() as directory:
        db_path = Path(directory) / "app.db"
        connection = sqlite3.connect(db_path)
        try:
            connection.executescript((FIXTURE_DIR / filename).read_text(encoding="utf-8"))
            connection.commit()
        finally:
            connection.close()
        with db.override_db_config(db.DbConfig(path=str(db_path))):
            db.init_db()
            yield db_path


class DbMigrationV17Tests(unittest.TestCase):
    def setUp(self) -> None:
        db.reset_db_config()
        self.addCleanup(db.reset_db_config)

    def test_migrations_stop_at_v17_without_product_or_ui_imports(self) -> None:
        db_dir = Path(db.__file__).parent
        migrations = (db_dir / "migrations.py").read_text(encoding="utf-8")
        helpers = (db_dir / "migration_helpers.py").read_text(encoding="utf-8")
        self.assertIn("version = 17", migrations)
        self.assertNotIn("version = 18", migrations)
        self.assertNotIn("summer_program_template_seed", helpers)
        self.assertNotIn("ui_", helpers)

    def test_fresh_install_reaches_v17_and_reinitializes_idempotently(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            db_path = Path(directory) / "fresh.db"
            with db.override_db_config(db.DbConfig(path=str(db_path))):
                db.init_db()
                with db.managed_connection() as connection:
                    self.assertEqual(17, self._schema_version(connection))
                    self.assertEqual([], connection.execute("PRAGMA foreign_key_check").fetchall())
                    tables = {
                        str(row["name"])
                        for row in connection.execute(
                            "SELECT name FROM sqlite_master WHERE type = 'table'"
                        ).fetchall()
                    }
                    self.assertTrue(V17_TABLES.issubset(tables))
                    self.assertEqual(0, self._pending_outbox_count(connection))
                    schema_before = self._schema_snapshot(connection)

                db.init_db()
                with db.managed_connection() as connection:
                    self.assertEqual(17, self._schema_version(connection))
                    self.assertEqual([], connection.execute("PRAGMA foreign_key_check").fetchall())
                    self.assertEqual(schema_before, self._schema_snapshot(connection))
                    self.assertEqual(0, self._pending_outbox_count(connection))

    def test_populated_v9_upgrade_preserves_all_legacy_domains(self) -> None:
        with _upgraded_fixture("pre_persistence_app_db_v9.sql"):
            with db.managed_connection() as connection:
                self._assert_upgrade_health(connection)
                expected_counts = {
                    "profiles": 2,
                    "quiz_sets": 1,
                    "quiz_attempts": 1,
                    "quiz_questions": 1,
                    "worksheets": 1,
                    "skill_subskill_progress": 1,
                    "assignments": 1,
                    "daily_goal_history": 1,
                    "books": 1,
                    "exercise_candidates": 1,
                    "question_templates": 1,
                    "template_vars": 1,
                    "historical_tests": 1,
                    "historical_questions": 1,
                }
                for table, expected in expected_counts.items():
                    with self.subTest(table=table):
                        row = connection.execute(f"SELECT COUNT(*) AS count FROM {table}").fetchone()
                        self.assertEqual(expected, int(row["count"]))
                question = connection.execute(
                    "SELECT prompt, correct_answer FROM quiz_questions WHERE id = 1"
                ).fetchone()
                worksheet = connection.execute(
                    "SELECT file_path, archived_at FROM worksheets WHERE id = 1"
                ).fetchone()
                self.assertEqual(("1/2 + 1/4", "3/4"), tuple(question))
                self.assertEqual(("/legacy/fractions-worksheet.pdf", None), tuple(worksheet))
                self.assertEqual(0, connection.execute("SELECT COUNT(*) FROM parent_auth").fetchone()[0])
                self.assertEqual(0, connection.execute("SELECT COUNT(*) FROM summer_programs").fetchone()[0])
            self._assert_stable_exactly_once_backfill()

    def test_populated_v11_upgrade_preserves_pin_resume_and_credited_history(self) -> None:
        with _upgraded_fixture("pre_sync_app_db_v11.sql"):
            with db.managed_connection() as connection:
                self._assert_upgrade_health(connection)
                profile_names = [
                    str(row["name"])
                    for row in connection.execute("SELECT name FROM profiles ORDER BY id").fetchall()
                ]
                self.assertEqual(["Legacy Parent", "Legacy Child"], profile_names)
                self.assertEqual(
                    "legacy-pin-hash",
                    connection.execute(
                        "SELECT pin_hash FROM parent_auth WHERE profile_id = 1"
                    ).fetchone()["pin_hash"],
                )
                self.assertEqual(
                    '{"version":1,"pending":true}',
                    connection.execute(
                        "SELECT state_json FROM quiz_attempt_progress WHERE attempt_id = 50"
                    ).fetchone()["state_json"],
                )
                question = connection.execute(
                    "SELECT subskill, correct_answer FROM quiz_questions WHERE id = 30"
                ).fetchone()
                self.assertEqual(("Sums within 20", "12"), tuple(question))
                self.assertEqual(
                    "/legacy/worksheet.pdf",
                    connection.execute("SELECT file_path FROM worksheets WHERE id = 40").fetchone()[0],
                )
                self.assertEqual(1, connection.execute("SELECT COUNT(*) FROM assignments").fetchone()[0])
                self.assertEqual(1, connection.execute("SELECT COUNT(*) FROM quiz_attempts").fetchone()[0])
            self._assert_stable_exactly_once_backfill()

    def test_v17_backfill_preserves_existing_pending_rows_without_duplicates(self) -> None:
        with _upgraded_fixture("pre_sync_app_db_v11.sql"):
            with db.managed_connection() as connection:
                kept = connection.execute(
                    """
                    SELECT id, entity_type, entity_sync_id
                    FROM sync_outbox
                    ORDER BY id
                    LIMIT 1
                    """
                ).fetchone()
                connection.execute("DELETE FROM sync_outbox WHERE id <> ?", (int(kept["id"]),))
                connection.execute("UPDATE schema_version SET version = 16 WHERE id = 1")

            db.init_db()

            with db.managed_connection() as connection:
                self.assertEqual(17, self._schema_version(connection))
                rows = connection.execute(
                    """
                    SELECT id, entity_type, entity_sync_id
                    FROM sync_outbox
                    WHERE synced_at IS NULL
                    ORDER BY id
                    """
                ).fetchall()
                self.assertEqual(6, len(rows))
                matching = [
                    row
                    for row in rows
                    if row["entity_type"] == kept["entity_type"]
                    and row["entity_sync_id"] == kept["entity_sync_id"]
                ]
                self.assertEqual(1, len(matching))
                self.assertEqual(int(kept["id"]), int(matching[0]["id"]))

    def test_reinitialization_does_not_scan_or_rewrite_complete_sync_rows(self) -> None:
        with _upgraded_fixture("pre_sync_app_db_v11.sql"):
            with (
                patch("app.db.migration_helpers.uuid.uuid4") as uuid_probe,
                patch("app.db.migration_helpers._sync_now_text") as time_probe,
            ):
                db.init_db()
            uuid_probe.assert_not_called()
            time_probe.assert_not_called()

    def _assert_upgrade_health(self, connection: sqlite3.Connection) -> None:
        self.assertEqual(17, self._schema_version(connection))
        self.assertEqual([], connection.execute("PRAGMA foreign_key_check").fetchall())
        tables = {
            str(row["name"])
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            ).fetchall()
        }
        self.assertTrue(V17_TABLES.issubset(tables))

    def _assert_stable_exactly_once_backfill(self) -> None:
        with db.managed_connection() as connection:
            sync_before = self._sync_snapshot(connection)
            expected = Counter(
                (table, sync_id)
                for table, rows in sync_before.items()
                for sync_id in rows.values()
            )
            actual_before = self._outbox_snapshot(connection)
            self.assertEqual(expected, actual_before)
            self.assertTrue(all(count == 1 for count in actual_before.values()))

        db.init_db()

        with db.managed_connection() as connection:
            self.assertEqual(sync_before, self._sync_snapshot(connection))
            self.assertEqual(actual_before, self._outbox_snapshot(connection))
            self.assertEqual([], connection.execute("PRAGMA foreign_key_check").fetchall())

    @staticmethod
    def _schema_version(connection: sqlite3.Connection) -> int:
        row = connection.execute("SELECT version FROM schema_version WHERE id = 1").fetchone()
        return int(row["version"])

    @staticmethod
    def _pending_outbox_count(connection: sqlite3.Connection) -> int:
        row = connection.execute(
            "SELECT COUNT(*) AS count FROM sync_outbox WHERE synced_at IS NULL"
        ).fetchone()
        return int(row["count"])

    @staticmethod
    def _schema_snapshot(connection: sqlite3.Connection) -> list[tuple[object, ...]]:
        rows = connection.execute(
            """
            SELECT type, name, tbl_name, sql
            FROM sqlite_master
            WHERE name NOT LIKE 'sqlite_%'
            ORDER BY type, name
            """
        ).fetchall()
        return [tuple(row) for row in rows]

    @staticmethod
    def _sync_snapshot(connection: sqlite3.Connection) -> dict[str, dict[int, str]]:
        snapshot: dict[str, dict[int, str]] = {}
        for table in SYNC_TABLES:
            rows = connection.execute(
                f"SELECT id, sync_id, sync_updated_at, sync_deleted FROM {table} ORDER BY id"
            ).fetchall()
            snapshot[table] = {}
            for row in rows:
                sync_id = str(row["sync_id"])
                uuid.UUID(sync_id)
                self_updated = str(row["sync_updated_at"])
                if not self_updated or int(row["sync_deleted"]) != 0:
                    raise AssertionError(f"invalid sync metadata in {table} row {row['id']}")
                snapshot[table][int(row["id"])] = sync_id
        return snapshot

    @staticmethod
    def _outbox_snapshot(connection: sqlite3.Connection) -> Counter[tuple[str, str]]:
        rows = connection.execute(
            """
            SELECT entity_type, entity_sync_id
            FROM sync_outbox
            WHERE synced_at IS NULL
            ORDER BY id
            """
        ).fetchall()
        return Counter((str(row["entity_type"]), str(row["entity_sync_id"])) for row in rows)


if __name__ == "__main__":
    unittest.main()
