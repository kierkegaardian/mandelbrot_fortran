from __future__ import annotations

import unittest

from app.quiz_engine import generate_question
from app.skill_graph import subskills_for


class QuizEngineAlgebraGeometryTests(unittest.TestCase):
    def test_algebra_linear_systems_subskill_generates_specific_prompt(self) -> None:
        q = generate_question("algebra_linear", 2, "typed", subskill="Systems of linear equations")
        self.assertEqual(q.skill, "algebra_linear")
        self.assertEqual(q.subskill, "Systems of linear equations")
        self.assertIn("Solve the system", q.prompt)
        self.assertTrue(q.correct_answer)

    def test_geometry_coordinate_subskill_generates_specific_prompt(self) -> None:
        q = generate_question("geometry_area", 2, "typed", subskill="Coordinate geometry distance and midpoint")
        self.assertEqual(q.skill, "geometry_area")
        self.assertEqual(q.subskill, "Coordinate geometry distance and midpoint")
        self.assertTrue("distance" in q.prompt.lower() or "midpoint" in q.prompt.lower())
        self.assertTrue(q.correct_answer)

    def test_all_listed_algebra_subskills_generate_question(self) -> None:
        for subskill in subskills_for("algebra_linear"):
            q = generate_question("algebra_linear", 2, "mc", subskill=subskill)
            self.assertEqual(q.subskill, subskill)
            self.assertIsNotNone(q.choices)
            self.assertEqual(len(q.choices or []), 4)

    def test_all_listed_geometry_subskills_generate_question(self) -> None:
        for subskill in subskills_for("geometry_area"):
            q = generate_question("geometry_area", 2, "mc", subskill=subskill)
            self.assertEqual(q.subskill, subskill)
            self.assertIsNotNone(q.choices)
            self.assertEqual(len(q.choices or []), 4)


if __name__ == "__main__":
    unittest.main()
