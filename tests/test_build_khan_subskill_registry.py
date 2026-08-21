from __future__ import annotations

import unittest

from scripts.build_khan_subskill_registry import build_registry


class KhanRegistryTests(unittest.TestCase):
    def test_registry_has_entries_and_queries(self) -> None:
        entries = build_registry(include_legacy=False)
        self.assertGreater(len(entries), 0)
        self.assertTrue(all(item.khan_query.strip() for item in entries))
        self.assertTrue(all(item.skill.strip() for item in entries))

    def test_registry_excludes_legacy_by_default(self) -> None:
        entries = build_registry(include_legacy=False)
        skills = {item.skill for item in entries}
        self.assertNotIn("calculus_slope", skills)

    def test_registry_can_include_legacy(self) -> None:
        entries = build_registry(include_legacy=True)
        skills = {item.skill for item in entries}
        self.assertIn("calculus_slope", skills)

    def test_registry_maps_algebra_1_quadratic_formula(self) -> None:
        entries = build_registry(include_legacy=False)
        entry = next(
            item
            for item in entries
            if item.skill == "algebra_1" and item.subskill == "Quadratic formula"
        )

        self.assertIn("quadratic formula", entry.khan_query)
        self.assertIn("quadratic-formula", entry.khan_assignable_url)

    def test_registry_maps_algebra_1_slope_from_points(self) -> None:
        entries = build_registry(include_legacy=False)
        entry = next(
            item
            for item in entries
            if item.skill == "algebra_1" and item.subskill == "Slope from points"
        )

        self.assertIn("slope from points", entry.khan_query)
        self.assertIn("slope-from-two-points", entry.khan_assignable_url)

    def test_registry_maps_algebra_1_slope_intercept_form(self) -> None:
        entries = build_registry(include_legacy=False)
        entry = next(
            item
            for item in entries
            if item.skill == "algebra_1" and item.subskill == "Slope-intercept form"
        )

        self.assertIn("slope-intercept form", entry.khan_query)
        self.assertIn("intro-to-slope-intercept-form", entry.khan_assignable_url)

    def test_registry_maps_algebra_1_graphing_linear_inequalities(self) -> None:
        entries = build_registry(include_legacy=False)
        entry = next(
            item
            for item in entries
            if item.skill == "algebra_1" and item.subskill == "Graphing linear inequalities"
        )

        self.assertIn("graphing linear inequalities", entry.khan_query)
        self.assertIn("graphing-two-variable-inequalities", entry.khan_assignable_url)

    def test_registry_maps_algebra_1_systems_by_substitution(self) -> None:
        entries = build_registry(include_legacy=False)
        entry = next(
            item
            for item in entries
            if item.skill == "algebra_1" and item.subskill == "Systems by substitution"
        )

        self.assertIn("systems by substitution", entry.khan_query)
        self.assertIn("systems-of-equations", entry.khan_assignable_url)
        self.assertIn("substitution", entry.khan_assignable_url)

    def test_registry_maps_algebra_1_systems_by_elimination(self) -> None:
        entries = build_registry(include_legacy=False)
        entry = next(
            item
            for item in entries
            if item.skill == "algebra_1" and item.subskill == "Systems by elimination"
        )

        self.assertIn("systems by elimination", entry.khan_query)
        self.assertIn("systems-of-equations", entry.khan_assignable_url)
        self.assertIn("elimination", entry.khan_assignable_url)

    def test_registry_maps_algebra_1_graphing_systems(self) -> None:
        entries = build_registry(include_legacy=False)
        entry = next(
            item
            for item in entries
            if item.skill == "algebra_1" and item.subskill == "Graphing systems and intersections"
        )

        self.assertIn("graphing systems and intersections", entry.khan_query)
        self.assertIn("systems-of-equations", entry.khan_assignable_url)
        self.assertIn("solving-systems-graphically", entry.khan_assignable_url)

    def test_registry_maps_algebra_1_polynomial_arithmetic(self) -> None:
        entries = build_registry(include_legacy=False)
        entry = next(
            item
            for item in entries
            if item.skill == "algebra_1" and item.subskill == "Polynomial arithmetic"
        )

        self.assertIn("polynomial arithmetic", entry.khan_query)
        self.assertIn("alg-polynomials", entry.khan_assignable_url)

    def test_registry_maps_algebra_1_factoring_basics(self) -> None:
        entries = build_registry(include_legacy=False)
        entry = next(
            item
            for item in entries
            if item.skill == "algebra_1" and item.subskill == "Factoring basics"
        )

        self.assertIn("factoring basics", entry.khan_query)
        self.assertIn("quadratics-multiplying-factoring", entry.khan_assignable_url)
        self.assertIn("factoring_polynomials_1", entry.khan_assignable_url)

    def test_registry_maps_algebra_1_quadratic_grouping(self) -> None:
        entries = build_registry(include_legacy=False)
        entry = next(
            item
            for item in entries
            if item.skill == "algebra_1" and item.subskill == "Quadratic factoring by grouping"
        )

        self.assertIn("quadratic factoring by grouping", entry.khan_query)
        self.assertIn("factor-quadratics-grouping", entry.khan_assignable_url)
        self.assertIn("factoring_polynomials_by_grouping_1", entry.khan_assignable_url)

    def test_registry_maps_algebra_1_difference_of_squares(self) -> None:
        entries = build_registry(include_legacy=False)
        entry = next(
            item
            for item in entries
            if item.skill == "algebra_1" and item.subskill == "Difference of squares"
        )

        self.assertIn("difference of squares", entry.khan_query)
        self.assertIn("factor-difference-squares", entry.khan_assignable_url)
        self.assertIn("factoring_difference_of_squares_2", entry.khan_assignable_url)

    def test_registry_maps_algebra_1_completing_the_square(self) -> None:
        entries = build_registry(include_legacy=False)
        entry = next(
            item
            for item in entries
            if item.skill == "algebra_1" and item.subskill == "Completing the square"
        )

        self.assertIn("completing the square", entry.khan_query)
        self.assertIn("completing_the_square", entry.khan_assignable_url)


if __name__ == "__main__":
    unittest.main()
