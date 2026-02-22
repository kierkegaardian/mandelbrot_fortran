from __future__ import annotations

import unittest

from app.skill_graph import skills_in_track


class SkillGraphTrackTests(unittest.TestCase):
    def test_calculus_track_has_three_courses(self) -> None:
        self.assertEqual(skills_in_track("Calculus"), ("calculus_1", "calculus_2", "calculus_3"))

    def test_algebra_track_has_linear_to_algebra2(self) -> None:
        self.assertEqual(skills_in_track("Algebra"), ("algebra_linear", "algebra_1", "algebra_2"))

    def test_statistics_track_has_composite_statistics_skill(self) -> None:
        stats = skills_in_track("Statistics / Probability")
        self.assertIn("statistics", stats)


if __name__ == "__main__":
    unittest.main()
