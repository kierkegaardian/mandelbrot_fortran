from __future__ import annotations

import unittest

from app.skill_graph import skills_in_track, subskills_for


class SkillGraphTrackTests(unittest.TestCase):
    def test_calculus_track_has_three_courses(self) -> None:
        self.assertEqual(skills_in_track("Calculus"), ("calculus_1", "calculus_2", "calculus_3"))

    def test_algebra_track_has_linear_to_algebra2(self) -> None:
        self.assertEqual(skills_in_track("Algebra"), ("algebra_linear", "algebra_1", "algebra_2"))

    def test_statistics_track_has_composite_statistics_skill(self) -> None:
        stats = skills_in_track("Statistics / Probability")
        self.assertIn("data_analysis", stats)
        self.assertIn("statistics", stats)

    def test_algebra_1_has_khan_style_subskills(self) -> None:
        subskills = subskills_for("algebra_1")
        self.assertGreaterEqual(len(subskills), 12)
        self.assertIn("Solving equations & inequalities", subskills)
        self.assertIn("Slope from points", subskills)
        self.assertIn("Slope-intercept form", subskills)
        self.assertIn("Graphing linear inequalities", subskills)
        self.assertIn("Systems by substitution", subskills)
        self.assertIn("Systems by elimination", subskills)
        self.assertIn("Graphing systems and intersections", subskills)
        self.assertIn("Function transformations", subskills)
        self.assertIn("Radicals and rational exponents", subskills)
        self.assertIn("Polynomial arithmetic", subskills)
        self.assertIn("Factoring basics", subskills)
        self.assertIn("Quadratic factoring by grouping", subskills)
        self.assertIn("Difference of squares", subskills)
        self.assertIn("Quadratic functions & equations", subskills)
        self.assertIn("Completing the square", subskills)
        self.assertIn("Quadratic formula", subskills)

    def test_algebra_linear_has_broad_foundations_subskills(self) -> None:
        subskills = subskills_for("algebra_linear")
        self.assertGreaterEqual(len(subskills), 10)
        self.assertIn("Systems of linear equations", subskills)
        self.assertIn("Word problems with linear models", subskills)

    def test_pre_algebra_has_foundation_subskills(self) -> None:
        subskills = subskills_for("pre_algebra")
        self.assertGreaterEqual(len(subskills), 8)
        self.assertIn("Integer and fraction fluency", subskills)
        self.assertIn("One-step equations", subskills)
        self.assertIn("Two-step equations and inequalities", subskills)
        self.assertIn("Ratios, rates, and proportional relationships", subskills)
        self.assertIn("Exponents, roots, and scientific notation", subskills)

    def test_algebra_2_has_khan_style_subskills(self) -> None:
        subskills = subskills_for("algebra_2")
        self.assertGreaterEqual(len(subskills), 10)
        self.assertIn("Polynomial arithmetic", subskills)
        self.assertIn("Rational functions", subskills)

    def test_geometry_has_full_course_style_subskills(self) -> None:
        subskills = subskills_for("geometry_area")
        self.assertGreaterEqual(len(subskills), 10)
        self.assertIn("Transformations and congruence", subskills)
        self.assertIn("Analytic geometry and coordinate proofs", subskills)

    def test_precalculus_track_skill_has_broad_subskills(self) -> None:
        subskills = subskills_for("trig_right_triangle")
        self.assertGreaterEqual(len(subskills), 8)
        self.assertIn("Right-triangle trig ratios", subskills)
        self.assertIn("Unit circle trig values", subskills)
        self.assertIn("Trig functions and graphs", subskills)
        self.assertIn("Trig identities", subskills)
        self.assertIn("Inverse trig", subskills)
        self.assertIn("Vectors", subskills)
        self.assertIn("Matrices and linear transformations", subskills)
        self.assertIn("Polar coordinates", subskills)

    def test_statistics_composite_includes_inference_subskills(self) -> None:
        subskills = subskills_for("statistics")
        self.assertGreaterEqual(len(subskills), 10)
        self.assertIn("Integrated descriptive statistics and probability", subskills)
        self.assertIn("Data collection and study design", subskills)
        self.assertIn("Distributions and standard deviation", subskills)
        self.assertIn("Probability rules", subskills)
        self.assertIn("Combinatorics", subskills)
        self.assertIn("Expected value", subskills)
        self.assertIn("Sampling and margin of error", subskills)
        self.assertIn("Confidence intervals", subskills)
        self.assertIn("Hypothesis tests", subskills)
        self.assertIn("Correlation and regression", subskills)

    def test_test_prep_tracks_match_collapsed_taxonomy(self) -> None:
        self.assertEqual(
            subskills_for("sat_math"),
            (
                "SAT algebra modeling",
                "SAT linear relationships",
                "SAT percent and data",
                "SAT statistics",
                "SAT mixed-domain",
            ),
        )
        self.assertEqual(
            subskills_for("psat_math"),
            (
                "PSAT algebra modeling",
                "PSAT equation solving",
                "PSAT geometry",
                "PSAT percentages",
                "PSAT mixed-domain",
            ),
        )
        self.assertEqual(
            subskills_for("gre_quant"),
            (
                "GRE quantitative comparison",
                "GRE ratios and proportions",
                "GRE percent reasoning",
                "GRE data interpretation",
            ),
        )

    def test_calculus_tracks_have_broad_subskills(self) -> None:
        self.assertGreaterEqual(len(subskills_for("calculus_1")), 5)
        self.assertIn("Limits and continuity", subskills_for("calculus_1"))
        self.assertIn("Derivative rules", subskills_for("calculus_1"))
        self.assertIn("Derivative as slope and velocity", subskills_for("calculus_1"))
        self.assertIn("Optimization", subskills_for("calculus_1"))

        self.assertGreaterEqual(len(subskills_for("calculus_2")), 4)
        self.assertIn("Accumulation and area under curves", subskills_for("calculus_2"))
        self.assertIn("Basic integration techniques", subskills_for("calculus_2"))
        self.assertIn("Area between curves", subskills_for("calculus_2"))

        self.assertGreaterEqual(len(subskills_for("calculus_3")), 3)
        self.assertIn("Gradient and directional change", subskills_for("calculus_3"))
        self.assertIn("Multivariable optimization", subskills_for("calculus_3"))

    def test_statistics_component_skills_match_collapsed_taxonomy(self) -> None:
        self.assertEqual(
            subskills_for("stats_percent"),
            ("Percent change", "Reverse percent change", "Percent word problems"),
        )
        self.assertEqual(subskills_for("stats_mean"), ("Mean", "Mean from display"))
        self.assertEqual(subskills_for("stats_probability"), ("Probability models",))


if __name__ == "__main__":
    unittest.main()
