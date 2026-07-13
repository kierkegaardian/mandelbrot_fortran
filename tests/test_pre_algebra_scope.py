from __future__ import annotations

from contextlib import closing
import sqlite3
import unittest

from app.early_math_catalog import spec_for
from app.explanations import explanation_for
from app.pre_algebra_generators import PRE_ALGEBRA_SUBSKILLS
from app.quiz_engine import generate_question
from app.skill_graph import subskills_for
from app.texas_grade_goals import quiz_ready_goals, texas_grade_plan

from tests.early_math_test_utils import imported_early_math_data_dir


PRE_ALGEBRA_ROADMAP_GROUPS: dict[str, tuple[str, ...]] = {
    "Expressions, variables, integer operations, and order of operations": (
        "Integer and fraction fluency",
        "Order of operations",
        "Expressions and variables",
    ),
    "One- and two-step equations/inequalities; coordinate plane": (
        "One-step equations",
        "Two-step equations and inequalities",
        "Coordinate plane and function tables",
    ),
    "Proportional relationships, ratios, rates, percent problems": (
        "Ratios, rates, and proportional relationships",
        "Percent problems",
    ),
    "Exponents, roots, scientific notation, and basic function tables": (
        "Exponents, roots, and scientific notation",
        "Coordinate plane and function tables",
    ),
}


class PreAlgebraScopeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._temp_data = imported_early_math_data_dir()
        cls._data_dir = cls._temp_data.__enter__()
        cls._db_path = cls._data_dir / "app.db"

    @classmethod
    def tearDownClass(cls) -> None:
        cls._temp_data.__exit__(None, None, None)

    def _active_template_count(self, subskill: str, mode: str) -> int:
        with closing(sqlite3.connect(self._db_path)) as conn:
            row = conn.execute(
                """
                SELECT COUNT(*)
                FROM question_templates
                WHERE active = 1 AND skill = 'pre_algebra' AND subskill = ? AND mode = ?
                """,
                (subskill, mode),
            ).fetchone()
        assert row is not None
        return int(row[0])

    def test_pre_algebra_roadmap_groups_are_visible(self) -> None:
        visible = set(subskills_for("pre_algebra"))
        self.assertEqual(PRE_ALGEBRA_SUBSKILLS, subskills_for("pre_algebra"))
        for group, subskills in PRE_ALGEBRA_ROADMAP_GROUPS.items():
            with self.subTest(group=group):
                self.assertTrue(set(subskills).issubset(visible))

    def test_pre_algebra_subskills_generate_mc_and_typed_questions(self) -> None:
        for subskill in PRE_ALGEBRA_SUBSKILLS:
            for question_type in ("mc", "typed"):
                with self.subTest(subskill=subskill, question_type=question_type):
                    question = generate_question("pre_algebra", 2, question_type, subskill=subskill)
                    self.assertEqual("pre_algebra", question.skill)
                    self.assertEqual(subskill, question.subskill)
                    self.assertTrue(question.correct_answer)
                    if question_type == "mc":
                        self.assertIsNotNone(question.choices)
                        self.assertEqual(4, len(question.choices or ()))

    def test_pre_algebra_subskills_have_intuition_links_and_templates(self) -> None:
        for subskill in PRE_ALGEBRA_SUBSKILLS:
            with self.subTest(subskill=subskill):
                explanation = explanation_for("pre_algebra", subskill)
                spec = spec_for("pre_algebra", subskill)
                self.assertTrue(explanation.mental_model)
                self.assertTrue(explanation.common_mistake)
                self.assertTrue(explanation.try_this)
                self.assertIsNotNone(spec)
                assert spec is not None
                self.assertTrue(spec.khan_assignable_url.startswith("https://www.khanacademy.org/"))
                self.assertGreaterEqual(self._active_template_count(subskill, "expression"), 2)
                if "word" in spec.required_modes:
                    self.assertGreater(self._active_template_count(subskill, "word"), 0)

    def test_texas_grades_five_through_seven_map_into_pre_algebra_scope(self) -> None:
        pre_algebra_items = {
            (grade, goal.code, subskill)
            for grade in range(5, 8)
            for goal in quiz_ready_goals(grade)
            if goal.skill == "pre_algebra"
            for subskill in goal.subskills
        }
        covered_subskills = {item[2] for item in pre_algebra_items}

        self.assertIn((5, "g5_coordinate_plane", "Coordinate plane and function tables"), pre_algebra_items)
        self.assertIn((6, "g6_proportionality", "Percent problems"), pre_algebra_items)
        self.assertIn((6, "g6_expressions", "One-step equations"), pre_algebra_items)
        self.assertIn((7, "g7_rational_operations", "Integer and fraction fluency"), pre_algebra_items)
        self.assertTrue(
            {
                "Integer and fraction fluency",
                "Expressions and variables",
                "One-step equations",
                "Ratios, rates, and proportional relationships",
                "Percent problems",
                "Coordinate plane and function tables",
            }.issubset(covered_subskills)
        )

    def test_grade_five_order_of_operations_is_covered_as_companion_foundation(self) -> None:
        goals = {goal.code: goal for goal in texas_grade_plan(5).goals}

        self.assertEqual("order_of_operations", goals["g5_expressions"].skill)
        self.assertIn("Parentheses first", goals["g5_expressions"].subskills)
        self.assertIn("Expression grouping", goals["g5_expressions"].subskills)


if __name__ == "__main__":
    unittest.main()
