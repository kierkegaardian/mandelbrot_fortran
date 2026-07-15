from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
import unittest
from unittest.mock import patch

from app import db, sync_service
from app.db import quiz_completion
from tests.test_support import temporary_database

NOW = "2026-07-15T10:00:00+00:00"


class QuizCompletionAtomicTests(unittest.TestCase):
    @contextmanager
    def _completion_case(self) -> Iterator[tuple[int, int, int]]:
        with temporary_database():
            child = db.create_profile("Atomic Child", "child", NOW)
            assignment_id = db.create_assignment(
                profile_id=child.id,
                skill="fractions",
                subskill=None,
                target_type="quiz_score_pct",
                target_value=100.0,
                level=1,
                num_questions=2,
                question_type="typed",
                mode_intuition_pct=None,
                mode_expression_pct=None,
                mode_word_pct=None,
                notes="Atomic completion",
                created_at=NOW,
            )
            resume_id = db.save_quiz_progress(
                child.id, None, 1, '{"version":1,"status":"in_progress"}', NOW
            )
            yield child.id, assignment_id, resume_id

    def _record(self, profile_id: int) -> sync_service.RecordCompletedQuizResult:
        questions = (
            sync_service.QuestionResultInput(
                skill="fractions",
                subskill="Add unlike denominators",
                question_label="Core",
                mode="expression",
                prompt="1/2 + 1/4",
                correct_answer="3/4",
                user_answer="3/4",
                is_correct=True,
                explanation="Use fourths.",
            ),
            sync_service.QuestionResultInput(
                skill="fractions",
                subskill="Add unlike denominators",
                question_label="Review",
                mode="word",
                prompt="Add one half and one quarter.",
                correct_answer="3/4",
                user_answer="3/4",
                is_correct=True,
                explanation="Use a common denominator.",
            ),
        )
        return sync_service.record_completed_quiz(
            profile_id=profile_id,
            quiz_set_id=None,
            skill="fractions",
            question_type="typed",
            num_questions=2,
            level=1,
            score=2,
            created_at=NOW,
            elapsed_seconds=12.5,
            question_results=questions,
            record_progress=True,
            streak_to_master=2,
            record_daily_review=True,
        )

    def _assert_rolled_back(
        self, profile_id: int, assignment_id: int, resume_id: int
    ) -> None:
        self.assertEqual([], db.list_attempts(profile_id))
        self.assertEqual([], db.list_subskill_progress(profile_id))
        self.assertEqual([], db.list_daily_goal_history(profile_id))
        self.assertEqual(resume_id, db.load_quiz_progress(profile_id)[0])
        assignment = db.list_assignments(profile_id, active_only=True)[0]
        self.assertEqual(assignment_id, assignment.id)
        with db.managed_connection() as connection:
            self.assertEqual(
                0, connection.execute("SELECT COUNT(*) FROM quiz_questions").fetchone()[0]
            )
            self.assertEqual(
                0, connection.execute("SELECT COUNT(*) FROM sync_outbox").fetchone()[0]
            )

    def test_failure_injection_rolls_back_every_stage_and_preserves_resume(self) -> None:
        stages = (
            "_insert_attempt",
            "_insert_question_result",
            "_upsert_subskill_progress",
            "_evaluate_assignments",
            "_record_daily_goal",
        )
        for helper_name in stages:
            with self.subTest(stage=helper_name), self._completion_case() as case:
                profile_id, assignment_id, resume_id = case
                with patch.object(
                    quiz_completion, helper_name, side_effect=RuntimeError(helper_name)
                ):
                    with self.assertRaisesRegex(RuntimeError, helper_name):
                        self._record(profile_id)
                self._assert_rolled_back(profile_id, assignment_id, resume_id)

        with self.subTest(stage="late_outbox"), self._completion_case() as case:
            profile_id, assignment_id, resume_id = case
            original = quiz_completion._enqueue_outbox
            calls = 0

            def fail_late(*args, **kwargs):
                nonlocal calls
                calls += 1
                if calls == 3:
                    raise RuntimeError("late_outbox")
                return original(*args, **kwargs)

            with patch.object(quiz_completion, "_enqueue_outbox", side_effect=fail_late):
                with self.assertRaisesRegex(RuntimeError, "late_outbox"):
                    self._record(profile_id)
            self._assert_rolled_back(profile_id, assignment_id, resume_id)

    def test_success_is_atomic_idempotent_and_resume_clears_afterward(self) -> None:
        with self._completion_case() as case:
            profile_id, assignment_id, resume_id = case
            result = self._record(profile_id)
            self.assertEqual(1, result.completed_assignments)
            self.assertEqual(resume_id, db.load_quiz_progress(profile_id)[0])
            self.assertEqual(1, len(db.list_attempts(profile_id)))
            self.assertTrue(db.list_subskill_progress(profile_id)[0].mastered)
            self.assertEqual(1, db.list_daily_goal_history(profile_id)[0].completions)
            self.assertEqual(assignment_id, db.list_assignments(profile_id, False)[0].id)

            repeated = self._record(profile_id)
            self.assertEqual(result.attempt_id, repeated.attempt_id)
            self.assertEqual(1, len(db.list_attempts(profile_id)))
            self.assertEqual(1, db.list_daily_goal_history(profile_id)[0].completions)
            with db.managed_connection() as connection:
                self.assertEqual(
                    2,
                    connection.execute("SELECT COUNT(*) FROM quiz_questions").fetchone()[0],
                )
                self.assertEqual(
                    4,
                    connection.execute("SELECT COUNT(*) FROM sync_outbox").fetchone()[0],
                )

            db.clear_quiz_progress(resume_id)
            self.assertIsNone(db.load_quiz_progress(profile_id))


if __name__ == "__main__":
    unittest.main()
