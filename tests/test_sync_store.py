from __future__ import annotations

import tempfile
import unittest

from app import db, sync_service, sync_store


class SyncStoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        tmp_path = self._tmp.name

        def _tmp_config() -> db.DbConfig:
            return db.DbConfig(path=f"{tmp_path}/test_app.db")

        self.enterContext(db.override_db_config(_tmp_config))
        db.init_db()

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_sync_ids_exist_for_raw_rows_after_init(self) -> None:
        profile = db.create_profile("Student", "child", "2026-04-11T10:00:00+00:00")
        sync_id = sync_store.entity_sync_id("profiles", profile.id)
        self.assertIsNotNone(sync_id)
        self.assertTrue(str(sync_id))

    def test_enqueue_and_mark_outbox_changes(self) -> None:
        profile = sync_service.create_profile("Student", "child", "2026-04-11T10:00:00+00:00")

        entries = sync_store.list_pending_changes()
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0].entity_type, "profiles")
        self.assertEqual(entries[0].action, "upsert")
        self.assertEqual(entries[0].payload["local_id"], profile.id)
        self.assertEqual(entries[0].payload["role"], "child")
        self.assertEqual(sync_store.count_pending_changes(), 1)

        sync_store.record_change_failure(entries[0].id, "2026-04-11T10:01:00+00:00", "busy")
        failed_entry = sync_store.list_pending_changes()[0]
        self.assertEqual(failed_entry.attempt_count, 1)
        self.assertEqual(failed_entry.last_error, "busy")

        sync_store.mark_changes_synced([failed_entry.id], "2026-04-11T10:02:00+00:00")
        self.assertEqual(sync_store.count_pending_changes(), 0)


if __name__ == "__main__":
    unittest.main()
