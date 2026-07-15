from __future__ import annotations

import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path

from app import sync_state


class SyncStateTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self._orig_data_dir = sync_state.data_dir
        self._root = Path(self._tmp.name)

        def _tmp_data_dir() -> Path:
            self._root.mkdir(parents=True, exist_ok=True)
            return self._root

        sync_state.data_dir = _tmp_data_dir

    def tearDown(self) -> None:
        sync_state.data_dir = self._orig_data_dir
        self._tmp.cleanup()

    def test_default_state_is_disabled(self) -> None:
        state = sync_state.load_sync_state()
        self.assertFalse(state.sync_enabled)
        self.assertIsNone(state.device_id)

    def test_enabling_sync_generates_device_id(self) -> None:
        enabled = sync_state.save_sync_enabled(True)
        self.assertTrue(enabled.sync_enabled)
        self.assertIsNotNone(enabled.device_id)

        loaded = sync_state.load_sync_state()
        self.assertEqual(loaded.device_id, enabled.device_id)
        self.assertTrue(loaded.sync_enabled)

    def test_disabling_sync_preserves_existing_device_identity(self) -> None:
        enabled = sync_state.save_sync_enabled(True)
        disabled = sync_state.save_sync_enabled(False)
        self.assertFalse(disabled.sync_enabled)
        self.assertEqual(disabled.device_id, enabled.device_id)

    def test_save_sync_probe_result_tracks_success_and_failure(self) -> None:
        sync_state.save_sync_enabled(True)
        failed = sync_state.save_sync_probe_result(
            succeeded=False,
            at_iso="2026-04-11T10:00:00+00:00",
            error_message="Server unreachable.",
        )
        self.assertEqual(failed.last_error, "Server unreachable.")
        self.assertIsNone(failed.last_sync_at)

        succeeded = sync_state.save_sync_probe_result(
            succeeded=True,
            at_iso="2026-04-11T10:05:00+00:00",
        )
        self.assertEqual(succeeded.last_sync_at, "2026-04-11T10:05:00+00:00")
        self.assertIsNone(succeeded.last_error)

    def test_state_write_is_atomic_and_owner_only(self) -> None:
        enabled = sync_state.save_sync_enabled(True)
        path = self._root / "sync_state.json"
        self.assertEqual(0o600, path.stat().st_mode & 0o777)
        original = path.read_text(encoding="utf-8")

        with patch("app.sync_state.os.replace", side_effect=OSError("locked")):
            with self.assertRaises(sync_state.SyncStateWriteError):
                sync_state.save_sync_enabled(False)

        self.assertEqual(original, path.read_text(encoding="utf-8"))
        self.assertTrue(sync_state.load_sync_state().sync_enabled)
        self.assertTrue(enabled.sync_enabled)

    def test_direct_cursor_save_rejects_rewind(self) -> None:
        sync_state.save_sync_server_cursor(10)

        with self.assertRaisesRegex(ValueError, "backward"):
            sync_state.save_sync_server_cursor(9)

        self.assertEqual(sync_state.load_sync_state().server_cursor, 10)


if __name__ == "__main__":
    unittest.main()
