from __future__ import annotations

import unittest

from app.content_depth.cumulative import (
    build_algebra1_cumulative_quiz,
    build_texas_cumulative_quiz,
    evaluate_cumulative_quiz,
)
from app.content_depth.models import ReasoningKind
from app.content_depth.units import (
    ALGEBRA_1_UNITS,
    cumulative_mix,
    texas_companion_units,
    texas_cumulative_checks,
    texas_question_count,
)
from app.skill_graph import subskills_for
from app.summer_program_defs import TASK_TARGETS


class ContentDepthUnitTests(unittest.TestCase):
    def test_question_lengths_and_50_30_20_composition(self) -> None:
        self.assertEqual((texas_question_count(1), texas_question_count(3), texas_question_count(6)), (8, 10, 12))
        self.assertEqual(cumulative_mix(10), type(cumulative_mix(10))(5, 3, 2))
        quiz = build_texas_cumulative_quiz(3, 1, seed=9)
        self.assertEqual(len(quiz.questions), 10)
        self.assertEqual(quiz.mix, cumulative_mix(10))
        multiply_count = sum(q.skill == "multiply" for q in quiz.questions)
        place_value_count = sum(q.skill == "place_value" for q in quiz.questions)
        self.assertEqual(multiply_count + place_value_count, 10)
        self.assertGreaterEqual(multiply_count, quiz.mix.current)
        self.assertGreaterEqual(place_value_count, quiz.mix.earlier)
        self.assertTrue(
            all(
                q.reasoning_kind in {
                    ReasoningKind.LEGACY,
                    ReasoningKind.PROCEDURAL,
                    ReasoningKind.APPLICATION,
                }
                for q in quiz.questions
            )
        )
        self.assertTrue(all(q.scaffold_steps is None for q in quiz.questions))

    def test_texas_goals_become_ordered_units_and_checks(self) -> None:
        units = texas_companion_units(2)
        checks = texas_cumulative_checks(2)
        self.assertEqual(len(units), 10)
        self.assertEqual([unit.code for unit in units[:2]], ["g2_place_value", "g2_fraction_units"])
        self.assertEqual(len(checks), 5)
        self.assertEqual(checks[-1].target_codes, tuple(unit.code for unit in units))

    def test_algebra_one_units_cover_every_subskill_once(self) -> None:
        listed = [subskill for unit in ALGEBRA_1_UNITS for subskill in unit.subskills]
        self.assertEqual(len(ALGEBRA_1_UNITS), 7)
        self.assertEqual(len(listed), len(set(listed)))
        self.assertEqual(set(listed), set(subskills_for("algebra_1")))
        quiz = build_algebra1_cumulative_quiz(3, seed=3)
        self.assertEqual(len(quiz.questions), 12)
        self.assertEqual(quiz.mix, cumulative_mix(12))
        self.assertLessEqual(sum(q.reasoning_kind is ReasoningKind.APPLICATION for q in quiz.questions), 2)

    def test_below_80_is_soft_review_and_prealgebra_exit_stays_85(self) -> None:
        quiz = build_texas_cumulative_quiz(1, 1, seed=2)
        result = evaluate_cumulative_quiz(quiz, (True, True, True, True, True, True, False, False))
        self.assertEqual(result.score_pct, 75.0)
        self.assertFalse(result.passed)
        self.assertTrue(result.recommended_review)
        self.assertEqual(TASK_TARGETS["exit_assessment"], 85.0)


if __name__ == "__main__":
    unittest.main()
