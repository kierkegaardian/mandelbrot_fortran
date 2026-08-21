from __future__ import annotations

import unittest

from app.quiz_engine import generate_question
from app.skill_graph import subskills_for


class QuizEngineAlgebraCourseTests(unittest.TestCase):
    def test_all_pre_algebra_subskills_generate_mc_questions(self) -> None:
        for subskill in subskills_for("pre_algebra"):
            q = generate_question("pre_algebra", 2, "mc", subskill=subskill)
            self.assertEqual(q.skill, "pre_algebra")
            self.assertEqual(q.subskill, subskill)
            self.assertIsNotNone(q.choices)
            self.assertEqual(len(q.choices or []), 4)

    def test_all_algebra_1_subskills_generate_mc_questions(self) -> None:
        for subskill in subskills_for("algebra_1"):
            q = generate_question("algebra_1", 2, "mc", subskill=subskill)
            self.assertEqual(q.skill, "algebra_1")
            self.assertEqual(q.subskill, subskill)
            self.assertIsNotNone(q.choices)
            self.assertEqual(len(q.choices or []), 4)

    def test_all_algebra_2_subskills_generate_mc_questions(self) -> None:
        for subskill in subskills_for("algebra_2"):
            q = generate_question("algebra_2", 2, "mc", subskill=subskill)
            self.assertEqual(q.skill, "algebra_2")
            self.assertEqual(q.subskill, subskill)
            self.assertIsNotNone(q.choices)
            self.assertEqual(len(q.choices or []), 4)

    def test_algebra_1_word_modeling_subskill(self) -> None:
        q = generate_question("algebra_1", 2, "typed", subskill="Quadratic functions & equations")
        self.assertEqual(q.subskill, "Quadratic functions & equations")
        self.assertTrue(q.correct_answer)

    def test_algebra_1_core_topics_generate_questions(self) -> None:
        for subskill in (
            "Linear equations & graphs",
            "Slope from points",
            "Slope-intercept form",
            "Graphing linear inequalities",
            "Systems of equations",
            "Systems by substitution",
            "Systems by elimination",
            "Graphing systems and intersections",
            "Function transformations",
            "Exponents & radicals",
            "Radicals and rational exponents",
            "Polynomial arithmetic",
            "Factoring basics",
            "Quadratics: Multiplying & factoring",
            "Quadratic factoring by grouping",
            "Difference of squares",
            "Quadratic functions & equations",
            "Completing the square",
            "Quadratic formula",
        ):
            with self.subTest(subskill=subskill):
                q = generate_question("algebra_1", 2, "typed", subskill=subskill)
                self.assertEqual(q.subskill, subskill)
                self.assertTrue(q.correct_answer)

    def test_algebra_1_function_transformation_question_uses_shifted_input(self) -> None:
        q = generate_question("algebra_1", 2, "typed", subskill="Function transformations")

        self.assertEqual(q.subskill, "Function transformations")
        self.assertIn("g(x)", q.prompt)
        self.assertIn("find g(", q.prompt)
        self.assertTrue(q.correct_answer)
        self.assertIn("horizontal shift", q.explanation)

    def test_algebra_1_slope_from_points_uses_rise_over_run(self) -> None:
        q = generate_question("algebra_1", 2, "typed", subskill="Slope from points")

        self.assertEqual(q.subskill, "Slope from points")
        self.assertIn("slope of the line through", q.prompt)
        self.assertTrue(q.correct_answer)
        self.assertIn("rise over run", q.explanation)

    def test_algebra_1_slope_intercept_questions_name_starting_output(self) -> None:
        q = generate_question("algebra_1", 2, "typed", subskill="Slope-intercept form")

        self.assertEqual(q.subskill, "Slope-intercept form")
        self.assertIn("what is y when x = 0", q.prompt)
        self.assertTrue(q.correct_answer)
        self.assertIn("y-intercept", q.explanation)

    def test_algebra_1_graphing_linear_inequalities_uses_boundary_line(self) -> None:
        q = generate_question("algebra_1", 2, "typed", subskill="Graphing linear inequalities")

        self.assertEqual(q.subskill, "Graphing linear inequalities")
        self.assertIn("boundary y-value", q.prompt)
        self.assertTrue(q.correct_answer)
        self.assertIn("boundary line", q.explanation)
        self.assertIn("shades", q.explanation)

    def test_algebra_1_systems_by_substitution_uses_two_y_expressions(self) -> None:
        q = generate_question("algebra_1", 2, "typed", subskill="Systems by substitution")

        self.assertEqual(q.subskill, "Systems by substitution")
        self.assertIn("substitution", q.prompt)
        self.assertIn("y =", q.prompt)
        self.assertTrue(q.correct_answer)
        self.assertIn("one-variable equation", q.explanation)

    def test_algebra_1_systems_by_elimination_cancels_variable(self) -> None:
        q = generate_question("algebra_1", 2, "typed", subskill="Systems by elimination")

        self.assertEqual(q.subskill, "Systems by elimination")
        self.assertIn("elimination", q.prompt)
        self.assertIn("report y", q.prompt)
        self.assertTrue(q.correct_answer)
        self.assertIn("x-terms cancel", q.explanation)

    def test_algebra_1_graphing_systems_questions_use_intersection_language(self) -> None:
        q = generate_question("algebra_1", 2, "typed", subskill="Graphing systems and intersections")

        self.assertEqual(q.subskill, "Graphing systems and intersections")
        self.assertIn("On a graph", q.prompt)
        self.assertIn("x-coordinate", q.prompt)
        self.assertTrue(q.correct_answer)
        self.assertIn("intersection point", q.explanation)

    def test_algebra_1_rational_exponents_generate_nth_root_questions(self) -> None:
        q = generate_question("algebra_1", 2, "typed", subskill="Radicals and rational exponents")

        self.assertEqual(q.subskill, "Radicals and rational exponents")
        self.assertIn("^(1/", q.prompt)
        self.assertTrue(q.correct_answer)
        self.assertIn("nth root", q.explanation)

    def test_algebra_1_polynomial_arithmetic_combines_like_terms(self) -> None:
        q = generate_question("algebra_1", 2, "typed", subskill="Polynomial arithmetic")

        self.assertEqual(q.subskill, "Polynomial arithmetic")
        self.assertIn("coefficient of x^2", q.prompt)
        self.assertTrue(q.correct_answer)
        self.assertIn("Combine like terms", q.explanation)

    def test_algebra_1_factoring_basics_uses_sum_and_product(self) -> None:
        q = generate_question("algebra_1", 2, "typed", subskill="Factoring basics")

        self.assertEqual(q.subskill, "Factoring basics")
        self.assertIn("Factor x^2", q.prompt)
        self.assertIn("larger constant", q.prompt)
        self.assertTrue(q.correct_answer)
        self.assertIn("multiply to the constant", q.explanation)

    def test_algebra_1_quadratic_multiplying_questions_use_cross_products(self) -> None:
        q = generate_question("algebra_1", 2, "typed", subskill="Quadratics: Multiplying & factoring")

        self.assertEqual(q.subskill, "Quadratics: Multiplying & factoring")
        self.assertIn("Expand", q.prompt)
        self.assertIn("coefficient of x", q.prompt)
        self.assertTrue(q.correct_answer)
        self.assertIn("middle term", q.explanation)

    def test_algebra_1_quadratic_grouping_questions_use_ac_method(self) -> None:
        q = generate_question("algebra_1", 2, "typed", subskill="Quadratic factoring by grouping")

        self.assertEqual(q.subskill, "Quadratic factoring by grouping")
        self.assertIn("Factor", q.prompt)
        self.assertIn("larger x-coefficient", q.prompt)
        self.assertTrue(q.correct_answer)
        self.assertIn("ac method", q.explanation)

    def test_algebra_1_difference_of_squares_questions_use_pattern(self) -> None:
        q = generate_question("algebra_1", 2, "typed", subskill="Difference of squares")

        self.assertEqual(q.subskill, "Difference of squares")
        self.assertIn("Factor", q.prompt)
        self.assertIn("(ax + b)(ax - b)", q.prompt)
        self.assertTrue(q.correct_answer)
        self.assertIn("A^2 - B^2", q.explanation)

    def test_algebra_1_completing_square_questions_solve_roots(self) -> None:
        q = generate_question("algebra_1", 2, "typed", subskill="Completing the square")

        self.assertEqual(q.subskill, "Completing the square")
        self.assertIn("completing the square", q.prompt)
        self.assertIn("larger root", q.prompt)
        self.assertTrue(q.correct_answer)
        self.assertIn("(b/2)^2", q.explanation)

    def test_algebra_1_quadratic_formula_questions_use_discriminant(self) -> None:
        q = generate_question("algebra_1", 2, "typed", subskill="Quadratic formula")

        self.assertEqual(q.subskill, "Quadratic formula")
        self.assertIn("quadratic formula", q.prompt)
        self.assertIn("larger real root", q.prompt)
        self.assertTrue(q.correct_answer)
        self.assertIn("b^2 - 4ac", q.explanation)

    def test_pre_algebra_ratio_subskill(self) -> None:
        q = generate_question("pre_algebra", 2, "typed", subskill="Ratios, rates, and proportional relationships")
        self.assertEqual(q.subskill, "Ratios, rates, and proportional relationships")
        self.assertTrue(q.correct_answer)

    def test_pre_algebra_key_new_subskills_generate_questions(self) -> None:
        for subskill in (
            "Expressions and variables",
            "One-step equations",
            "Two-step equations and inequalities",
            "Percent problems",
            "Exponents, roots, and scientific notation",
            "Coordinate plane and function tables",
        ):
            with self.subTest(subskill=subskill):
                q = generate_question("pre_algebra", 2, "typed", subskill=subskill)
                self.assertEqual(q.subskill, subskill)
                self.assertTrue(q.correct_answer)

    def test_pre_algebra_template_backed_subskill_prefers_templates(self) -> None:
        q = generate_question("pre_algebra", 2, "typed", subskill="Two-step equations and inequalities")
        self.assertEqual(q.subskill, "Two-step equations and inequalities")
        self.assertIsNotNone(q.template_external_id)
        self.assertTrue(q.correct_answer)

    def test_algebra_2_log_subskill(self) -> None:
        q = generate_question("algebra_2", 2, "typed", subskill="Logarithms")
        self.assertEqual(q.subskill, "Logarithms")
        self.assertTrue(q.correct_answer)


if __name__ == "__main__":
    unittest.main()
