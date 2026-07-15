from __future__ import annotations

import tempfile
import unittest

from app import db, sync_apply


T0 = "2026-04-11T10:00:00+00:00"
T1 = "2026-04-11T11:00:00+00:00"


class SyncConflictTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.enterContext(
            db.override_db_config(db.DbConfig(path=f"{self._tmp.name}/app.db"))
        )
        db.init_db()

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_unknown_delete_tombstone_blocks_older_late_upsert(self) -> None:
        deleted = sync_apply.apply_remote_changes(
            [_delete("profiles", "ghost", T1)]
        )
        resurrected = sync_apply.apply_remote_changes(
            [_profile("ghost", "Too late", T0)]
        )

        self.assertEqual(deleted.applied, 1)
        self.assertEqual(resurrected.stale_skipped, 1)
        self.assertEqual(db.list_profiles(), [])
        with db.managed_connection() as conn:
            row = conn.execute(
                """SELECT deleted_at FROM sync_tombstones
                WHERE entity_type='profiles' AND entity_sync_id='ghost'"""
            ).fetchone()
        self.assertEqual(str(row["deleted_at"]), T1)

    def test_newer_upsert_can_explicitly_resurrect_tombstoned_entity(self) -> None:
        sync_apply.apply_remote_changes([_delete("profiles", "profile-1", T0)])
        result = sync_apply.apply_remote_changes(
            [_profile("profile-1", "Restored", T1)]
        )

        self.assertEqual(result.applied, 1)
        self.assertEqual([item.name for item in db.list_profiles()], ["Restored"])

    def test_soft_deleted_dependency_makes_child_upsert_stale(self) -> None:
        sync_apply.apply_remote_changes([_profile("profile-1", "Child", T0)])
        sync_apply.apply_remote_changes([_delete("profiles", "profile-1", T1)])
        result = sync_apply.apply_remote_changes(
            [_assignment("assignment-1", "profile-1", "2026-04-11T12:00:00+00:00")]
        )

        self.assertEqual(result.stale_skipped, 1)
        self.assertEqual(result.deferred, 0)
        with db.managed_connection() as conn:
            count = conn.execute("SELECT COUNT(*) AS count FROM assignments").fetchone()
        self.assertEqual(int(count["count"]), 0)

    def test_catch_up_lifecycle_with_later_deletes_does_not_defer(self) -> None:
        result = sync_apply.apply_remote_changes(
            [
                _profile("profile-1", "Old child", T0),
                _attempt("attempt-1", "profile-1", T0),
                _delete("quiz_attempts", "attempt-1", T1),
                _delete("profiles", "profile-1", T1),
            ]
        )

        self.assertEqual(result.deferred, 0)
        self.assertEqual(result.stale_skipped, 1)
        self.assertEqual(result.applied, 3)
        self.assertEqual(db.list_profiles(), [])

    def test_attempt_detaches_from_tombstoned_optional_quiz_set(self) -> None:
        sync_apply.apply_remote_changes(
            [
                _profile("profile-1", "Child", T0),
                _quiz_set("quiz-set-1", T0),
            ]
        )
        sync_apply.apply_remote_changes([_delete("quiz_sets", "quiz-set-1", T1)])

        result = sync_apply.apply_remote_changes(
            [_attempt("attempt-1", "profile-1", "2026-04-11T12:00:00+00:00", "quiz-set-1")]
        )

        self.assertEqual(result.applied, 1)
        with db.managed_connection() as conn:
            row = conn.execute(
                "SELECT quiz_set_id FROM quiz_attempts WHERE sync_id='attempt-1'"
            ).fetchone()
        self.assertIsNone(row["quiz_set_id"])

    def test_invalid_or_changed_remote_role_rolls_back(self) -> None:
        with self.assertRaisesRegex(ValueError, "role"):
            sync_apply.apply_remote_changes(
                [_profile("invalid-role", "Mallory", T0, role="admin")]
            )
        sync_apply.apply_remote_changes([_profile("profile-1", "Child", T0)])
        with self.assertRaisesRegex(ValueError, "role changes"):
            sync_apply.apply_remote_changes(
                [_profile("profile-1", "Child", T1, role="parent")]
            )

        profile = db.list_profiles()[0]
        self.assertEqual(profile.role, "child")
        self.assertEqual(len(db.list_profiles()), 1)

    def test_string_boolean_is_rejected_and_batch_rolls_back(self) -> None:
        with self.assertRaisesRegex(ValueError, "boolean"):
            sync_apply.apply_remote_changes(
                [
                    _profile("profile-1", "Must roll back", T0),
                    _assignment("assignment-1", "profile-1", T0, active="false"),
                ]
            )

        self.assertEqual(db.list_profiles(), [])

    def test_equal_timestamp_upsert_does_not_clobber_local_value(self) -> None:
        sync_apply.apply_remote_changes([_profile("profile-1", "First", T0)])
        result = sync_apply.apply_remote_changes(
            [_profile("profile-1", "Second", T0)]
        )

        self.assertEqual(result.stale_skipped, 1)
        self.assertEqual(db.list_profiles()[0].name, "First")


def _profile(
    sync_id: str, name: str, updated_at: str, *, role: str = "child"
) -> dict[str, object]:
    return {
        "entity_type": "profiles",
        "action": "upsert",
        "entity_sync_id": sync_id,
        "updated_at": updated_at,
        "payload": {"name": name, "role": role, "created_at": T0},
    }


def _assignment(
    sync_id: str,
    profile_sync_id: str,
    updated_at: str,
    *,
    active: object = True,
) -> dict[str, object]:
    return {
        "entity_type": "assignments",
        "action": "upsert",
        "entity_sync_id": sync_id,
        "updated_at": updated_at,
        "payload": {
            "profile_sync_id": profile_sync_id,
            "skill": "counting",
            "subskill": None,
            "target_type": "quiz_score_pct",
            "target_value": 80,
            "level": 1,
            "num_questions": 5,
            "question_type": "typed",
            "active": active,
            "notes": "",
            "created_at": T0,
        },
    }


def _attempt(
    sync_id: str,
    profile_sync_id: str,
    updated_at: str,
    quiz_set_sync_id: str | None = None,
):
    return {
        "entity_type": "quiz_attempts",
        "action": "upsert",
        "entity_sync_id": sync_id,
        "updated_at": updated_at,
        "payload": {
            "profile_sync_id": profile_sync_id,
            "quiz_set_sync_id": quiz_set_sync_id,
            "skill": "counting",
            "question_type": "typed",
            "num_questions": 1,
            "level": 1,
            "score": 1,
            "elapsed_seconds": 2.0,
            "created_at": T0,
        },
    }


def _quiz_set(sync_id: str, updated_at: str):
    return {
        "entity_type": "quiz_sets",
        "action": "upsert",
        "entity_sync_id": sync_id,
        "updated_at": updated_at,
        "payload": {
            "name": "Old set",
            "skill": "counting",
            "question_type": "typed",
            "num_questions": 5,
            "level": 1,
            "created_at": T0,
        },
    }


def _delete(entity_type: str, sync_id: str, updated_at: str) -> dict[str, object]:
    return {
        "entity_type": entity_type,
        "action": "delete",
        "entity_sync_id": sync_id,
        "updated_at": updated_at,
        "payload": {},
    }


if __name__ == "__main__":
    unittest.main()
