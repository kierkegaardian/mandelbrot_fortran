from __future__ import annotations

import os
from pathlib import Path
import tempfile
import unittest

from app import db, school_year, school_year_assessment
from app.fall_readiness_audit import build_fall_readiness_report, render_fall_readiness_markdown


class FallReadinessAuditTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self._orig_data_dir = os.environ.get("MANDELQUEST_DATA_DIR")
        tmp_path = self._tmp.name
        os.environ["MANDELQUEST_DATA_DIR"] = tmp_path

        def _tmp_config() -> db.DbConfig:
            return db.DbConfig(path=f"{tmp_path}/test_app.db")

        self.enterContext(db.override_db_config(_tmp_config))
        db.init_db()

    def tearDown(self) -> None:
        if self._orig_data_dir is None:
            os.environ.pop("MANDELQUEST_DATA_DIR", None)
        else:
            os.environ["MANDELQUEST_DATA_DIR"] = self._orig_data_dir
        self._tmp.cleanup()

    def test_report_is_ready_and_names_core_school_year_contracts(self) -> None:
        report = build_fall_readiness_report()

        failures = [(check.code, check.evidence) for check in report.failures]
        self.assertTrue(report.ready, failures)
        codes = {check.code for check in report.checks}
        self.assertIn("texas_grades_1_to_7", codes)
        self.assertIn("grade_goal_problem_generation", codes)
        self.assertIn("two_child_independent_targets", codes)
        self.assertIn("quiz_test_packet_surface", codes)
        self.assertIn("child_first_navigation_and_bonus_explore", codes)

        markdown = render_fall_readiness_markdown(report)
        self.assertIn("Overall status: ready", markdown)
        self.assertIn("Texas standards source:", markdown)
        self.assertIn("| adaptive_blended_practice_policy | pass |", markdown)

    def test_two_children_keep_independent_texas_grade_paths(self) -> None:
        now = "2026-06-26T12:00:00+00:00"
        kid_one = db.create_profile("Kid One", "child", now)
        kid_two = db.create_profile("Kid Two", "child", now)

        db.save_school_year_target(kid_one.id, 1, False, now)
        db.save_school_year_target(kid_two.id, 7, True, now)

        status_one = school_year.school_year_status(kid_one.id)
        status_two = school_year.school_year_status(kid_two.id)
        self.assertIsNotNone(status_one)
        self.assertIsNotNone(status_two)
        assert status_one is not None
        assert status_two is not None

        self.assertEqual(1, status_one.target.grade)
        self.assertEqual(7, status_two.target.grade)
        self.assertFalse(status_one.target.stretch_enabled)
        self.assertTrue(status_two.target.stretch_enabled)
        self.assertEqual("g1_place_value", status_one.next_goal.code if status_one.next_goal else None)
        self.assertEqual("g7_rational_operations", status_two.next_goal.code if status_two.next_goal else None)
        self.assertNotEqual(status_one.total_count, status_two.total_count)

    def test_grade_one_and_seven_packets_generate_questions_and_answer_keys(self) -> None:
        for grade in (1, 7):
            with self.subTest(grade=grade):
                packet = school_year_assessment.generate_texas_grade_assessment(
                    grade,
                    include_stretch=True,
                    questions_per_subskill=1,
                )
                path = Path(packet.path)
                html = path.read_text(encoding="utf-8")

                self.assertEqual(grade, packet.grade)
                self.assertTrue(path.exists())
                self.assertGreaterEqual(len(packet.items), 8)
                self.assertFalse(any("content gap" in note for note in packet.skipped))
                self.assertIn(f"Texas Grade {grade} Math Assessment", html)
                self.assertIn("Answer Key", html)
                self.assertIn(f"{grade}.", html)


if __name__ == "__main__":
    unittest.main()
