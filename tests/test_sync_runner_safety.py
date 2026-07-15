from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app import db, sync_runner, sync_service, sync_state, sync_store
from app.sync_client import (
    FamilyLinkResult,
    SyncBatchChange,
    SyncBatchResult,
    SyncEndpointResult,
    SyncStatus,
)


T0 = "2026-04-11T10:00:00+00:00"


class SyncRunnerSafetyTests(unittest.TestCase):
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

    def tearDown(self) -> None:
        sync_state.data_dir = self._old_data_dir
        self._tmp.cleanup()

    def test_disabled_sync_never_probes_network(self) -> None:
        with patch.object(sync_runner.sync_client, "sync_now") as probe:
            result = sync_runner.sync_now()

        probe.assert_not_called()
        self.assertFalse(result.attempted)
        self.assertFalse(result.enabled)

    def test_only_distinct_acknowledged_sent_ids_are_marked(self) -> None:
        self._enable_and_pair()
        sync_service.create_profile("First", "child", T0)
        sync_service.create_profile("Second", "child", T0)
        pending = sync_store.list_pending_changes()
        accepted = pending[0].id
        batch = _batch(cursor=4, accepted=[accepted, accepted, 999_999])

        with (
            patch.object(sync_runner.sync_client, "sync_now", return_value=_status()),
            patch.object(sync_runner.sync_client, "sync_batch", return_value=batch),
        ):
            result = sync_runner.sync_now(self.parent.id)

        self.assertTrue(result.ok)
        self.assertEqual(result.uploaded_count, 1)
        self.assertEqual(sync_store.count_pending_changes(), 1)
        self.assertEqual(sync_store.list_pending_changes()[0].id, pending[1].id)

    def test_deferred_supported_change_retains_cursor_until_retry(self) -> None:
        self._enable_and_pair(cursor=3)
        missing_dependency = _remote_assignment("assignment-1", "profile-1")
        deferred_batch = _batch(cursor=9, changes=[missing_dependency])

        with (
            patch.object(sync_runner.sync_client, "sync_now", return_value=_status()),
            patch.object(
                sync_runner.sync_client, "sync_batch", return_value=deferred_batch
            ),
        ):
            first = sync_runner.sync_now(self.parent.id)

        self.assertFalse(first.ok)
        self.assertIn("deferred", first.message)
        self.assertEqual(sync_state.load_sync_state().server_cursor, 3)
        self.assertEqual([item.name for item in db.list_profiles()], ["Parent"])

        retry_batch = _batch(
            cursor=9,
            changes=[missing_dependency, _remote_profile("profile-1")],
        )
        with (
            patch.object(sync_runner.sync_client, "sync_now", return_value=_status()),
            patch.object(sync_runner.sync_client, "sync_batch", return_value=retry_batch),
        ):
            retry = sync_runner.sync_now(self.parent.id)

        self.assertTrue(retry.ok)
        self.assertEqual(retry.applied_count, 2)
        self.assertEqual(sync_state.load_sync_state().server_cursor, 9)

    def test_unsupported_remote_change_is_counted_but_does_not_pin_cursor(self) -> None:
        self._enable_and_pair(cursor=2)
        future = SyncBatchChange(7, "future_entity", "upsert", "future-1", T0, {})
        with (
            patch.object(sync_runner.sync_client, "sync_now", return_value=_status()),
            patch.object(
                sync_runner.sync_client,
                "sync_batch",
                return_value=_batch(cursor=7, changes=[future]),
            ),
        ):
            result = sync_runner.sync_now(self.parent.id)

        self.assertTrue(result.ok)
        self.assertIn("1 unsupported", result.message)
        self.assertEqual(sync_state.load_sync_state().server_cursor, 7)

    def test_pairing_state_failure_is_reported_without_claiming_success(self) -> None:
        sync_state.save_sync_enabled(True)
        with (
            patch.object(
                sync_runner.sync_client,
                "bootstrap_family",
                return_value=_family_link(),
            ),
            patch.object(
                sync_runner.sync_state,
                "save_sync_pairing",
                side_effect=sync_state.SyncStateWriteError("state write failed"),
            ),
        ):
            result = sync_runner.start_family_sync(self.parent.id)

        self.assertFalse(result.ok)
        self.assertIn("state write failed", result.message)
        self.assertIsNone(sync_state.load_sync_state().family_id)

    def test_success_state_failure_keeps_prior_cursor_and_surfaces_error(self) -> None:
        self._enable_and_pair(cursor=3)
        with (
            patch.object(sync_runner.sync_client, "sync_now", return_value=_status()),
            patch.object(
                sync_runner.sync_client,
                "sync_batch",
                return_value=_batch(cursor=9),
            ),
            patch.object(
                sync_runner.sync_state,
                "save_sync_success",
                side_effect=sync_state.SyncStateWriteError("state replace failed"),
            ),
        ):
            result = sync_runner.sync_now(self.parent.id)

        self.assertFalse(result.ok)
        self.assertIn("state replace failed", result.message)
        self.assertEqual(sync_state.load_sync_state().server_cursor, 3)

    def _enable_and_pair(self, *, cursor: int = 0) -> None:
        sync_state.save_sync_enabled(True)
        sync_state.save_sync_pairing(
            family_id="family-1", pairing_token="pair-123", server_cursor=cursor
        )


def _endpoint() -> SyncEndpointResult:
    return SyncEndpointResult(True, "http://localhost", 200, {}, "{}", None, None)


def _status() -> SyncStatus:
    endpoint = _endpoint()
    return SyncStatus(
        ok=True,
        config_available=True,
        server_base_url="http://localhost",
        server_label="Test",
        profile="test",
        config_source="test-config",
        config_path="/tmp/test.json",
        health=endpoint,
        api_root=endpoint,
        error_code=None,
        error_message=None,
    )


def _family_link() -> FamilyLinkResult:
    return FamilyLinkResult(
        True, "family-1", "pair-123", None, None, _endpoint()
    )


def _batch(
    *,
    cursor: int,
    accepted: list[int] | None = None,
    changes: list[SyncBatchChange] | None = None,
) -> SyncBatchResult:
    return SyncBatchResult(
        True,
        cursor,
        accepted or [],
        changes or [],
        None,
        None,
        _endpoint(),
    )


def _remote_profile(sync_id: str) -> SyncBatchChange:
    return SyncBatchChange(
        8,
        "profiles",
        "upsert",
        sync_id,
        T0,
        {"name": "Remote child", "role": "child", "created_at": T0},
    )


def _remote_assignment(sync_id: str, profile_sync_id: str) -> SyncBatchChange:
    return SyncBatchChange(
        9,
        "assignments",
        "upsert",
        sync_id,
        T0,
        {
            "profile_sync_id": profile_sync_id,
            "skill": "counting",
            "subskill": None,
            "target_type": "quiz_score_pct",
            "target_value": 80,
            "level": 1,
            "num_questions": 5,
            "question_type": "typed",
            "active": True,
            "notes": "",
            "created_at": T0,
        },
    )


if __name__ == "__main__":
    unittest.main()
