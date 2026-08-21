from __future__ import annotations

import unittest

from app.algebra_1_generators import ALGEBRA_1_SUBSKILLS
from app.explanations import ARITHMETIC_MODE_EXPLANATIONS, explanation_for
from app.quiz_engine import generate_question
from app.skill_graph import subskills_for
from app.texas_grade_goals import quiz_ready_goals
from app.ui_arithmetic import khan_url_for_selection, lesson_link_state
from app.ui_settings import UiSettings


ALGEBRA_1_ROADMAP_GROUPS: dict[str, tuple[str, ...]] = {
    "Linear equations/inequalities; slope and y=mx+b intuition": (
        "Solving equations & inequalities",
        "Linear equations & graphs",
        "Forms of linear equations",
        "Slope from points",
        "Slope-intercept form",
        "Graphing linear inequalities",
        "Inequalities (systems & graphs)",
    ),
    "Systems of equations (graphing + substitution/elimination)": (
        "Systems of equations",
        "Systems by substitution",
        "Systems by elimination",
        "Graphing systems and intersections",
    ),
    "Polynomials: add/subtract/multiply; factoring basics": (
        "Polynomial arithmetic",
        "Factoring basics",
        "Quadratics: Multiplying & factoring",
    ),
    "Quadratics: factoring, completing the square, quadratic formula": (
        "Quadratic functions & equations",
        "Quadratic factoring by grouping",
        "Difference of squares",
        "Completing the square",
        "Quadratic formula",
    ),
    "Radicals, rational exponents, and function transformations": (
        "Functions",
        "Sequences",
        "Absolute value & piecewise functions",
        "Function transformations",
        "Exponents & radicals",
        "Radicals and rational exponents",
        "Exponential growth & decay",
        "Irrational numbers",
    ),
}


class Algebra1ScopeTests(unittest.TestCase):
    def test_algebra_1_roadmap_groups_are_visible(self) -> None:
        visible = set(subskills_for("algebra_1"))
        self.assertEqual(ALGEBRA_1_SUBSKILLS, subskills_for("algebra_1"))
        for group, subskills in ALGEBRA_1_ROADMAP_GROUPS.items():
            with self.subTest(group=group):
                self.assertTrue(set(subskills).issubset(visible))

    def test_algebra_1_subskills_generate_mc_and_typed_questions(self) -> None:
        for subskill in ALGEBRA_1_SUBSKILLS:
            for question_type in ("mc", "typed"):
                with self.subTest(subskill=subskill, question_type=question_type):
                    question = generate_question("algebra_1", 2, question_type, subskill=subskill)
                    self.assertEqual("algebra_1", question.skill)
                    self.assertEqual(subskill, question.subskill)
                    self.assertTrue(question.correct_answer)
                    if question_type == "mc":
                        self.assertIsNotNone(question.choices)
                        self.assertEqual(4, len(question.choices or ()))

    def test_algebra_1_subskills_have_specific_intuition_and_links(self) -> None:
        generic = ARITHMETIC_MODE_EXPLANATIONS["algebra_1"]
        links_off = UiSettings(show_external_links=False, enforce_offline_mode=False)
        links_on = UiSettings(show_external_links=True, enforce_offline_mode=False)

        for subskill in ALGEBRA_1_SUBSKILLS:
            with self.subTest(subskill=subskill):
                explanation = explanation_for("algebra_1", subskill)
                self.assertTrue(explanation.mental_model)
                self.assertTrue(explanation.common_mistake)
                self.assertTrue(explanation.try_this)
                self.assertNotEqual(generic.mental_model, explanation.mental_model)

                url = khan_url_for_selection("algebra_1", subskill)
                self.assertTrue(url.startswith("https://www.khanacademy.org/"))
                self.assertFalse(lesson_link_state("algebra_1", subskill, links_off).enabled)
                enabled = lesson_link_state("algebra_1", subskill, links_on)
                self.assertTrue(enabled.enabled)
                self.assertEqual(url, enabled.url)

    def test_texas_grade_seven_stretch_maps_into_algebra_1_scope(self) -> None:
        stretch_goals = {
            goal.code: goal
            for goal in quiz_ready_goals(7)
            if goal.stretch and goal.skill == "algebra_1"
        }

        self.assertIn("g7_algebra1_stretch", stretch_goals)
        goal = stretch_goals["g7_algebra1_stretch"]
        self.assertEqual(("Functions", "Sequences", "Linear equations & graphs"), goal.subskills)
        self.assertTrue(set(goal.subskills).issubset(set(ALGEBRA_1_SUBSKILLS)))


if __name__ == "__main__":
    unittest.main()
