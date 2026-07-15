from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app import db, sync_runner, sync_service, sync_state, sync_store
from app.sync_client import SyncBatchChange

from tests.test_sync_runner_safety import T0, _batch, _status

T1 = "2026-04-11T11:00:00+00:00"


class SyncAccessTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self._root = Path(self._tmp.name)
        self._old_data_dir = sync_state.data_dir
        self.enterContext(
            db.override_db_config(db.DbConfig(path=str(self._root / "app.db")))
        )
        sync_state.data_dir = lambda: self._root
        db.init_db()
        self.parent = db.create_profile("Parent", "parent", T0)
        self.child = db.create_profile("Child", "child", T0)

    def tearDown(self) -> None:
        sync_state.data_dir = self._old_data_dir
        self._tmp.cleanup()

    def test_enabled_unpaired_sync_fails_closed_without_auto_bootstrap(self) -> None:
        sync_state.save_sync_enabled(True)
        with (
            patch.object(sync_runner.sync_client, "sync_now") as probe,
            patch.object(sync_runner.sync_client, "bootstrap_family") as bootstrap,
        ):
            result = sync_service.sync_now(self.parent.id)

        probe.assert_not_called()
        bootstrap.assert_not_called()
        self.assertFalse(result.ok)
        self.assertFalse(result.attempted)
        self.assertIn("Start or join", result.message)
        self.assertIsNone(sync_state.load_sync_state().family_id)

    def test_child_profile_cannot_call_pairing_or_sync_service(self) -> None:
        sync_state.save_sync_enabled(True)
        sync_state.save_sync_pairing(family_id="family-1", pairing_token="pair-123")
        with (
            patch.object(sync_runner.sync_client, "sync_now") as probe,
            patch.object(sync_runner.sync_client, "bootstrap_family") as bootstrap,
            patch.object(sync_runner.sync_client, "join_family") as join,
        ):
            sync_result = sync_service.sync_now(self.child.id)
            start_result = sync_service.start_family_sync(self.child.id)
            join_result = sync_service.join_family_sync("new-pair", self.child.id)

        probe.assert_not_called()
        bootstrap.assert_not_called()
        join.assert_not_called()
        self.assertFalse(sync_result.ok)
        self.assertFalse(start_result.ok)
        self.assertFalse(join_result.ok)

    def test_cursor_rewind_rejects_ack_and_retains_pending_change(self) -> None:
        sync_state.save_sync_enabled(True)
        sync_state.save_sync_pairing(
            family_id="family-1", pairing_token="pair-123", server_cursor=10
        )
        sync_service.create_profile("Queued", "child", T0)
        entry = sync_store.list_pending_changes()[0]
        with (
            patch.object(sync_runner.sync_client, "sync_now", return_value=_status()),
            patch.object(
                sync_runner.sync_client,
                "sync_batch",
                return_value=_batch(cursor=9, accepted=[entry.id]),
            ),
        ):
            result = sync_service.sync_now(self.parent.id)

        self.assertFalse(result.ok)
        self.assertIn("backward", result.message)
        self.assertEqual(sync_state.load_sync_state().server_cursor, 10)
        self.assertEqual(sync_store.count_pending_changes(), 1)

    def test_catch_up_lifecycle_batch_advances_cursor(self) -> None:
        sync_state.save_sync_enabled(True)
        sync_state.save_sync_pairing(family_id="family-1", pairing_token="pair-123")
        changes = [
            SyncBatchChange(
                1,
                "profiles",
                "upsert",
                "old-profile",
                T0,
                {"name": "Old child", "role": "child", "created_at": T0},
            ),
            SyncBatchChange(
                2,
                "quiz_attempts",
                "upsert",
                "old-attempt",
                T0,
                {
                    "profile_sync_id": "old-profile",
                    "quiz_set_sync_id": None,
                    "skill": "counting",
                    "question_type": "typed",
                    "num_questions": 1,
                    "level": 1,
                    "score": 1,
                    "elapsed_seconds": 2.0,
                    "created_at": T0,
                },
            ),
            SyncBatchChange(3, "quiz_attempts", "delete", "old-attempt", T1, {}),
            SyncBatchChange(4, "profiles", "delete", "old-profile", T1, {}),
        ]
        with (
            patch.object(sync_runner.sync_client, "sync_now", return_value=_status()),
            patch.object(
                sync_runner.sync_client,
                "sync_batch",
                return_value=_batch(cursor=4, changes=changes),
            ),
        ):
            result = sync_service.sync_now(self.parent.id)

        self.assertTrue(result.ok)
        self.assertEqual(result.applied_count, 3)
        self.assertEqual(sync_state.load_sync_state().server_cursor, 4)


if __name__ == "__main__":
    unittest.main()
