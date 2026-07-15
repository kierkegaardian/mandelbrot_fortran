from __future__ import annotations

import unittest

from app import db
from tests.test_support import temporary_database


NOW = "2026-07-15T00:00:00+00:00"


class DbPersistenceContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.enterContext(temporary_database())
        self.parent = db.create_profile("Parent", "parent", NOW)
        self.child = db.create_profile("Child", "child", NOW)

    def test_parent_pin_roundtrip_bounds_and_lockout(self) -> None:
        for invalid in ("123", "1234567890123", "12ab"):
            with self.subTest(pin=invalid):
                with self.assertRaises(ValueError):
                    db.set_parent_pin(self.parent.id, invalid, NOW)
        with self.assertRaises(ValueError):
            db.set_parent_pin(self.child.id, "1234", NOW)

        db.set_parent_pin(self.parent.id, "1234", NOW)
        self.assertTrue(db.parent_pin_configured())
        for _ in range(2):
            self.assertFalse(db.verify_parent_pin("9999", "2026-07-15T00:00:04+00:00"))
            db.record_parent_auth_failure("2026-07-15T00:00:04+00:00")
        self.assertTrue(db.verify_parent_pin("1234", "2026-07-15T00:00:05+00:00"))
        with db.managed_connection() as connection:
            failed_attempts = connection.execute(
                "SELECT failed_attempts FROM parent_auth"
            ).fetchone()["failed_attempts"]
        self.assertEqual(0, int(failed_attempts))
        for attempt in range(db.PIN_LOCK_MAX_ATTEMPTS):
            self.assertFalse(db.verify_parent_pin("9999", "2026-07-15T00:01:00+00:00"))
            locked_until = db.record_parent_auth_failure(
                f"2026-07-15T00:01:{attempt:02d}+00:00"
            )
        self.assertIsNotNone(locked_until)
        self.assertTrue(db.parent_pin_locked("2026-07-15T00:02:00+00:00")[0])
        self.assertFalse(db.verify_parent_pin("1234", "2026-07-15T00:02:00+00:00"))
        self.assertEqual(
            locked_until,
            db.record_parent_auth_failure("2026-07-15T00:02:01+00:00"),
        )
        self.assertTrue(db.parent_pin_locked("2026-07-15T00:02:02+00:00")[0])

        db.clear_parent_lock("2026-07-15T00:03:00+00:00")
        self.assertFalse(db.parent_pin_locked("2026-07-15T00:03:01+00:00")[0])
        self.assertTrue(db.verify_parent_pin("1234", "2026-07-15T00:03:01+00:00"))

    def test_quiz_resume_and_credited_subskill_history(self) -> None:
        attempt_id = db.create_attempt(
            self.child.id,
            None,
            "fractions",
            "typed",
            1,
            2,
            1,
            NOW,
            8.0,
        )
        question_id = db.add_question_result_with_subskill(
            attempt_id=attempt_id,
            skill="fractions",
            subskill="Add unlike denominators",
            question_label="Core",
            mode="expression",
            prompt="1/2 + 1/4",
            correct_answer="3/4",
            user_answer="3/4",
            is_correct=True,
            explanation="Use fourths.",
            sync_updated_at=NOW,
        )
        resume_id = db.save_quiz_progress(
            self.child.id,
            None,
            1,
            '{"version":1,"question":1}',
            NOW,
        )
        self.assertEqual(
            (resume_id, 1, '{"version":1,"question":1}'),
            db.load_quiz_progress(self.child.id),
        )
        with self.assertRaisesRegex(ValueError, "not found"):
            db.save_quiz_progress(
                self.child.id,
                resume_id + 100,
                2,
                '{"version":1,"question":2}',
                NOW,
            )

        db.rebuild_subskill_progress(self.child.id, streak_to_master=1)
        progress = db.list_subskill_progress(self.child.id, "fractions")
        self.assertEqual(1, len(progress))
        self.assertEqual("Add unlike denominators", progress[0].subskill)
        self.assertTrue(progress[0].mastered)
        with db.managed_connection() as connection:
            row = connection.execute(
                "SELECT subskill FROM quiz_questions WHERE id = ?",
                (question_id,),
            ).fetchone()
        self.assertEqual("Add unlike denominators", str(row["subskill"]))

        db.clear_quiz_progress_for_profile(self.child.id)
        self.assertIsNone(db.load_quiz_progress(self.child.id))

    def test_school_year_summer_and_worksheet_records_are_local_contracts(self) -> None:
        target = db.save_school_year_target(self.child.id, 4, True, NOW)
        self.assertEqual(target, db.get_school_year_target(self.child.id))
        with self.assertRaises(ValueError):
            db.save_school_year_target(self.parent.id, 4, True, NOW)
        with self.assertRaises(ValueError):
            db.save_school_year_target(self.child.id, 8, True, NOW)

        program = db.create_summer_program(
            profile_id=self.child.id,
            lane="grade_4",
            start_date="2026-06-01",
            end_date="2026-08-01",
            days_per_week=4,
            minutes_per_session=30,
            status="active",
            finish_definition="Complete every required task.",
            placement_recommendation="grade_4",
            placement_review_status="accepted",
            placement_reviewed_at=NOW,
            student_age_years=10,
            created_at=NOW,
            updated_at=NOW,
        )
        task = db.create_summer_program_task(
            program_id=program.id,
            unit_code="unit-1",
            task_kind="quiz",
            skill="fractions",
            subskill="Add unlike denominators",
            sequence_index=1,
            status="pending",
            target_score_pct=80.0,
            scheduled_date="2026-06-02",
        )
        db.update_summer_program_task(task.id, status="completed")
        self.assertEqual("completed", db.get_summer_program_task(task.id).status)
        assessment = db.record_summer_assessment(
            program_id=program.id,
            assessment_type="placement",
            score_pct=85.0,
            passed=True,
            strand_results_json='{"fractions":85}',
            completed_at=NOW,
        )
        self.assertEqual([assessment], db.list_summer_assessment_runs(program.id))

        worksheet = db.create_worksheet(
            self.child.id,
            None,
            "texas_grade_4",
            "typed",
            10,
            4,
            "/tmp/packet.pdf",
            NOW,
        )
        self.assertEqual([worksheet], db.list_worksheets(self.child.id))
        self.assertTrue(
            db.archive_worksheet(
                worksheet.id,
                profile_id=self.child.id,
                archived_at="2026-07-16T00:00:00+00:00",
            )
        )
        self.assertEqual([], db.list_worksheets(self.child.id))
        archived = db.list_worksheets(self.child.id, include_archived=True)
        self.assertEqual("2026-07-16T00:00:00+00:00", archived[0].archived_at)

        db.archive_summer_programs(self.child.id, archived_at="2026-08-02T00:00:00+00:00")
        self.assertIsNone(db.get_active_summer_program(self.child.id))
        self.assertEqual("archived", db.list_summer_programs(self.child.id, include_inactive=True)[0].status)


if __name__ == "__main__":
    unittest.main()
