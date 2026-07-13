from __future__ import annotations

import re
import unittest

from app.quiz_engine import generate_question
from app.texas_grade_goals import content_gap_goals, texas_grade_plan, texas_grade_plans


EXPECTED_CORE_TEKS_ROOTS: dict[int, tuple[str, ...]] = {
    1: ("1.2", "1.3", "1.4", "1.5", "1.6", "1.7", "1.8", "1.9"),
    2: ("2.2", "2.3", "2.4", "2.5", "2.6", "2.7", "2.8", "2.9", "2.10", "2.11"),
    3: ("3.2", "3.3", "3.4", "3.5", "3.6", "3.7", "3.8", "3.9"),
    4: ("4.2", "4.3", "4.4", "4.5", "4.6", "4.7", "4.8", "4.9", "4.10"),
    5: ("5.2", "5.3", "5.4", "5.5", "5.6", "5.7", "5.8", "5.9", "5.10"),
    6: ("6.2", "6.3", "6.4", "6.5", "6.6", "6.7", "6.8", "6.9", "6.10", "6.11", "6.12", "6.13", "6.14"),
    7: ("7.2", "7.3", "7.4", "7.5", "7.6", "7.7", "7.8", "7.9", "7.10", "7.11", "7.12", "7.13"),
}


def _root(ref: str) -> str:
    match = re.match(r"^(\d+\.\d+)", ref)
    if match is None:
        raise AssertionError(f"Bad TEKS reference format: {ref}")
    return match.group(1)


class TexasStandardsAuditTests(unittest.TestCase):
    def test_every_core_teks_root_has_a_non_stretch_quiz_ready_goal(self) -> None:
        for plan in texas_grade_plans():
            covered = {
                _root(ref)
                for goal in plan.goals
                if goal.quiz_ready and not goal.stretch
                for ref in goal.standard_refs
            }
            with self.subTest(grade=plan.grade):
                self.assertEqual(set(EXPECTED_CORE_TEKS_ROOTS[plan.grade]), covered)

    def test_no_grade_one_through_seven_content_gaps_remain(self) -> None:
        for grade in range(1, 8):
            with self.subTest(grade=grade):
                self.assertEqual((), content_gap_goals(grade))

    def test_every_non_stretch_goal_subskill_can_generate_a_question(self) -> None:
        for plan in texas_grade_plans():
            for goal in plan.goals:
                if goal.stretch:
                    continue
                self.assertIsNotNone(goal.skill)
                assert goal.skill is not None
                for subskill in goal.subskills:
                    with self.subTest(grade=plan.grade, goal=goal.code, subskill=subskill):
                        question = generate_question(goal.skill, goal.quiz_level, "typed", subskill=subskill)
                        self.assertEqual(goal.skill, question.skill)
                        self.assertTrue(question.correct_answer)

    def test_fall_assessment_rows_include_newly_audited_grade_two_and_three_roots(self) -> None:
        grade_two = {goal.code: goal for goal in texas_grade_plan(2).goals}
        grade_three = {goal.code: goal for goal in texas_grade_plan(3).goals}

        self.assertEqual(("2.3",), grade_two["g2_fraction_units"].standard_refs)
        self.assertEqual("geometry_shapes", grade_two["g2_fraction_units"].skill)
        self.assertIn("Equal shares of shapes", grade_two["g2_fraction_units"].subskills)
        self.assertEqual(("3.2",), grade_three["g3_place_value"].standard_refs)
        self.assertEqual("place_value", grade_three["g3_place_value"].skill)


if __name__ == "__main__":
    unittest.main()
