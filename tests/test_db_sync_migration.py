from __future__ import annotations

from contextlib import closing
from typing import Any
from unittest.mock import patch
import sqlite3
import tempfile
import unittest
import uuid
from pathlib import Path

from app import db, sync_service, sync_state, sync_store
from app.sync_client import SyncBatchResult, SyncEndpointResult, SyncStatus


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "pre_sync_app_db_v11.sql"
SYNC_TABLES = ("profiles", "quiz_sets", "assignments", "quiz_attempts", "quiz_questions")


class DbSyncMigrationTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self._root = Path(self._tmp.name)
        self._db_path = self._root / "app.db"
        self._state_root = self._root / "state"
        self._state_root.mkdir()
        self._orig_data_dir = sync_state.data_dir

        self.enterContext(db.override_db_config(db.DbConfig(path=str(self._db_path))))
        sync_state.data_dir = lambda: self._state_root
        with closing(sqlite3.connect(self._db_path)) as conn:
            conn.executescript(FIXTURE_PATH.read_text())
            conn.commit()

    def tearDown(self) -> None:
        sync_state.data_dir = self._orig_data_dir
        self._tmp.cleanup()

    def test_pre_sync_fixture_upgrades_without_enabling_sync(self) -> None:
        db.init_db()

        self.assertFalse(sync_state.load_sync_state().sync_enabled)
        self.assertFalse((self._state_root / "sync_state.json").exists())
        with db.managed_connection() as conn:
            version = conn.execute("SELECT version FROM schema_version WHERE id = 1").fetchone()
            self.assertEqual(int(version["version"]), 17)
            self.assertEqual(conn.execute("PRAGMA foreign_key_check").fetchall(), [])
            profile_rows = conn.execute("SELECT id, name FROM profiles ORDER BY id").fetchall()
            self.assertEqual(
                [(int(row["id"]), str(row["name"])) for row in profile_rows],
                [(1, "Legacy Parent"), (2, "Legacy Child")],
            )
            for table in SYNC_TABLES:
                rows = conn.execute(
                    f"SELECT sync_id, sync_updated_at, sync_deleted FROM {table} ORDER BY id"
                ).fetchall()
                self.assertTrue(rows)
                for row in rows:
                    uuid.UUID(str(row["sync_id"]))
                    self.assertTrue(str(row["sync_updated_at"]))
                    self.assertEqual(int(row["sync_deleted"]), 0)
            worksheet = conn.execute("SELECT file_path FROM worksheets WHERE id = 40").fetchone()
            parent_auth = conn.execute("SELECT pin_hash FROM parent_auth WHERE profile_id = 1").fetchone()
            resume = conn.execute("SELECT state_json FROM quiz_attempt_progress WHERE attempt_id = 50").fetchone()
            self.assertEqual(str(worksheet["file_path"]), "/legacy/worksheet.pdf")
            self.assertEqual(str(parent_auth["pin_hash"]), "legacy-pin-hash")
            self.assertEqual(str(resume["state_json"]), '{"version":1,"pending":true}')

        pending = sync_store.list_pending_changes(limit=20)
        self.assertEqual(
            [entry.entity_type for entry in pending],
            ["profiles", "profiles", "quiz_sets", "assignments", "quiz_attempts", "quiz_questions"],
        )
        with patch.object(sync_service.sync_client, "sync_now") as network_probe:
            result = sync_service.sync_now()
        network_probe.assert_not_called()
        self.assertFalse(result.attempted)
        self.assertEqual(result.pending_count, 6)

        db.init_db()
        self.assertEqual(sync_store.count_pending_changes(), 6)

    def test_migrated_rows_upload_when_sync_is_enabled_later(self) -> None:
        db.init_db()
        sync_state.save_sync_enabled(True)
        sync_state.save_sync_pairing(family_id="legacy-family", pairing_token="pair-123")
        uploaded: list[dict[str, Any]] = []

        def accept_batch(
            *,
            family_id: str,
            pairing_token: str,
            device_id: str,
            since_cursor: int,
            changes: list[dict[str, Any]],
        ) -> SyncBatchResult:
            self.assertEqual(family_id, "legacy-family")
            self.assertEqual(pairing_token, "pair-123")
            self.assertTrue(device_id)
            self.assertEqual(since_cursor, 0)
            uploaded.extend(changes)
            return SyncBatchResult(
                ok=True,
                server_cursor=6,
                accepted_client_change_ids=[int(change["client_change_id"]) for change in changes],
                changes=[],
                error_code=None,
                error_message=None,
                response=_success_endpoint(),
            )

        with (
            patch.object(sync_service.sync_client, "sync_now", return_value=_success_status()),
            patch.object(sync_service.sync_client, "sync_batch", side_effect=accept_batch),
        ):
            result = sync_service.sync_now()

        self.assertTrue(result.ok)
        self.assertEqual(result.uploaded_count, 6)
        self.assertEqual(sync_store.count_pending_changes(), 0)
        self.assertEqual(
            [str(change["entity_type"]) for change in uploaded],
            ["profiles", "profiles", "quiz_sets", "assignments", "quiz_attempts", "quiz_questions"],
        )
        profiles = {str(change["data"]["name"]): change for change in uploaded if change["entity_type"] == "profiles"}
        quiz_set = next(change for change in uploaded if change["entity_type"] == "quiz_sets")
        assignment = next(change for change in uploaded if change["entity_type"] == "assignments")
        attempt = next(change for change in uploaded if change["entity_type"] == "quiz_attempts")
        question = next(change for change in uploaded if change["entity_type"] == "quiz_questions")
        self.assertEqual(assignment["data"]["profile_sync_id"], profiles["Legacy Child"]["entity_sync_id"])
        self.assertEqual(attempt["data"]["profile_sync_id"], profiles["Legacy Child"]["entity_sync_id"])
        self.assertEqual(attempt["data"]["quiz_set_sync_id"], quiz_set["entity_sync_id"])
        self.assertEqual(question["data"]["attempt_sync_id"], attempt["entity_sync_id"])


def _success_endpoint() -> SyncEndpointResult:
    return SyncEndpointResult(
        ok=True,
        url="http://127.0.0.1:8091/api/v1/sync",
        status_code=200,
        data={},
        raw_text="{}",
        error_code=None,
        error_message=None,
    )


def _success_status() -> SyncStatus:
    endpoint = _success_endpoint()
    return SyncStatus(
        ok=True,
        config_available=True,
        server_base_url="http://127.0.0.1:8091",
        server_label="Fixture sync server",
        profile="fixture",
        config_source="test",
        config_path="/tmp/sync.fixture.json",
        health=endpoint,
        api_root=endpoint,
        error_code=None,
        error_message=None,
    )


if __name__ == "__main__":
    unittest.main()
