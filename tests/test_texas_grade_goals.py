from __future__ import annotations

import unittest

from app.skill_graph import SKILL_ORDER, subskills_for
from app.texas_grade_goals import (
    ELEMENTARY_TEKS_URL,
    MIDDLE_SCHOOL_TEKS_URL,
    content_gap_goals,
    quiz_ready_goals,
    texas_grade_plan,
    texas_grade_plans,
)


class TexasGradeGoalTests(unittest.TestCase):
    def test_catalog_covers_grades_one_through_seven(self) -> None:
        self.assertEqual(tuple(range(1, 8)), tuple(plan.grade for plan in texas_grade_plans()))

    def test_source_urls_follow_elementary_and_middle_school_split(self) -> None:
        for grade in range(1, 6):
            self.assertEqual(ELEMENTARY_TEKS_URL, texas_grade_plan(grade).source_url)
        for grade in range(6, 8):
            self.assertEqual(MIDDLE_SCHOOL_TEKS_URL, texas_grade_plan(grade).source_url)

    def test_every_grade_has_quiz_ready_goals_and_gap_tracking(self) -> None:
        for grade in range(1, 8):
            with self.subTest(grade=grade):
                self.assertGreaterEqual(len(quiz_ready_goals(grade)), 3)
                self.assertGreaterEqual(len(texas_grade_plan(grade).focal_areas), 3)
                self.assertEqual(
                    len(texas_grade_plan(grade).goals),
                    len(quiz_ready_goals(grade)) + len(content_gap_goals(grade)),
                )

    def test_goal_references_match_grade_level(self) -> None:
        for plan in texas_grade_plans():
            for goal in plan.goals:
                with self.subTest(grade=plan.grade, goal=goal.code):
                    self.assertTrue(goal.standard_refs)
                    self.assertTrue(all(ref.startswith(f"{plan.grade}.") for ref in goal.standard_refs))

    def test_mapped_goals_use_existing_skills_and_subskills(self) -> None:
        known_skills = set(SKILL_ORDER)
        for plan in texas_grade_plans():
            for goal in quiz_ready_goals(plan.grade):
                with self.subTest(grade=plan.grade, goal=goal.code):
                    self.assertIsNotNone(goal.skill)
                    assert goal.skill is not None
                    self.assertIn(goal.skill, known_skills)
                    available = set(subskills_for(goal.skill))
                    self.assertTrue(available)
                    for subskill in goal.subskills:
                        self.assertIn(subskill, available)

    def test_stretch_goals_keep_above_grade_progress_available(self) -> None:
        stretch = [goal for plan in texas_grade_plans() for goal in plan.goals if goal.stretch]
        self.assertGreaterEqual(len(stretch), 2)
        self.assertTrue(any(goal.skill == "algebra_1" for goal in stretch))


if __name__ == "__main__":
    unittest.main()
