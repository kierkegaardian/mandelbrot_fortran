from __future__ import annotations

import unittest

from app.explanations import ARITHMETIC_MODE_EXPLANATIONS, explanation_for
from app.quiz_engine import GEOMETRY_AREA_SUBSKILLS, generate_question
from app.skill_graph import subskills_for
from app.texas_grade_goals import quiz_ready_goals
from app.ui_arithmetic import khan_url_for_selection, lesson_link_state
from app.ui_settings import UiSettings


GEOMETRY_ROADMAP_GROUPS: dict[str, tuple[tuple[str, str], ...]] = {
    "Proofs: congruence/similarity, triangle criteria, angle theorems": (
        ("geometry_area", "Angles in lines and triangles"),
        ("geometry_area", "Triangle congruence criteria"),
        ("geometry_area", "Transformations and congruence"),
        ("geometry_area", "Similarity and scale factor"),
        ("geometry_area", "Analytic geometry and coordinate proofs"),
    ),
    "Polygons, circles, area/volume, coordinate geometry": (
        ("geometry_area", "Area of rectangles and squares"),
        ("geometry_area", "Area of triangles and parallelograms"),
        ("geometry_area", "Area of trapezoids and composite figures"),
        ("geometry_area", "Perimeter and missing sides"),
        ("geometry_area", "Circumference and area of circles"),
        ("geometry_area", "Surface area and volume"),
        ("geometry_area", "Coordinate geometry distance and midpoint"),
    ),
    "Right-triangle trigonometry and basic trig ratios": (
        ("geometry_area", "Pythagorean theorem"),
        ("trig_right_triangle", "Right-triangle trig ratios"),
    ),
}


class GeometryScopeTests(unittest.TestCase):
    def test_geometry_roadmap_groups_are_visible(self) -> None:
        visible = {
            (skill, subskill)
            for skill in ("geometry_area", "trig_right_triangle")
            for subskill in subskills_for(skill)
        }
        self.assertEqual(GEOMETRY_AREA_SUBSKILLS, subskills_for("geometry_area"))
        for group, subskills in GEOMETRY_ROADMAP_GROUPS.items():
            with self.subTest(group=group):
                self.assertTrue(set(subskills).issubset(visible))

    def test_geometry_and_trig_subskills_generate_mc_and_typed_questions(self) -> None:
        for skill in ("geometry_area", "trig_right_triangle"):
            for subskill in subskills_for(skill):
                for question_type in ("mc", "typed"):
                    with self.subTest(skill=skill, subskill=subskill, question_type=question_type):
                        question = generate_question(skill, 2, question_type, subskill=subskill)
                        self.assertEqual(skill, question.skill)
                        self.assertEqual(subskill, question.subskill)
                        self.assertTrue(question.correct_answer)
                        if question_type == "mc":
                            self.assertIsNotNone(question.choices)
                            self.assertEqual(4, len(question.choices or ()))

    def test_geometry_and_trig_subskills_have_specific_intuition_and_links(self) -> None:
        links_off = UiSettings(show_external_links=False, enforce_offline_mode=False)
        links_on = UiSettings(show_external_links=True, enforce_offline_mode=False)

        for skill in ("geometry_area", "trig_right_triangle"):
            generic = ARITHMETIC_MODE_EXPLANATIONS[skill]
            for subskill in subskills_for(skill):
                with self.subTest(skill=skill, subskill=subskill):
                    explanation = explanation_for(skill, subskill)
                    self.assertTrue(explanation.mental_model)
                    self.assertTrue(explanation.common_mistake)
                    self.assertTrue(explanation.try_this)
                    self.assertNotEqual(generic.mental_model, explanation.mental_model)

                    url = khan_url_for_selection(skill, subskill)
                    self.assertTrue(url.startswith("https://www.khanacademy.org/"))
                    self.assertFalse(lesson_link_state(skill, subskill, links_off).enabled)
                    enabled = lesson_link_state(skill, subskill, links_on)
                    self.assertTrue(enabled.enabled)
                    self.assertEqual(url, enabled.url)

    def test_texas_geometry_goals_map_into_geometry_scope(self) -> None:
        geometry_items = {
            (grade, goal.code, subskill)
            for grade in range(2, 8)
            for goal in quiz_ready_goals(grade)
            if goal.skill == "geometry_area"
            for subskill in goal.subskills
        }

        self.assertIn((5, "g5_volume", "Surface area and volume"), geometry_items)
        self.assertIn((6, "g6_geometry_measurement", "Area of trapezoids and composite figures"), geometry_items)
        self.assertIn((7, "g7_similarity_circles", "Similarity and scale factor"), geometry_items)
        self.assertIn((7, "g7_similarity_circles", "Circumference and area of circles"), geometry_items)
        self.assertTrue(
            {
                "Area of rectangles and squares",
                "Area of triangles and parallelograms",
                "Area of trapezoids and composite figures",
                "Perimeter and missing sides",
                "Circumference and area of circles",
                "Surface area and volume",
                "Similarity and scale factor",
            }.issubset({item[2] for item in geometry_items})
        )


if __name__ == "__main__":
    unittest.main()
