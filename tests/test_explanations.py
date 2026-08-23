from __future__ import annotations

import unittest

from app.explanations import ARITHMETIC_MODE_EXPLANATIONS, explanation_for
from app.skill_graph import SKILL_LABELS
from app.ui_arithmetic import KHAN_URL_BY_SKILL


class ExplanationCoverageTests(unittest.TestCase):
    def test_every_skill_has_an_explanation_entry(self) -> None:
        expected = {skill for skill in SKILL_LABELS if skill != "mixed"}
        missing = sorted(expected.difference(ARITHMETIC_MODE_EXPLANATIONS))
        self.assertFalse(missing, f"Missing explanation entries: {missing}")

    def test_every_skill_has_enriched_intuition_sections(self) -> None:
        expected = {skill for skill in SKILL_LABELS if skill != "mixed"}
        missing_by_skill: dict[str, list[str]] = {}
        for skill in sorted(expected):
            explanation = ARITHMETIC_MODE_EXPLANATIONS[skill]
            missing_fields = [
                field
                for field in (
                    "how_short",
                    "how_long",
                    "why_short",
                    "why_long",
                    "mental_model",
                    "common_mistake",
                    "try_this",
                )
                if not getattr(explanation, field).strip()
            ]
            if missing_fields:
                missing_by_skill[skill] = missing_fields
        self.assertFalse(missing_by_skill, f"Incomplete explanations: {missing_by_skill}")

    def test_every_skill_has_a_khan_mapping(self) -> None:
        expected = {skill for skill in SKILL_LABELS if skill != "mixed"}
        missing = sorted(expected.difference(KHAN_URL_BY_SKILL))
        self.assertFalse(missing, f"Missing Khan links: {missing}")
        for skill in sorted(expected):
            with self.subTest(skill=skill):
                self.assertTrue(KHAN_URL_BY_SKILL[skill].startswith("https://www.khanacademy.org/"))

    def test_algebra_1_function_transformations_have_specific_intuition(self) -> None:
        generic = ARITHMETIC_MODE_EXPLANATIONS["algebra_1"]
        explanation = explanation_for("algebra_1", "Function transformations")

        self.assertNotEqual(generic.mental_model, explanation.mental_model)
        self.assertIn("inside changes", explanation.mental_model)
        self.assertIn("substituting the full shifted input", explanation.common_mistake)
        self.assertIn("g(x)", explanation.try_this)

    def test_algebra_1_slope_from_points_has_specific_intuition(self) -> None:
        generic = ARITHMETIC_MODE_EXPLANATIONS["algebra_1"]
        explanation = explanation_for("algebra_1", "Slope from points")

        self.assertNotEqual(generic.mental_model, explanation.mental_model)
        self.assertIn("rise divided by run", explanation.mental_model)
        self.assertIn("flips the sign", explanation.common_mistake)
        self.assertIn("change in y", explanation.try_this)

    def test_algebra_1_slope_intercept_form_has_specific_intuition(self) -> None:
        generic = ARITHMETIC_MODE_EXPLANATIONS["algebra_1"]
        explanation = explanation_for("algebra_1", "Slope-intercept form")

        self.assertNotEqual(generic.mental_model, explanation.mental_model)
        self.assertIn("rate of change", explanation.mental_model)
        self.assertIn("x-intercept", explanation.common_mistake)
        self.assertIn("crosses the y-axis", explanation.try_this)

    def test_algebra_1_graphing_linear_inequalities_has_specific_intuition(self) -> None:
        generic = ARITHMETIC_MODE_EXPLANATIONS["algebra_1"]
        explanation = explanation_for("algebra_1", "Graphing linear inequalities")

        self.assertNotEqual(generic.mental_model, explanation.mental_model)
        self.assertIn("boundary line", explanation.mental_model)
        self.assertIn("greater-than or less-than", explanation.common_mistake)
        self.assertIn("one point above", explanation.try_this)

    def test_algebra_1_systems_by_substitution_have_specific_intuition(self) -> None:
        generic = ARITHMETIC_MODE_EXPLANATIONS["algebra_1"]
        explanation = explanation_for("algebra_1", "Systems by substitution")

        self.assertNotEqual(generic.mental_model, explanation.mental_model)
        self.assertIn("same point", explanation.mental_model)
        self.assertIn("same x and y", explanation.common_mistake)
        self.assertIn("set the right sides equal", explanation.try_this)

    def test_algebra_1_systems_by_elimination_have_specific_intuition(self) -> None:
        generic = ARITHMETIC_MODE_EXPLANATIONS["algebra_1"]
        explanation = explanation_for("algebra_1", "Systems by elimination")

        self.assertNotEqual(generic.mental_model, explanation.mental_model)
        self.assertIn("one variable disappears", explanation.mental_model)
        self.assertIn("opposite coefficients cancel", explanation.common_mistake)
        self.assertIn("watch x disappear", explanation.try_this)

    def test_algebra_1_graphing_systems_have_specific_intuition(self) -> None:
        generic = ARITHMETIC_MODE_EXPLANATIONS["algebra_1"]
        explanation = explanation_for("algebra_1", "Graphing systems and intersections")

        self.assertNotEqual(generic.mental_model, explanation.mental_model)
        self.assertIn("same plane", explanation.mental_model)
        self.assertIn("cross each other", explanation.common_mistake)
        self.assertIn("lines meet", explanation.try_this)

    def test_algebra_1_radicals_and_rational_exponents_have_specific_intuition(self) -> None:
        generic = ARITHMETIC_MODE_EXPLANATIONS["algebra_1"]
        explanation = explanation_for("algebra_1", "Radicals and rational exponents")

        self.assertNotEqual(generic.mental_model, explanation.mental_model)
        self.assertIn("x^(1/n)", explanation.mental_model)
        self.assertIn("root index", explanation.common_mistake)
        self.assertIn("64^(1/3)", explanation.try_this)

    def test_algebra_1_polynomial_arithmetic_has_specific_intuition(self) -> None:
        generic = ARITHMETIC_MODE_EXPLANATIONS["algebra_1"]
        explanation = explanation_for("algebra_1", "Polynomial arithmetic")

        self.assertNotEqual(generic.mental_model, explanation.mental_model)
        self.assertIn("matching powers", explanation.mental_model)
        self.assertIn("unlike terms", explanation.common_mistake)
        self.assertIn("like terms", explanation.try_this)

    def test_algebra_1_factoring_basics_has_specific_intuition(self) -> None:
        generic = ARITHMETIC_MODE_EXPLANATIONS["algebra_1"]
        explanation = explanation_for("algebra_1", "Factoring basics")

        self.assertNotEqual(generic.mental_model, explanation.mental_model)
        self.assertIn("reverses multiplication", explanation.mental_model)
        self.assertIn("x-coefficient", explanation.common_mistake)
        self.assertIn("factor pairs", explanation.try_this)

    def test_algebra_1_quadratic_multiplying_has_specific_intuition(self) -> None:
        generic = ARITHMETIC_MODE_EXPLANATIONS["algebra_1"]
        explanation = explanation_for("algebra_1", "Quadratics: Multiplying & factoring")

        self.assertNotEqual(generic.mental_model, explanation.mental_model)
        self.assertIn("cross-products", explanation.mental_model)
        self.assertIn("middle products", explanation.common_mistake)
        self.assertIn("8x term", explanation.try_this)

    def test_algebra_1_quadratic_grouping_has_specific_intuition(self) -> None:
        generic = ARITHMETIC_MODE_EXPLANATIONS["algebra_1"]
        explanation = explanation_for("algebra_1", "Quadratic factoring by grouping")

        self.assertNotEqual(generic.mental_model, explanation.mental_model)
        self.assertIn("ac method", explanation.mental_model)
        self.assertIn("middle coefficient", explanation.common_mistake)
        self.assertIn("split 7x", explanation.try_this)

    def test_algebra_1_difference_of_squares_has_specific_intuition(self) -> None:
        generic = ARITHMETIC_MODE_EXPLANATIONS["algebra_1"]
        explanation = explanation_for("algebra_1", "Difference of squares")

        self.assertNotEqual(generic.mental_model, explanation.mental_model)
        self.assertIn("one square minus another", explanation.mental_model)
        self.assertIn("sum of squares", explanation.common_mistake)
        self.assertIn("9x^2 - 25", explanation.try_this)

    def test_algebra_1_quadratic_formula_has_specific_intuition(self) -> None:
        generic = ARITHMETIC_MODE_EXPLANATIONS["algebra_1"]
        explanation = explanation_for("algebra_1", "Quadratic formula")

        self.assertNotEqual(generic.mental_model, explanation.mental_model)
        self.assertIn("universal root-finder", explanation.mental_model)
        self.assertIn("2a", explanation.common_mistake)
        self.assertIn("x^2 - 5x + 6", explanation.try_this)

    def test_algebra_1_completing_square_has_specific_intuition(self) -> None:
        generic = ARITHMETIC_MODE_EXPLANATIONS["algebra_1"]
        explanation = explanation_for("algebra_1", "Completing the square")

        self.assertNotEqual(generic.mental_model, explanation.mental_model)
        self.assertIn("perfect-square pattern", explanation.mental_model)
        self.assertIn("(b/2)^2", explanation.common_mistake)
        self.assertIn("x^2 + 8x", explanation.try_this)


if __name__ == "__main__":
    unittest.main()
