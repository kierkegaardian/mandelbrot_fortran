from __future__ import annotations

import unittest

from app.quiz_engine import Question
from app.ui_quiz import _subskill_for_question


class SubskillMappingTests(unittest.TestCase):
    def test_explicit_subskill_is_used_for_mastery(self) -> None:
        question = Question(
            skill="calculus_1",
            prompt="Find the slope of the line through (1, 2) and (3, 6).",
            correct_answer="2",
            explanation="",
            choices=None,
            visual=None,
            subskill="Average rate of change between two points",
            question_label="Core",
            mode="expression",
        )
        self.assertEqual(_subskill_for_question(question), "Average rate of change between two points")

    def test_missing_subskill_stays_untracked(self) -> None:
        question = Question(
            skill="add_subtract",
            prompt="8 + 5 = ?",
            correct_answer="13",
            explanation="",
            choices=None,
            visual=None,
            question_label="Core",
            mode="expression",
        )
        self.assertIsNone(_subskill_for_question(question))


if __name__ == "__main__":
    unittest.main()
