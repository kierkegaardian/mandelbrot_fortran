from __future__ import annotations

import unittest

from app.early_math_catalog import spec_for
from app.explanations import explanation_for
from app.quiz_engine import generate_question
from app.skill_graph import subskills_for


MEASUREMENT_SUBSKILLS = (
    "Length unit conversion",
    "Time reading and arithmetic",
    "Capacity and weight units",
    "Temperature basics",
    "Metric and customary conversions",
    "Elapsed time",
)

AREA_VOLUME_SUBSKILLS = (
    "Area of rectangles and squares",
    "Area of triangles and parallelograms",
    "Surface area and volume",
)


class FoundationMeasurementScopeTests(unittest.TestCase):
    def test_foundation_measurement_scope_is_visible(self) -> None:
        self.assertEqual(MEASUREMENT_SUBSKILLS, subskills_for("measurement"))
        for subskill in AREA_VOLUME_SUBSKILLS:
            with self.subTest(subskill=subskill):
                self.assertIn(subskill, subskills_for("geometry_area"))

    def test_measurement_subskills_generate_mc_and_typed_questions(self) -> None:
        for subskill in MEASUREMENT_SUBSKILLS:
            for question_type in ("mc", "typed"):
                with self.subTest(subskill=subskill, question_type=question_type):
                    question = generate_question("measurement", 2, question_type, subskill=subskill)
                    self.assertEqual("measurement", question.skill)
                    self.assertEqual(subskill, question.subskill)
                    self.assertTrue(question.correct_answer)
                    if question_type == "mc":
                        self.assertIsNotNone(question.choices)
                        self.assertEqual(4, len(question.choices or ()))

    def test_measurement_subskills_have_intuition_and_lesson_links(self) -> None:
        for subskill in MEASUREMENT_SUBSKILLS:
            with self.subTest(subskill=subskill):
                explanation = explanation_for("measurement", subskill)
                spec = spec_for("measurement", subskill)
                self.assertTrue(explanation.mental_model)
                self.assertTrue(explanation.common_mistake)
                self.assertTrue(explanation.try_this)
                self.assertIsNotNone(spec)
                assert spec is not None
                self.assertTrue(spec.khan_assignable_url.startswith("https://www.khanacademy.org/"))

    def test_area_and_volume_generate_questions_through_geometry_area(self) -> None:
        for subskill in AREA_VOLUME_SUBSKILLS:
            with self.subTest(subskill=subskill):
                question = generate_question("geometry_area", 2, "mc", subskill=subskill)
                explanation = explanation_for("geometry_area", subskill)
                self.assertEqual("geometry_area", question.skill)
                self.assertEqual(subskill, question.subskill)
                self.assertTrue(question.correct_answer)
                self.assertIsNotNone(question.choices)
                self.assertTrue(explanation.mental_model)
                self.assertTrue(explanation.common_mistake)
                self.assertTrue(explanation.try_this)


if __name__ == "__main__":
    unittest.main()
