from __future__ import annotations

import unittest

from app.arithmetic_summer_lessons import build_summer_lesson, supports_summer_lesson
from app.explanations import explanation_for
from app.quiz_engine import generate_question
from app.skill_graph import skills_in_track, subskills_for
from app.texas_grade_goals import content_gap_goals, texas_grade_plan


class ElementaryShapesDataTests(unittest.TestCase):
    def test_shape_and_data_skills_are_visible_in_tracks(self) -> None:
        self.assertIn("geometry_shapes", skills_in_track("Geometry"))
        self.assertIn("data_displays", skills_in_track("Statistics / Probability"))
        self.assertEqual(
            (
                "2D shape attributes",
                "3D solid attributes",
                "Compose 2D shapes",
                "Equal shares of shapes",
            ),
            subskills_for("geometry_shapes"),
        )
        self.assertEqual(
            (
                "Sort data into categories",
                "Picture and bar graphs",
                "Dot plots",
                "Frequency tables",
                "Stem-and-leaf plots",
                "Scatterplots and paired data",
                "Questions from data displays",
            ),
            subskills_for("data_displays"),
        )

    def test_every_new_subskill_generates_a_question(self) -> None:
        for skill in ("geometry_shapes", "data_displays"):
            for subskill in subskills_for(skill):
                with self.subTest(skill=skill, subskill=subskill):
                    question = generate_question(skill, 1, "mc", subskill=subskill)
                    self.assertEqual(skill, question.skill)
                    self.assertEqual(subskill, question.subskill)
                    self.assertTrue(question.correct_answer)
                    self.assertIsNotNone(question.choices)

    def test_new_subskills_have_intuition_packs(self) -> None:
        for skill in ("geometry_shapes", "data_displays"):
            for subskill in subskills_for(skill):
                with self.subTest(skill=skill, subskill=subskill):
                    explanation = explanation_for(skill, subskill)
                    self.assertTrue(explanation.mental_model)
                    self.assertTrue(explanation.common_mistake)
                    self.assertTrue(explanation.try_this)

    def test_guided_lessons_cover_shape_and_data_skills(self) -> None:
        for skill in ("geometry_shapes", "data_displays"):
            with self.subTest(skill=skill):
                self.assertTrue(supports_summer_lesson(skill))
                steps = build_summer_lesson(skill)
                self.assertEqual(3, len(steps))
                self.assertTrue(any(step.expected_answer for step in steps))

    def test_grade_one_texas_plan_now_covers_shapes_and_data(self) -> None:
        plan = texas_grade_plan(1)
        goals = {goal.code: goal for goal in plan.goals}
        self.assertEqual("geometry_shapes", goals["g1_shapes"].skill)
        self.assertEqual("data_displays", goals["g1_data"].skill)
        self.assertEqual((), content_gap_goals(1))


if __name__ == "__main__":
    unittest.main()
