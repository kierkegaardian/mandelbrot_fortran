from __future__ import annotations

import os
from pathlib import Path
import tempfile
import unittest

from app import content_audit, content_audit_report, db
from app.content_audit import MISSING, READY
from app.summer_program_defs import FOUNDATION_BRIDGE_LANE, PREALGEBRA_FINISH_LANE


class SummerResourceReviewTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self._old_data_dir = os.environ.get("MANDELQUEST_DATA_DIR")
        tmp_path = self._tmp.name
        os.environ["MANDELQUEST_DATA_DIR"] = tmp_path

        def _tmp_config() -> db.DbConfig:
            return db.DbConfig(path=f"{tmp_path}/test_app.db")

        self.enterContext(db.override_db_config(_tmp_config))
        db.init_db()

    def tearDown(self) -> None:
        if self._old_data_dir is None:
            os.environ.pop("MANDELQUEST_DATA_DIR", None)
        else:
            os.environ["MANDELQUEST_DATA_DIR"] = self._old_data_dir
        self._tmp.cleanup()

    def test_prealgebra_review_includes_preview_rows_with_resources(self) -> None:
        review = content_audit.summer_resource_review(PREALGEBRA_FINISH_LANE)

        preview_rows = [row for row in review.rows if row.optional]
        self.assertGreaterEqual(len(preview_rows), 10)
        self.assertIn("linear_relationships_preview", {row.unit_code for row in preview_rows})
        self.assertIn("algebra_1_preview_capstone", {row.unit_code for row in preview_rows})
        self.assertIn("coordinate_geometry_preview", {row.unit_code for row in preview_rows})
        self.assertIn("geometry_preview_capstone", {row.unit_code for row in preview_rows})
        for row in preview_rows:
            with self.subTest(unit=row.unit_code, subskill=row.subskill):
                self.assertTrue(row.native_question_available)
                self.assertTrue(row.has_khan_link)
                self.assertTrue(row.has_open_resource)
                self.assertNotEqual(row.readiness, MISSING)

    def test_core_depth_targets_show_template_counts(self) -> None:
        review = content_audit.summer_resource_review(PREALGEBRA_FINISH_LANE)
        percent = next(row for row in review.rows if row.subskill == "Percent problems")
        ratios = next(row for row in review.rows if row.subskill == "Ratios, rates, and proportional relationships")

        self.assertGreaterEqual(percent.expression_template_count, 12)
        self.assertGreaterEqual(percent.word_template_count, 6)
        self.assertGreaterEqual(ratios.expression_template_count, 12)
        self.assertGreaterEqual(ratios.word_template_count, 6)
        self.assertNotEqual(percent.readiness, MISSING)
        self.assertNotEqual(ratios.readiness, MISSING)

    def test_linear_relationships_preview_rows_are_ready_after_seed_templates(self) -> None:
        review = content_audit.summer_resource_review(PREALGEBRA_FINISH_LANE)

        linear_rows = [row for row in review.rows if row.unit_code == "linear_relationships_preview"]

        self.assertEqual(len(linear_rows), 5)
        for row in linear_rows:
            with self.subTest(subskill=row.subskill):
                self.assertGreaterEqual(row.expression_template_count, 1)
                self.assertGreater(row.scaffold_step_count, 0)
                self.assertEqual(row.readiness, READY)

        word_model = next(row for row in linear_rows if row.subskill == "Word problems with linear models")
        self.assertGreaterEqual(word_model.word_template_count, 1)

    def test_functions_patterns_preview_rows_are_ready_after_seed_templates(self) -> None:
        review = content_audit.summer_resource_review(PREALGEBRA_FINISH_LANE)

        function_rows = [row for row in review.rows if row.unit_code == "functions_patterns_preview"]

        self.assertEqual(len(function_rows), 4)
        for row in function_rows:
            with self.subTest(subskill=row.subskill):
                self.assertGreaterEqual(row.expression_template_count, 1)
                self.assertGreaterEqual(row.word_template_count, 1)
                self.assertGreater(row.scaffold_step_count, 0)
                self.assertEqual(row.readiness, READY)

    def test_algebra_1_preview_capstone_rows_are_ready_after_seed_templates(self) -> None:
        review = content_audit.summer_resource_review(PREALGEBRA_FINISH_LANE)

        capstone_rows = [row for row in review.rows if row.unit_code == "algebra_1_preview_capstone"]

        self.assertEqual(len(capstone_rows), 6)
        self.assertEqual(
            {row.subskill for row in capstone_rows},
            {
                "Slope from points",
                "Functions",
                "Slope-intercept form",
                "Sequences",
                "Graphing linear inequalities",
                "Solving equations & inequalities",
            },
        )
        for row in capstone_rows:
            with self.subTest(subskill=row.subskill):
                self.assertEqual(row.skill, "algebra_1")
                self.assertGreaterEqual(row.expression_template_count, 1)
                self.assertGreaterEqual(row.word_template_count, 1)
                self.assertGreater(row.scaffold_step_count, 0)
                self.assertEqual(row.readiness, READY)

    def test_geometry_measurement_preview_rows_are_ready_after_seed_templates(self) -> None:
        review = content_audit.summer_resource_review(PREALGEBRA_FINISH_LANE)

        geometry_rows = [row for row in review.rows if row.unit_code == "geometry_measurement_preview"]

        self.assertEqual(len(geometry_rows), 5)
        for row in geometry_rows:
            with self.subTest(subskill=row.subskill):
                self.assertGreaterEqual(row.expression_template_count, 1)
                self.assertGreaterEqual(row.word_template_count, 1)
                self.assertGreater(row.scaffold_step_count, 0)
                self.assertEqual(row.readiness, READY)

    def test_coordinate_geometry_preview_rows_are_ready_after_seed_templates(self) -> None:
        review = content_audit.summer_resource_review(PREALGEBRA_FINISH_LANE)

        coordinate_rows = [row for row in review.rows if row.unit_code == "coordinate_geometry_preview"]

        self.assertEqual(len(coordinate_rows), 5)
        for row in coordinate_rows:
            with self.subTest(subskill=row.subskill):
                self.assertGreaterEqual(row.expression_template_count, 1)
                self.assertGreaterEqual(row.word_template_count, 1)
                self.assertGreater(row.scaffold_step_count, 0)
                self.assertEqual(row.readiness, READY)

    def test_geometry_preview_capstone_rows_are_ready_after_seed_templates(self) -> None:
        review = content_audit.summer_resource_review(PREALGEBRA_FINISH_LANE)

        capstone_rows = [row for row in review.rows if row.unit_code == "geometry_preview_capstone"]

        self.assertEqual(len(capstone_rows), 5)
        self.assertEqual(
            {row.subskill for row in capstone_rows},
            {
                "Circumference and area of circles",
                "Pythagorean theorem",
                "Coordinate geometry distance and midpoint",
                "Transformations and congruence",
                "Similarity and scale factor",
            },
        )
        for row in capstone_rows:
            with self.subTest(subskill=row.subskill):
                self.assertEqual(row.skill, "geometry_area")
                self.assertGreaterEqual(row.expression_template_count, 1)
                self.assertGreaterEqual(row.word_template_count, 1)
                self.assertGreater(row.scaffold_step_count, 0)
                self.assertEqual(row.readiness, READY)

    def test_prealgebra_finish_review_has_no_thin_or_missing_rows(self) -> None:
        review = content_audit.summer_resource_review(PREALGEBRA_FINISH_LANE)

        self.assertEqual(review.thin_count, 0)
        self.assertEqual(review.missing_count, 0)
        self.assertTrue(review.rows)
        for row in review.rows:
            with self.subTest(unit=row.unit_code, subskill=row.subskill):
                self.assertEqual(row.readiness, READY)

    def test_resource_review_report_exports_full_printable_audit(self) -> None:
        report = content_audit_report.generate_resource_review_report(PREALGEBRA_FINISH_LANE)

        self.assertEqual(report.ready_count, 43)
        self.assertEqual(report.thin_count, 0)
        self.assertEqual(report.missing_count, 0)
        self.assertEqual(report.row_count, 43)
        path = Path(report.path)
        self.assertTrue(path.exists())
        html = path.read_text(encoding="utf-8")
        self.assertIn("Pre-Algebra Finish Resource Review", html)
        self.assertIn("Algebra 1 mixed readiness", html)
        self.assertIn("Geometry mixed readiness", html)
        self.assertIn("Coordinate geometry distance and midpoint", html)
        self.assertIn("Khan", html)
        self.assertIn("Open resource", html)

    def test_foundation_bridge_has_no_preview_or_algebra_only_rows(self) -> None:
        review = content_audit.summer_resource_review(FOUNDATION_BRIDGE_LANE)

        self.assertTrue(review.rows)
        self.assertFalse(any(row.optional for row in review.rows))
        self.assertFalse(any(row.skill in {"algebra_linear", "algebra_1", "geometry_area"} for row in review.rows))
        for row in review.rows:
            with self.subTest(unit=row.unit_code, subskill=row.subskill):
                self.assertGreater(row.active_question_count, 0)
                self.assertTrue(row.has_khan_link)

    def test_weakest_rows_prioritize_actionable_gaps(self) -> None:
        review = content_audit.summer_resource_review(PREALGEBRA_FINISH_LANE)

        self.assertEqual(len(review.weakest_rows), len(review.rows))
        order = {"missing": 0, "thin": 1, "ready": 2}
        readiness_order = [order[row.readiness] for row in review.weakest_rows]
        self.assertEqual(readiness_order, sorted(readiness_order))


if __name__ == "__main__":
    unittest.main()
