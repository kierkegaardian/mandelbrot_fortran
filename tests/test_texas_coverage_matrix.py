from __future__ import annotations

import unittest

from app.texas_coverage_matrix import (
    CORE_TEKS_ROOTS,
    build_texas_coverage_report,
    render_texas_coverage_markdown,
)
from app.summer_program_defs import FOUNDATION_BRIDGE_LANE, PREALGEBRA_FINISH_LANE
from app.summer_program_quiz import assessment_blueprint_for_lane

from tests.early_math_test_utils import imported_early_math_data_dir


class TexasCoverageMatrixTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._temp_data = imported_early_math_data_dir()
        cls._temp_data.__enter__()

    @classmethod
    def tearDownClass(cls) -> None:
        cls._temp_data.__exit__(None, None, None)

    def test_report_has_no_missing_grade_one_through_seven_core_roots(self) -> None:
        report = build_texas_coverage_report()

        self.assertEqual((), report.missing_rows)
        self.assertEqual(CORE_TEKS_ROOTS, report.covered_roots_by_grade)

    def test_matrix_names_summer_diagnostics_for_previously_weak_teks_families(self) -> None:
        report = build_texas_coverage_report()
        rows = {row.goal_code: row for row in report.rows}

        expected_diagnostics = {
            "g1_personal_finance": "Foundation Bridge midpoint/exit: financial_literacy",
            "g4_data": "Foundation Bridge midpoint/exit: data_displays",
            "g7_probability": "Pre-Algebra Finish midpoint/exit: data_probability",
            "g7_data_comparisons": "Pre-Algebra Finish midpoint/exit: data_probability",
            "g7_personal_finance": "Pre-Algebra Finish midpoint/exit: financial_literacy",
        }
        for goal_code, expected in expected_diagnostics.items():
            with self.subTest(goal=goal_code):
                self.assertIn(expected, rows[goal_code].quiz_surfaces)
                self.assertEqual("diagnostic-only", rows[goal_code].coverage_status)

    def test_summer_assessment_blueprints_include_texas_diagnostic_strands(self) -> None:
        foundation = set(assessment_blueprint_for_lane(FOUNDATION_BRIDGE_LANE))
        prealgebra = set(assessment_blueprint_for_lane(PREALGEBRA_FINISH_LANE))

        self.assertIn(("geometry_shapes", "geometry_shapes", "2D shape attributes"), foundation)
        self.assertIn(("data_displays", "data_displays", "Frequency tables"), foundation)
        self.assertIn(("financial_literacy", "financial_literacy", "Income, gifts, wants, and needs"), foundation)
        self.assertIn(("data_probability", "stats_probability", "Probability models"), prealgebra)
        self.assertIn(("data_probability", "data_analysis", "Sample inferences from displays"), prealgebra)
        self.assertIn(
            (
                "financial_literacy",
                "financial_literacy",
                "Budget percentages, net worth, interest, and incentives",
            ),
            prealgebra,
        )

    def test_rendered_markdown_includes_summary_and_matrix(self) -> None:
        markdown = render_texas_coverage_markdown(build_texas_coverage_report())

        self.assertIn("# Texas TEKS Coverage Matrix, Grades 1-7", markdown)
        self.assertIn("Missing curriculum/quiz rows: 0", markdown)
        self.assertIn("| Grade | TEKS | Goal | Curriculum target | Summer units | Quiz/assessment coverage | Status | Notes |", markdown)
        self.assertIn("Calculate taxes, budget shares, net worth, interest, and incentives", markdown)


if __name__ == "__main__":
    unittest.main()
