from __future__ import annotations

import os
import tempfile
import unittest

from pathlib import Path

from app import db, school_year, school_year_assessment


class SchoolYearTargetTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self._orig_data_dir = os.environ.get("MANDELQUEST_DATA_DIR")
        tmp_path = self._tmp.name
        os.environ["MANDELQUEST_DATA_DIR"] = tmp_path

        def _tmp_config() -> db.DbConfig:
            return db.DbConfig(path=f"{tmp_path}/test_app.db")

        self.enterContext(db.override_db_config(_tmp_config))
        db.init_db()
        now = "2026-06-26T00:00:00+00:00"
        self.child = db.create_profile("Student", "child", now)
        self.parent = db.create_profile("Parent", "parent", now)

    def tearDown(self) -> None:
        if self._orig_data_dir is None:
            os.environ.pop("MANDELQUEST_DATA_DIR", None)
        else:
            os.environ["MANDELQUEST_DATA_DIR"] = self._orig_data_dir
        self._tmp.cleanup()

    def test_school_year_target_persists_for_child_profile(self) -> None:
        target = db.save_school_year_target(
            self.child.id,
            4,
            True,
            "2026-06-26T01:00:00+00:00",
        )

        loaded = db.get_school_year_target(self.child.id)
        self.assertEqual(target, loaded)
        self.assertEqual(4, target.grade)
        self.assertTrue(target.stretch_enabled)

    def test_school_year_target_rejects_parent_and_unsupported_grade(self) -> None:
        with self.assertRaises(ValueError):
            db.save_school_year_target(
                self.parent.id,
                3,
                True,
                "2026-06-26T01:00:00+00:00",
            )

        with self.assertRaises(ValueError):
            db.save_school_year_target(
                self.child.id,
                8,
                True,
                "2026-06-26T01:00:00+00:00",
            )

    def test_status_derives_next_goal_from_mastered_subskills(self) -> None:
        db.save_school_year_target(
            self.child.id,
            1,
            True,
            "2026-06-26T01:00:00+00:00",
        )

        status = school_year.school_year_status(self.child.id)
        self.assertIsNotNone(status)
        assert status is not None
        self.assertEqual("g1_place_value", status.next_goal.code if status.next_goal else None)
        self.assertEqual(0, len(status.content_gaps))
        self.assertEqual(
            (
                "Ones, tens, and hundreds identification",
                "Compare numbers by place value",
            ),
            tuple(step.subskill for step in status.next_goal_steps),
        )
        self.assertFalse(any(step.mastered for step in status.next_goal_steps))

        for idx in range(3):
            db.upsert_subskill_progress(
                self.child.id,
                "place_value",
                "Ones, tens, and hundreds identification",
                True,
                f"2026-06-26T01:0{idx}:00+00:00",
                streak_to_master=3,
            )

        status = school_year.school_year_status(self.child.id)
        self.assertIsNotNone(status)
        assert status is not None
        self.assertEqual("g1_place_value", status.next_goal.code if status.next_goal else None)
        self.assertTrue(status.next_goal_steps[0].mastered)
        self.assertFalse(status.next_goal_steps[1].mastered)
        self.assertEqual(3, status.next_goal_steps[0].current_streak)
        self.assertEqual(0, status.completed_count)

        for idx in range(3):
            db.upsert_subskill_progress(
                self.child.id,
                "place_value",
                "Compare numbers by place value",
                True,
                f"2026-06-26T01:1{idx}:00+00:00",
                streak_to_master=3,
            )

        status = school_year.school_year_status(self.child.id)
        self.assertIsNotNone(status)
        assert status is not None
        self.assertEqual(1, status.completed_count)
        self.assertEqual("g1_add_subtract", status.next_goal.code if status.next_goal else None)

    def test_stretch_flag_controls_active_goal_count(self) -> None:
        db.save_school_year_target(
            self.child.id,
            5,
            False,
            "2026-06-26T01:00:00+00:00",
        )
        status = school_year.school_year_status(self.child.id)
        self.assertIsNotNone(status)
        assert status is not None
        self.assertFalse(any(goal.stretch for goal in status.active_goals))
        self.assertTrue(any(goal.code == "g5_personal_finance" for goal in status.active_goals))
        self.assertEqual(8, status.total_count)

        db.save_school_year_target(
            self.child.id,
            5,
            True,
            "2026-06-26T02:00:00+00:00",
        )
        status = school_year.school_year_status(self.child.id)
        self.assertIsNotNone(status)
        assert status is not None
        self.assertTrue(any(goal.stretch for goal in status.active_goals))
        self.assertEqual(9, status.total_count)

    def test_assessment_packet_generates_questions_and_answer_key(self) -> None:
        packet = school_year_assessment.generate_texas_grade_assessment(
            1,
            include_stretch=True,
            questions_per_subskill=1,
        )

        self.assertEqual(1, packet.grade)
        self.assertGreaterEqual(len(packet.items), 10)
        self.assertFalse(any("content gap" in note for note in packet.skipped))
        item_keys = {(item.goal.code, item.subskill) for item in packet.items}
        self.assertIn(("g1_shapes", "Compose 2D shapes"), item_keys)
        self.assertIn(("g1_data", "Picture and bar graphs"), item_keys)
        path = Path(packet.path)
        self.assertTrue(path.exists())
        html = path.read_text(encoding="utf-8")
        self.assertIn("Texas Grade 1 Math Assessment", html)
        self.assertIn("Answer Key", html)
        self.assertIn("1.2", html)


if __name__ == "__main__":
    unittest.main()
