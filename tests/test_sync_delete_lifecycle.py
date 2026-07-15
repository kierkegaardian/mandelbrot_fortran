from __future__ import annotations

import tempfile
import unittest

from app import db, sync_payloads, sync_service, sync_store


T0 = "2026-04-11T10:00:00+00:00"
T1 = "2026-04-11T11:00:00+00:00"


class SyncDeleteLifecycleTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.enterContext(
            db.override_db_config(db.DbConfig(path=f"{self._tmp.name}/app.db"))
        )
        db.init_db()

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_delete_supersedes_unsent_graph_upserts_without_poison_rows(self) -> None:
        child = sync_service.create_profile("Child", "child", T0)
        resume_id = db.save_quiz_progress(child.id, None, 1, '{"pending":true}', T0)
        sync_service.record_completed_quiz(
            profile_id=child.id,
            quiz_set_id=None,
            skill="counting",
            question_type="typed",
            num_questions=1,
            level=1,
            score=1,
            created_at=T0,
            elapsed_seconds=2.0,
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
        self.assertEqual(
            [item.action for item in sync_store.list_pending_changes()],
            ["upsert", "upsert", "upsert"],
        )

        sync_service.delete_profile(child.id, T1)

        pending = sync_store.list_pending_changes()
        self.assertEqual(
            [item.entity_type for item in pending],
            ["quiz_questions", "quiz_attempts", "profiles"],
        )
        self.assertTrue(all(item.action == "delete" for item in pending))
        self.assertTrue(
            all(sync_payloads.build_outbound_change(item) for item in pending)
        )
        self.assertEqual(db.list_profiles(), [])
        self.assertEqual(
            db.load_quiz_progress(child.id),
            (resume_id, 1, '{"pending":true}'),
        )
        with db.managed_connection() as conn:
            deleted = conn.execute(
                """SELECT
                (SELECT sync_deleted FROM profiles WHERE id = ?) AS profile_deleted,
                (SELECT sync_deleted FROM quiz_attempts LIMIT 1) AS attempt_deleted,
                (SELECT sync_deleted FROM quiz_questions LIMIT 1) AS question_deleted""",
                (child.id,),
            ).fetchone()
            self.assertEqual(conn.execute("PRAGMA foreign_key_check").fetchall(), [])
        self.assertEqual(
            tuple(int(deleted[key]) for key in deleted.keys()),
            (1, 1, 1),
        )

    def test_unsent_quiz_set_create_is_replaced_by_one_delete(self) -> None:
        quiz_set = sync_service.create_quiz_set(
            "Quick set", "counting", "typed", 5, 1, T0
        )
        self.assertEqual(sync_store.count_pending_changes(), 1)

        sync_service.delete_quiz_set(quiz_set.id, T1)

        pending = sync_store.list_pending_changes()
        self.assertEqual(len(pending), 1)
        self.assertEqual(pending[0].entity_type, "quiz_sets")
        self.assertEqual(pending[0].action, "delete")
        self.assertIsNotNone(sync_payloads.build_outbound_change(pending[0]))
        self.assertEqual(db.list_quiz_sets(), [])


if __name__ == "__main__":
    unittest.main()
