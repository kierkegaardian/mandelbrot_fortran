from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from app import db, sync_service, sync_state, sync_store
from app.sync_client import FamilyLinkResult, SyncBatchChange, SyncBatchResult, SyncEndpointResult, SyncStatus


class SyncServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self._orig_data_dir = sync_state.data_dir
        tmp_root = Path(self._tmp.name)

        def _tmp_config() -> db.DbConfig:
            return db.DbConfig(path=str(tmp_root / "test_app.db"))

        def _tmp_data_dir() -> Path:
            data_root = tmp_root / "data"
            data_root.mkdir(parents=True, exist_ok=True)
            return data_root

        self.enterContext(db.override_db_config(_tmp_config))
        sync_state.data_dir = _tmp_data_dir
        db.init_db()

    def tearDown(self) -> None:
        sync_state.data_dir = self._orig_data_dir
        self._tmp.cleanup()

    def test_record_completed_quiz_enqueues_attempt_questions_and_assignment_update(self) -> None:
        child = db.create_profile("Child", "child", "2026-04-11T10:00:00+00:00")
        assignment_id = db.create_assignment(
            profile_id=child.id,
            skill="counting",
            subskill=None,
            target_type="quiz_score_pct",
            target_value=100,
            level=1,
            num_questions=2,
            question_type="typed",
            mode_intuition_pct=None,
            mode_expression_pct=None,
            mode_word_pct=None,
            notes="Finish cleanly",
            created_at="2026-04-11T10:00:00+00:00",
        )

        result = sync_service.record_completed_quiz(
            profile_id=child.id,
            quiz_set_id=None,
            skill="counting",
            question_type="typed",
            num_questions=2,
            level=1,
            score=2,
            created_at="2026-04-11T10:05:00+00:00",
            elapsed_seconds=12.5,
            question_results=[
                sync_service.QuestionResultInput(
                    skill="counting",
                    subskill="Count to 10",
                    question_label="Core",
                    mode="expression",
                    prompt="1 + 1",
                    correct_answer="2",
                    user_answer="2",
                    is_correct=True,
                    explanation="Two.",
                ),
                sync_service.QuestionResultInput(
                    skill="counting",
                    subskill="Count to 10",
                    question_label="Core",
                    mode="expression",
                    prompt="2 + 2",
                    correct_answer="4",
                    user_answer="4",
                    is_correct=True,
                    explanation="Four.",
                ),
            ],
            record_progress=True,
            streak_to_master=3,
            record_daily_review=False,
        )

        self.assertEqual(result.completed_assignments, 1)
        pending = sync_store.list_pending_changes(limit=10)
        self.assertEqual([entry.entity_type for entry in pending], ["quiz_attempts", "quiz_questions", "quiz_questions", "assignments"])
        completed_items = db.list_assignments(child.id, active_only=False)
        self.assertEqual(len(completed_items), 1)
        self.assertEqual(completed_items[0].id, assignment_id)
        attempts = db.list_attempts(child.id)
        self.assertEqual(len(attempts), 1)
        self.assertEqual(attempts[0].id, result.attempt_id)

    def test_sync_now_handles_disabled_and_success_states(self) -> None:
        disabled = sync_service.sync_now()
        self.assertFalse(disabled.attempted)
        self.assertFalse(disabled.enabled)

        sync_state.save_sync_enabled(True)
        parent = db.create_profile("Parent", "parent", "2026-04-11T09:59:00+00:00")
        profile = sync_service.create_profile("Sam", "child", "2026-04-11T10:00:00+00:00")
        original_sync_now = sync_service.sync_client.sync_now
        original_bootstrap = sync_service.sync_client.bootstrap_family
        original_sync_batch = sync_service.sync_client.sync_batch
        try:
            sync_service.sync_client.sync_now = lambda: _success_status()
            sync_service.sync_client.bootstrap_family = lambda **_kwargs: _success_family_link()
            sync_service.sync_client.sync_batch = lambda **_kwargs: _success_batch_result(_kwargs["changes"][0]["client_change_id"])
            paired = sync_service.start_family_sync(parent.id)
            self.assertTrue(paired.ok)
            result = sync_service.sync_now(parent.id)
        finally:
            sync_service.sync_client.sync_now = original_sync_now
            sync_service.sync_client.bootstrap_family = original_bootstrap
            sync_service.sync_client.sync_batch = original_sync_batch

        self.assertTrue(result.attempted)
        self.assertTrue(result.ok)
        self.assertEqual(result.uploaded_count, 1)
        self.assertEqual(result.applied_count, 1)
        state = sync_state.load_sync_state()
        self.assertEqual(state.family_id, "home-lan")
        self.assertEqual(state.pairing_token, "pair-123")
        self.assertEqual(state.server_cursor, 9)
        self.assertIsNotNone(state.last_sync_at)
        self.assertIsNone(state.last_error)
        self.assertEqual(sync_store.count_pending_changes(), 0)
        synced_profiles = sync_service.list_profiles()
        self.assertEqual(len(synced_profiles), 3)
        self.assertTrue(any(item.id == profile.id for item in synced_profiles))

    def test_delete_profile_enqueues_dependent_delete_changes(self) -> None:
        child = sync_service.create_profile("Child", "child", "2026-04-11T10:00:00+00:00")
        sync_store.mark_changes_synced([entry.id for entry in sync_store.list_pending_changes()], "2026-04-11T10:01:00+00:00")
        sync_service.record_completed_quiz(
            profile_id=child.id,
            quiz_set_id=None,
            skill="counting",
            question_type="typed",
            num_questions=1,
            level=1,
            score=1,
            created_at="2026-04-11T10:02:00+00:00",
            elapsed_seconds=5.0,
            question_results=[
                sync_service.QuestionResultInput(
                    skill="counting",
                    subskill="Count to 10",
                    question_label="Core",
                    mode="expression",
                    prompt="1 + 0",
                    correct_answer="1",
                    user_answer="1",
                    is_correct=True,
                    explanation="One.",
                )
            ],
            record_progress=True,
            streak_to_master=3,
            record_daily_review=False,
        )
        sync_store.mark_changes_synced([entry.id for entry in sync_store.list_pending_changes()], "2026-04-11T10:03:00+00:00")

        sync_service.delete_profile(child.id, "2026-04-11T10:04:00+00:00")
        pending = sync_store.list_pending_changes(limit=10)
        self.assertEqual(
            [entry.entity_type for entry in pending],
            ["quiz_questions", "quiz_attempts", "profiles"],
        )
        self.assertTrue(all(entry.action == "delete" for entry in pending))


def _success_status() -> SyncStatus:
    health = SyncEndpointResult(
        ok=True,
        url="http://127.0.0.1:8091/health",
        status_code=200,
        data={"status": "ok"},
        raw_text='{"status":"ok"}',
        error_code=None,
        error_message=None,
    )
    api_root = SyncEndpointResult(
        ok=True,
        url="http://127.0.0.1:8091/api/v1",
        status_code=200,
        data={"capabilities": ["discover"]},
        raw_text='{"capabilities":["discover"]}',
        error_code=None,
        error_message=None,
    )
    return SyncStatus(
        ok=True,
        config_available=True,
        server_base_url="http://127.0.0.1:8091",
        server_label="Home sync server",
        profile="home-lan",
        config_source="override",
        config_path="/tmp/sync.internal.json",
        health=health,
        api_root=api_root,
        error_code=None,
        error_message=None,
    )


def _success_family_link() -> FamilyLinkResult:
    response = SyncEndpointResult(
        ok=True,
        url="http://127.0.0.1:8091/api/v1/family/bootstrap",
        status_code=200,
        data={"family_id": "home-lan", "pairing_token": "pair-123"},
        raw_text='{"family_id":"home-lan","pairing_token":"pair-123"}',
        error_code=None,
        error_message=None,
    )
    return FamilyLinkResult(
        ok=True,
        family_id="home-lan",
        pairing_token="pair-123",
        error_code=None,
        error_message=None,
        response=response,
    )


def _success_batch_result(client_change_id: int) -> SyncBatchResult:
    response = SyncEndpointResult(
        ok=True,
        url="http://127.0.0.1:8091/api/v1/sync",
        status_code=200,
        data={},
        raw_text="{}",
        error_code=None,
        error_message=None,
    )
    return SyncBatchResult(
        ok=True,
        server_cursor=9,
        accepted_client_change_ids=[int(client_change_id)],
        changes=[
            SyncBatchChange(
                server_change_id=9,
                entity_type="profiles",
                action="upsert",
                entity_sync_id="remote-profile-sync-1",
                updated_at="2026-04-11T10:05:00+00:00",
                data={
                    "name": "Remote child",
                    "role": "child",
                    "created_at": "2026-04-11T10:05:00+00:00",
                },
            )
        ],
        error_code=None,
        error_message=None,
        response=response,
    )


if __name__ == "__main__":
    unittest.main()
