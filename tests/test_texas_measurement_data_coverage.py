from __future__ import annotations

import unittest

from app.quiz_engine import generate_question
from app.school_year_assessment import generate_texas_grade_assessment
from app.texas_grade_goals import quiz_ready_goals, texas_grade_plan


EXPECTED_COVERAGE: dict[int, tuple[tuple[str, str], ...]] = {
    2: (("2.8", "geometry_shapes"), ("2.9", "measurement"), ("2.10", "data_displays")),
    3: (("3.6", "geometry_area"), ("3.7", "measurement"), ("3.8", "data_displays")),
    4: (("4.6", "geometry_area"), ("4.8", "measurement"), ("4.9", "data_displays")),
    5: (("5.6", "geometry_area"), ("5.7", "measurement"), ("5.8", "pre_algebra"), ("5.9", "data_displays")),
}

EXPECTED_MIDDLE_COVERAGE: dict[int, tuple[tuple[str, str], ...]] = {
    6: (
        ("6.8", "geometry_area"),
        ("6.11", "pre_algebra"),
        ("6.12", "data_analysis"),
        ("6.12", "stats_mean"),
        ("6.12", "stats_percent"),
    ),
    7: (
        ("7.6", "stats_probability"),
        ("7.9", "geometry_area"),
        ("7.12", "data_analysis"),
    ),
}


class TexasMeasurementDataCoverageTests(unittest.TestCase):
    def test_grades_two_through_five_have_quiz_ready_measurement_and_data_goals(self) -> None:
        for grade, expectations in EXPECTED_COVERAGE.items():
            goals = quiz_ready_goals(grade)
            for ref_root, skill in expectations:
                with self.subTest(grade=grade, ref=ref_root, skill=skill):
                    matches = [
                        goal
                        for goal in goals
                        if goal.skill == skill and any(ref.startswith(ref_root) for ref in goal.standard_refs)
                    ]
                    self.assertTrue(matches)
                    self.assertTrue(matches[0].subskills)

    def test_data_standards_are_explicit_data_display_goals(self) -> None:
        for grade in range(2, 6):
            with self.subTest(grade=grade):
                data_goals = [goal for goal in texas_grade_plan(grade).goals if goal.skill == "data_displays"]
                self.assertEqual(1, len(data_goals))
                self.assertEqual(f"g{grade}_data", data_goals[0].code)
                self.assertTrue(any(ref.startswith(f"{grade}.") for ref in data_goals[0].standard_refs))

    def test_texas_goal_subskills_generate_questions(self) -> None:
        focus_skills = {
            "measurement",
            "data_displays",
            "geometry_area",
            "geometry_shapes",
            "pre_algebra",
            "stats_mean",
            "stats_percent",
            "stats_probability",
            "statistics",
            "financial_literacy",
            "data_analysis",
        }
        for grade in range(2, 8):
            for goal in quiz_ready_goals(grade):
                if goal.skill not in focus_skills:
                    continue
                assert goal.skill is not None
                for subskill in goal.subskills:
                    with self.subTest(grade=grade, goal=goal.code, subskill=subskill):
                        question = generate_question(goal.skill, goal.quiz_level, "mc", subskill=subskill)
                        self.assertEqual(goal.skill, question.skill)
                        self.assertEqual(subskill, question.subskill)
                        self.assertTrue(question.correct_answer)

    def test_grades_six_and_seven_split_measurement_data_and_probability(self) -> None:
        for grade, expectations in EXPECTED_MIDDLE_COVERAGE.items():
            goals = quiz_ready_goals(grade)
            for ref_root, skill in expectations:
                with self.subTest(grade=grade, ref=ref_root, skill=skill):
                    matches = [
                        goal
                        for goal in goals
                        if goal.skill == skill and any(ref.startswith(ref_root) for ref in goal.standard_refs)
                    ]
                    self.assertTrue(matches)
                    self.assertTrue(matches[0].subskills)

    def test_grade_seven_probability_and_inference_are_not_geometry_only(self) -> None:
        goals = {goal.code: goal for goal in texas_grade_plan(7).goals}

        self.assertEqual("stats_probability", goals["g7_probability"].skill)
        self.assertEqual("data_analysis", goals["g7_data_comparisons"].skill)
        self.assertNotIn("7.12", goals["g7_similarity_circles"].standard_refs)
        self.assertNotIn("7.12", goals["g7_volume_surface_area"].standard_refs)

    def test_middle_school_data_displays_include_exact_teks_display_types(self) -> None:
        grade_six = {goal.code: goal for goal in texas_grade_plan(6).goals}
        grade_seven = {goal.code: goal for goal in texas_grade_plan(7).goals}

        self.assertEqual("data_analysis", grade_six["g6_data_displays"].skill)
        self.assertIn("Histograms", grade_six["g6_data_displays"].subskills)
        self.assertIn("Box plots", grade_six["g6_data_displays"].subskills)
        self.assertIn("Center, spread, and shape", grade_six["g6_data_displays"].subskills)
        self.assertIn("Variability in data", grade_six["g6_data_displays"].subskills)
        self.assertEqual("data_analysis", grade_six["g6_median_iqr"].skill)
        self.assertIn("Median, range, and IQR", grade_six["g6_median_iqr"].subskills)

        self.assertIn("Comparative dot and box plots", grade_seven["g7_data_comparisons"].subskills)
        self.assertIn("Sample inferences from displays", grade_seven["g7_data_comparisons"].subskills)
        self.assertIn("Part-to-whole display comparisons", grade_seven["g7_data_comparisons"].subskills)

    def test_grade_five_assessment_packet_includes_data_goal(self) -> None:
        packet = generate_texas_grade_assessment(5, include_stretch=False, questions_per_subskill=1)
        item_keys = {(item.goal.code, item.subskill) for item in packet.items}

        self.assertIn(("g5_data", "Scatterplots and paired data"), item_keys)
        self.assertIn(("g5_measurement", "Metric and customary conversions"), item_keys)
        self.assertFalse(any("content gap" in note for note in packet.skipped))

    def test_grade_seven_assessment_packet_includes_probability_and_inference(self) -> None:
        packet = generate_texas_grade_assessment(7, include_stretch=False, questions_per_subskill=1)
        item_keys = {(item.goal.code, item.subskill) for item in packet.items}

        self.assertIn(("g7_probability", "Probability models"), item_keys)
        self.assertIn(("g7_data_comparisons", "Comparative dot and box plots"), item_keys)
        self.assertIn(("g7_data_comparisons", "Sample inferences from displays"), item_keys)
        self.assertFalse(any("content gap" in note for note in packet.skipped))


if __name__ == "__main__":
    unittest.main()
