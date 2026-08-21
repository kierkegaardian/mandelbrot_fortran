from __future__ import annotations

import unittest

from app.early_math_catalog import khan_url_for
from app.ui_arithmetic import KHAN_URL_BY_SKILL, khan_url_for_selection, lesson_link_state
from app.ui_settings import UiSettings


class KhanSubskillLinkTests(unittest.TestCase):
    def test_subskill_url_lookup_uses_catalog_mapping(self) -> None:
        expected = khan_url_for("divide", "Remainders")
        self.assertEqual(khan_url_for_selection("divide", "Remainders"), expected)
        self.assertTrue(expected.startswith("https://www.khanacademy.org/"))

    def test_skill_fallback_still_works(self) -> None:
        self.assertEqual(khan_url_for_selection("algebra_1", "Any"), KHAN_URL_BY_SKILL["algebra_1"])
        self.assertEqual(khan_url_for_selection("counting", None), KHAN_URL_BY_SKILL["counting"])

    def test_algebra_1_quadratic_formula_link_is_parent_controlled(self) -> None:
        url = khan_url_for_selection("algebra_1", "Quadratic formula")
        self.assertIn("quadratic-formula", url)

        disabled = lesson_link_state(
            "algebra_1",
            "Quadratic formula",
            UiSettings(show_external_links=False, enforce_offline_mode=False),
        )
        enabled = lesson_link_state(
            "algebra_1",
            "Quadratic formula",
            UiSettings(show_external_links=True, enforce_offline_mode=False),
        )

        self.assertFalse(disabled.enabled)
        self.assertTrue(enabled.enabled)
        self.assertEqual(enabled.url, url)

    def test_algebra_1_slope_from_points_link_is_parent_controlled(self) -> None:
        url = khan_url_for_selection("algebra_1", "Slope from points")
        self.assertIn("linear-equations-graphs", url)
        self.assertIn("slope-from-two-points", url)

        disabled = lesson_link_state(
            "algebra_1",
            "Slope from points",
            UiSettings(show_external_links=False, enforce_offline_mode=False),
        )
        enabled = lesson_link_state(
            "algebra_1",
            "Slope from points",
            UiSettings(show_external_links=True, enforce_offline_mode=False),
        )

        self.assertFalse(disabled.enabled)
        self.assertTrue(enabled.enabled)
        self.assertEqual(enabled.url, url)

    def test_algebra_1_slope_intercept_form_link_is_parent_controlled(self) -> None:
        url = khan_url_for_selection("algebra_1", "Slope-intercept form")
        self.assertIn("intro-to-slope-intercept-form", url)
        self.assertIn("slope-from-an-equation", url)

        offline = lesson_link_state(
            "algebra_1",
            "Slope-intercept form",
            UiSettings(show_external_links=True, enforce_offline_mode=True),
        )
        enabled = lesson_link_state(
            "algebra_1",
            "Slope-intercept form",
            UiSettings(show_external_links=True, enforce_offline_mode=False),
        )

        self.assertFalse(offline.enabled)
        self.assertTrue(enabled.enabled)
        self.assertEqual(enabled.url, url)

    def test_algebra_1_graphing_linear_inequalities_link_is_parent_controlled(self) -> None:
        url = khan_url_for_selection("algebra_1", "Graphing linear inequalities")
        self.assertIn("graphing-two-variable-inequalities", url)
        self.assertIn("graphing_inequalities_2", url)

        disabled = lesson_link_state(
            "algebra_1",
            "Graphing linear inequalities",
            UiSettings(show_external_links=False, enforce_offline_mode=False),
        )
        enabled = lesson_link_state(
            "algebra_1",
            "Graphing linear inequalities",
            UiSettings(show_external_links=True, enforce_offline_mode=False),
        )

        self.assertFalse(disabled.enabled)
        self.assertTrue(enabled.enabled)
        self.assertEqual(enabled.url, url)

    def test_algebra_1_systems_by_substitution_link_is_parent_controlled(self) -> None:
        url = khan_url_for_selection("algebra_1", "Systems by substitution")
        self.assertIn("systems-of-equations", url)
        self.assertIn("substitution", url)

        disabled = lesson_link_state(
            "algebra_1",
            "Systems by substitution",
            UiSettings(show_external_links=False, enforce_offline_mode=False),
        )
        enabled = lesson_link_state(
            "algebra_1",
            "Systems by substitution",
            UiSettings(show_external_links=True, enforce_offline_mode=False),
        )

        self.assertFalse(disabled.enabled)
        self.assertTrue(enabled.enabled)
        self.assertEqual(enabled.url, url)

    def test_algebra_1_systems_by_elimination_link_is_parent_controlled(self) -> None:
        url = khan_url_for_selection("algebra_1", "Systems by elimination")
        self.assertIn("systems-of-equations", url)
        self.assertIn("elimination", url)

        offline = lesson_link_state(
            "algebra_1",
            "Systems by elimination",
            UiSettings(show_external_links=True, enforce_offline_mode=True),
        )
        enabled = lesson_link_state(
            "algebra_1",
            "Systems by elimination",
            UiSettings(show_external_links=True, enforce_offline_mode=False),
        )

        self.assertFalse(offline.enabled)
        self.assertTrue(enabled.enabled)
        self.assertEqual(enabled.url, url)

    def test_algebra_1_graphing_systems_link_is_parent_controlled(self) -> None:
        url = khan_url_for_selection("algebra_1", "Graphing systems and intersections")
        self.assertIn("systems-of-equations", url)
        self.assertIn("solving-systems-graphically", url)

        disabled = lesson_link_state(
            "algebra_1",
            "Graphing systems and intersections",
            UiSettings(show_external_links=False, enforce_offline_mode=False),
        )
        enabled = lesson_link_state(
            "algebra_1",
            "Graphing systems and intersections",
            UiSettings(show_external_links=True, enforce_offline_mode=False),
        )

        self.assertFalse(disabled.enabled)
        self.assertTrue(enabled.enabled)
        self.assertEqual(enabled.url, url)

    def test_algebra_1_polynomial_arithmetic_link_is_parent_controlled(self) -> None:
        url = khan_url_for_selection("algebra_1", "Polynomial arithmetic")
        self.assertIn("alg-polynomials", url)

        disabled = lesson_link_state(
            "algebra_1",
            "Polynomial arithmetic",
            UiSettings(show_external_links=False, enforce_offline_mode=False),
        )
        enabled = lesson_link_state(
            "algebra_1",
            "Polynomial arithmetic",
            UiSettings(show_external_links=True, enforce_offline_mode=False),
        )

        self.assertFalse(disabled.enabled)
        self.assertTrue(enabled.enabled)
        self.assertEqual(enabled.url, url)

    def test_algebra_1_factoring_basics_link_is_parent_controlled(self) -> None:
        url = khan_url_for_selection("algebra_1", "Factoring basics")
        self.assertIn("quadratics-multiplying-factoring", url)
        self.assertIn("factoring_polynomials_1", url)

        offline = lesson_link_state(
            "algebra_1",
            "Factoring basics",
            UiSettings(show_external_links=True, enforce_offline_mode=True),
        )
        enabled = lesson_link_state(
            "algebra_1",
            "Factoring basics",
            UiSettings(show_external_links=True, enforce_offline_mode=False),
        )

        self.assertFalse(offline.enabled)
        self.assertTrue(enabled.enabled)
        self.assertEqual(enabled.url, url)

    def test_algebra_1_quadratic_grouping_link_is_parent_controlled(self) -> None:
        url = khan_url_for_selection("algebra_1", "Quadratic factoring by grouping")
        self.assertIn("factor-quadratics-grouping", url)
        self.assertIn("factoring_polynomials_by_grouping_1", url)

        disabled = lesson_link_state(
            "algebra_1",
            "Quadratic factoring by grouping",
            UiSettings(show_external_links=False, enforce_offline_mode=False),
        )
        enabled = lesson_link_state(
            "algebra_1",
            "Quadratic factoring by grouping",
            UiSettings(show_external_links=True, enforce_offline_mode=False),
        )

        self.assertFalse(disabled.enabled)
        self.assertTrue(enabled.enabled)
        self.assertEqual(enabled.url, url)

    def test_algebra_1_difference_of_squares_link_is_parent_controlled(self) -> None:
        url = khan_url_for_selection("algebra_1", "Difference of squares")
        self.assertIn("factor-difference-squares", url)
        self.assertIn("factoring_difference_of_squares_2", url)

        offline = lesson_link_state(
            "algebra_1",
            "Difference of squares",
            UiSettings(show_external_links=True, enforce_offline_mode=True),
        )
        enabled = lesson_link_state(
            "algebra_1",
            "Difference of squares",
            UiSettings(show_external_links=True, enforce_offline_mode=False),
        )

        self.assertFalse(offline.enabled)
        self.assertTrue(enabled.enabled)
        self.assertEqual(enabled.url, url)

    def test_algebra_1_completing_square_link_is_parent_controlled(self) -> None:
        url = khan_url_for_selection("algebra_1", "Completing the square")
        self.assertIn("completing_the_square", url)

        offline = lesson_link_state(
            "algebra_1",
            "Completing the square",
            UiSettings(show_external_links=True, enforce_offline_mode=True),
        )
        enabled = lesson_link_state(
            "algebra_1",
            "Completing the square",
            UiSettings(show_external_links=True, enforce_offline_mode=False),
        )

        self.assertFalse(offline.enabled)
        self.assertTrue(enabled.enabled)
        self.assertEqual(enabled.url, url)

    def test_disabled_or_offline_states_block_links(self) -> None:
        disabled = lesson_link_state(
            "divide",
            "Remainders",
            UiSettings(show_external_links=False, enforce_offline_mode=False),
        )
        offline = lesson_link_state(
            "divide",
            "Remainders",
            UiSettings(show_external_links=True, enforce_offline_mode=True),
        )
        enabled = lesson_link_state(
            "divide",
            "Remainders",
            UiSettings(show_external_links=True, enforce_offline_mode=False),
        )

        self.assertFalse(disabled.enabled)
        self.assertIn("disabled", disabled.message.lower())
        self.assertFalse(offline.enabled)
        self.assertIn("offline mode", offline.message.lower())
        self.assertTrue(enabled.enabled)
        self.assertEqual(enabled.url, khan_url_for("divide", "Remainders"))


if __name__ == "__main__":
    unittest.main()
