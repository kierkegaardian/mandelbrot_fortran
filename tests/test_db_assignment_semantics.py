from __future__ import annotations

import tempfile
import unittest

from app import db


class DbAssignmentSemanticsTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self._orig_db_config = db.db_config
        tmp_path = self._tmp.name

        def _tmp_config() -> db.DbConfig:
            return db.DbConfig(path=f"{tmp_path}/test_app.db")

        db.db_config = _tmp_config
        db.init_db()
        profile = db.create_profile("Student", "child", "2026-02-18T00:00:00+00:00")
        self.profile_id = profile.id

    def tearDown(self) -> None:
        db.db_config = self._orig_db_config
        self._tmp.cleanup()

    def test_assignment_completion_requires_100_even_if_target_lower(self) -> None:
        assignment_id = db.create_assignment(
            profile_id=self.profile_id,
            skill="add_subtract",
            subskill=None,
            target_type="quiz_score_pct",
            target_value=80.0,
            level=1,
            num_questions=10,
            question_type="both",
            mode_intuition_pct=None,
            mode_expression_pct=None,
            mode_word_pct=None,
            notes="",
            created_at="2026-02-18T00:00:00+00:00",
        )
        attempt_90 = db.create_attempt(
            profile_id=self.profile_id,
            quiz_set_id=None,
            skill="add_subtract",
            question_type="both",
            num_questions=10,
            level=1,
            score=9,
            created_at="2026-02-18T01:00:00+00:00",
        )
        completed = db.evaluate_assignments_for_attempt(self.profile_id, attempt_90, "2026-02-18T01:10:00+00:00")
        self.assertEqual(completed, 0)
        active = db.list_assignments(self.profile_id, active_only=True)
        self.assertEqual(len(active), 1)
        self.assertEqual(active[0].id, assignment_id)

        attempt_100 = db.create_attempt(
            profile_id=self.profile_id,
            quiz_set_id=None,
            skill="add_subtract",
            question_type="both",
            num_questions=10,
            level=1,
            score=10,
            created_at="2026-02-18T02:00:00+00:00",
        )
        completed = db.evaluate_assignments_for_attempt(self.profile_id, attempt_100, "2026-02-18T02:10:00+00:00")
        self.assertEqual(completed, 1)
        self.assertEqual(len(db.list_assignments(self.profile_id, active_only=True)), 0)

    def test_mode_overrides_persist_for_quiz_set_and_assignment(self) -> None:
        qset = db.create_quiz_set(
            name="Mode Mix Quiz",
            skill="add_subtract",
            question_type="both",
            num_questions=8,
            level=1,
            created_at="2026-02-18T00:00:00+00:00",
            mode_intuition_pct=20,
            mode_expression_pct=50,
            mode_word_pct=30,
        )
        listed_qset = next(item for item in db.list_quiz_sets() if item.id == qset.id)
        self.assertEqual((listed_qset.mode_intuition_pct, listed_qset.mode_expression_pct, listed_qset.mode_word_pct), (20, 50, 30))

        assignment_id = db.create_assignment(
            profile_id=self.profile_id,
            skill="add_subtract",
            subskill=None,
            target_type="quiz_score_pct",
            target_value=100.0,
            level=1,
            num_questions=8,
            question_type="both",
            mode_intuition_pct=25,
            mode_expression_pct=45,
            mode_word_pct=30,
            notes="with mode override",
            created_at="2026-02-18T00:00:00+00:00",
        )
        listed_assignment = next(item for item in db.list_assignments(self.profile_id, active_only=True) if item.id == assignment_id)
        self.assertEqual(
            (
                listed_assignment.mode_intuition_pct,
                listed_assignment.mode_expression_pct,
                listed_assignment.mode_word_pct,
            ),
            (25, 45, 30),
        )

    def test_assignment_filters_and_analytics(self) -> None:
        first_id = db.create_assignment(
            profile_id=self.profile_id,
            skill="add_subtract",
            subskill=None,
            target_type="quiz_score_pct",
            target_value=100.0,
            level=1,
            num_questions=6,
            question_type="both",
            mode_intuition_pct=None,
            mode_expression_pct=None,
            mode_word_pct=None,
            notes="",
            created_at="2026-02-18T00:00:00+00:00",
        )
        second_id = db.create_assignment(
            profile_id=self.profile_id,
            skill="fractions",
            subskill="Equivalent fractions",
            target_type="subskill_mastered",
            target_value=1.0,
            level=1,
            num_questions=6,
            question_type="both",
            mode_intuition_pct=None,
            mode_expression_pct=None,
            mode_word_pct=None,
            notes="",
            created_at="2026-02-18T01:00:00+00:00",
        )
        db.set_assignment_active(first_id, False, completed_at="2026-02-20T00:00:00+00:00")
        done_filtered = db.list_assignments(
            self.profile_id,
            active_only=False,
            skill="add_subtract",
            target_type="quiz_score_pct",
            limit=1,
        )
        self.assertEqual(len(done_filtered), 1)
        self.assertEqual(done_filtered[0].id, first_id)

        active_filtered = db.list_assignments(self.profile_id, active_only=True, skill="fractions")
        self.assertEqual(len(active_filtered), 1)
        self.assertEqual(active_filtered[0].id, second_id)

        analytics = db.assignment_completion_analytics(self.profile_id, recent_days=30)
        self.assertEqual(int(analytics["active_count"]), 1)
        self.assertEqual(int(analytics["completed_count"]), 1)
        self.assertEqual(int(analytics["completed_recent_count"]), 1)
        self.assertTrue(float(analytics["avg_completion_hours"]) > 0.0)

    def test_daily_goal_history_streak(self) -> None:
        db.record_daily_review_completion(self.profile_id, "2026-02-16T08:00:00+00:00")
        db.record_daily_review_completion(self.profile_id, "2026-02-17T08:00:00+00:00")
        db.record_daily_review_completion(self.profile_id, "2026-02-18T08:00:00+00:00")
        db.record_daily_review_completion(self.profile_id, "2026-02-18T09:30:00+00:00")
        today_count, streak = db.daily_goal_status(self.profile_id, now_iso_text="2026-02-18T12:00:00+00:00")
        self.assertEqual(today_count, 2)
        self.assertEqual(streak, 3)

    def test_skill_progress_pipeline_combines_attempts_and_worksheets(self) -> None:
        db.create_attempt(
            profile_id=self.profile_id,
            quiz_set_id=None,
            skill="add_subtract",
            question_type="both",
            num_questions=8,
            level=1,
            score=7,
            created_at="2026-02-18T08:00:00+00:00",
            elapsed_seconds=80.0,
        )
        db.create_worksheet(
            profile_id=self.profile_id,
            quiz_set_id=None,
            skill="add_subtract",
            question_type="both",
            num_questions=8,
            level=1,
            file_path="/tmp/fake.pdf",
            created_at="2026-02-18T08:05:00+00:00",
        )
        pipeline = db.skill_progress_pipeline(self.profile_id)
        self.assertIn("add_subtract", pipeline)
        self.assertEqual(int(pipeline["add_subtract"]["attempts"]), 1)
        self.assertEqual(int(pipeline["add_subtract"]["worksheets"]), 1)
        self.assertEqual(int(pipeline["add_subtract"]["questions"]), 8)


if __name__ == "__main__":
    unittest.main()
