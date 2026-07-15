from __future__ import annotations

import tempfile
import unittest

from app import db, sync_apply, sync_service, sync_store


T0 = "2026-04-11T10:00:00+00:00"


class SyncApplySafetyTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.enterContext(
            db.override_db_config(db.DbConfig(path=f"{self._tmp.name}/app.db"))
        )
        db.init_db()

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_dependencies_are_ordered_even_when_input_is_not(self) -> None:
        result = sync_apply.apply_remote_changes(
            [
                _assignment_change("assignment-1", "profile-1"),
                _profile_change("profile-1", name="Remote child"),
            ]
        )

        self.assertEqual(result.applied, 2)
        profiles = db.list_profiles()
        self.assertEqual([item.name for item in profiles], ["Remote child"])
        self.assertEqual(len(db.list_assignments(profiles[0].id)), 1)

    def test_missing_dependency_defers_and_rolls_back_entire_batch(self) -> None:
        result = sync_apply.apply_remote_changes(
            [
                _profile_change("profile-rollback", name="Must roll back"),
                _assignment_change("assignment-1", "missing-profile"),
            ]
        )

        self.assertEqual(result.applied, 0)
        self.assertEqual(result.deferred, 1)
        self.assertEqual(db.list_profiles(), [])
        self._assert_foreign_keys_clean()

    def test_invalid_supported_change_rolls_back_prior_apply(self) -> None:
        invalid = _profile_change("profile-invalid", name="")
        with self.assertRaisesRegex(ValueError, "Missing required sync field"):
            sync_apply.apply_remote_changes(
                [_profile_change("profile-valid", name="Must roll back"), invalid]
            )

        self.assertEqual(db.list_profiles(), [])

    def test_delete_comparison_uses_timestamp_instants_not_text(self) -> None:
        sync_apply.apply_remote_changes(
            [
                _profile_change(
                    "profile-offset",
                    name="Offset child",
                    updated_at="2026-04-11T03:00:00-10:00",
                )
            ]
        )
        stale = sync_apply.apply_remote_changes(
            [_delete_change("profiles", "profile-offset", "2026-04-11T12:00:00+00:00")]
        )
        self.assertEqual(stale.stale_skipped, 1)
        self.assertEqual(len(db.list_profiles()), 1)

        applied = sync_apply.apply_remote_changes(
            [_delete_change("profiles", "profile-offset", "2026-04-11T14:00:00+00:00")]
        )
        self.assertEqual(applied.applied, 1)
        self.assertEqual(db.list_profiles(), [])

    def test_remote_soft_delete_preserves_local_only_pin_and_resume(self) -> None:
        parent = sync_service.create_profile("Parent", "parent", T0)
        child = sync_service.create_profile("Child", "child", T0)
        db.set_parent_pin(parent.id, "1234", T0)
        resume_id = db.save_quiz_progress(child.id, None, 2, '{"pending":true}', T0)
        parent_sync_id = sync_store.entity_sync_id("profiles", parent.id)
        child_sync_id = sync_store.entity_sync_id("profiles", child.id)

        result = sync_apply.apply_remote_changes(
            [
                _delete_change("profiles", str(parent_sync_id), "2026-04-11T11:00:00+00:00"),
                _delete_change("profiles", str(child_sync_id), "2026-04-11T11:00:00+00:00"),
            ]
        )

        self.assertEqual(result.applied, 2)
        self.assertEqual(db.list_profiles(), [])
        self.assertTrue(db.parent_pin_configured())
        self.assertEqual(db.parent_pin_owner_id(), parent.id)
        self.assertEqual(db.load_quiz_progress(child.id), (resume_id, 2, '{"pending":true}'))
        self._assert_foreign_keys_clean()

    def test_delete_batch_hides_attempt_graph_without_fk_deletion(self) -> None:
        sync_apply.apply_remote_changes(
            [
                _profile_change("profile-1"),
                _attempt_change("attempt-1", "profile-1"),
                _question_change("question-1", "attempt-1"),
            ]
        )
        profile = db.list_profiles()[0]
        self.assertEqual(len(db.list_attempts(profile.id)), 1)

        result = sync_apply.apply_remote_changes(
            [
                _delete_change("profiles", "profile-1", "2026-04-11T11:00:00+00:00"),
                _delete_change("quiz_attempts", "attempt-1", "2026-04-11T11:00:00+00:00"),
                _delete_change("quiz_questions", "question-1", "2026-04-11T11:00:00+00:00"),
            ]
        )

        self.assertEqual(result.applied, 3)
        self.assertEqual(db.list_profiles(), [])
        self.assertEqual(db.list_attempts(profile.id), [])
        self._assert_foreign_keys_clean()

    def _assert_foreign_keys_clean(self) -> None:
        with db.managed_connection() as conn:
            self.assertEqual(conn.execute("PRAGMA foreign_key_check").fetchall(), [])


def _change(entity: str, sync_id: str, data: dict[str, object], updated_at: str = T0):
    return {
        "entity_type": entity,
        "action": "upsert",
        "entity_sync_id": sync_id,
        "updated_at": updated_at,
        "payload": data,
    }


def _profile_change(sync_id: str, *, name: str = "Child", updated_at: str = T0):
    return _change(
        "profiles",
        sync_id,
        {"name": name, "role": "child", "created_at": T0},
        updated_at,
    )


def _assignment_change(sync_id: str, profile_sync_id: str):
    return _change(
        "assignments",
        sync_id,
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


def _attempt_change(sync_id: str, profile_sync_id: str):
    return _change(
        "quiz_attempts",
        sync_id,
        {
            "profile_sync_id": profile_sync_id,
            "quiz_set_sync_id": None,
            "skill": "counting",
            "question_type": "typed",
            "num_questions": 1,
            "level": 1,
            "score": 1,
            "elapsed_seconds": 2.0,
            "created_at": T0,
        },
    )


def _question_change(sync_id: str, attempt_sync_id: str):
    return _change(
        "quiz_questions",
        sync_id,
        {
            "attempt_sync_id": attempt_sync_id,
            "skill": "counting",
            "subskill": "Count to 10",
            "question_label": "Core",
            "mode": "expression",
            "prompt": "1 + 0",
            "correct_answer": "1",
            "user_answer": "1",
            "is_correct": True,
            "explanation": "One.",
        },
    )


def _delete_change(entity: str, sync_id: str, updated_at: str):
    return {
        "entity_type": entity,
        "action": "delete",
        "entity_sync_id": sync_id,
        "updated_at": updated_at,
        "payload": {},
    }


if __name__ == "__main__":
    unittest.main()
