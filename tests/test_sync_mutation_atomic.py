from __future__ import annotations

import tempfile
import unittest
from unittest.mock import patch

from app import (
    db,
    sync_mutations_assignments,
    sync_mutations_profiles,
    sync_mutations_quiz_sets,
    sync_service,
    sync_store,
)


T0 = "2026-04-11T10:00:00+00:00"
T1 = "2026-04-11T11:00:00+00:00"


class SyncMutationAtomicTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.enterContext(
            db.override_db_config(db.DbConfig(path=f"{self._tmp.name}/app.db"))
        )
        db.init_db()

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_profile_create_rolls_back_when_outbox_insert_fails(self) -> None:
        with patch.object(
            sync_mutations_profiles,
            "enqueue_change_on",
            side_effect=RuntimeError("outbox failed"),
        ):
            with self.assertRaisesRegex(RuntimeError, "outbox failed"):
                sync_service.create_profile("Child", "child", T0)

        self.assertEqual(db.list_profiles(), [])
        self.assertEqual(sync_store.count_pending_changes(), 0)

    def test_profile_delete_rolls_back_when_outbox_insert_fails(self) -> None:
        child = db.create_profile("Child", "child", T0)
        with patch.object(
            sync_mutations_profiles,
            "soft_delete_entity_on",
            side_effect=RuntimeError("outbox failed"),
        ):
            with self.assertRaisesRegex(RuntimeError, "outbox failed"):
                sync_service.delete_profile(child.id, T1)

        self.assertEqual([item.id for item in db.list_profiles()], [child.id])
        self.assertEqual(sync_store.count_pending_changes(), 0)

    def test_quiz_set_update_rolls_back_when_outbox_insert_fails(self) -> None:
        quiz_set = db.create_quiz_set("Before", "counting", "typed", 5, 1, T0)
        with patch.object(
            sync_mutations_quiz_sets,
            "enqueue_change_on",
            side_effect=RuntimeError("outbox failed"),
        ):
            with self.assertRaisesRegex(RuntimeError, "outbox failed"):
                sync_service.update_quiz_set(
                    quiz_set.id,
                    "After",
                    "counting",
                    "typed",
                    5,
                    1,
                    updated_at=T1,
                )

        self.assertEqual(db.list_quiz_sets()[0].name, "Before")
        self.assertEqual(sync_store.count_pending_changes(), 0)

    def test_assignment_create_rolls_back_when_outbox_insert_fails(self) -> None:
        child = db.create_profile("Child", "child", T0)
        with patch.object(
            sync_mutations_assignments,
            "enqueue_change_on",
            side_effect=RuntimeError("outbox failed"),
        ):
            with self.assertRaisesRegex(RuntimeError, "outbox failed"):
                sync_service.create_assignment(
                    profile_id=child.id,
                    skill="counting",
                    subskill=None,
                    target_type="quiz_score_pct",
                    target_value=80,
                    level=1,
                    num_questions=5,
                    question_type="typed",
                    mode_intuition_pct=None,
                    mode_expression_pct=None,
                    mode_word_pct=None,
                    notes="",
                    created_at=T0,
                )

        self.assertEqual(db.list_assignments(child.id), [])
        self.assertEqual(sync_store.count_pending_changes(), 0)

    def test_assignment_completion_rolls_back_when_outbox_insert_fails(self) -> None:
        child = db.create_profile("Child", "child", T0)
        assignment_id = db.create_assignment(
            profile_id=child.id,
            skill="counting",
            subskill=None,
            target_type="quiz_score_pct",
            target_value=80,
            level=1,
            num_questions=5,
            question_type="typed",
            mode_intuition_pct=None,
            mode_expression_pct=None,
            mode_word_pct=None,
            notes="",
            created_at=T0,
        )
        with patch.object(
            sync_mutations_assignments,
            "enqueue_change_on",
            side_effect=RuntimeError("outbox failed"),
        ):
            with self.assertRaisesRegex(RuntimeError, "outbox failed"):
                sync_service.complete_assignment(assignment_id, T1)

        assignment = db.list_assignments(child.id)[0]
        self.assertTrue(assignment.active)
        self.assertIsNone(assignment.completed_at)
        self.assertEqual(sync_store.count_pending_changes(), 0)


if __name__ == "__main__":
    unittest.main()
