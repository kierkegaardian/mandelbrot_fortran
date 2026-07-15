from __future__ import annotations

import unittest

from app.explanations import Explanation
from app.quiz_engine import Question
from app.quiz_recovery import (
    build_mistake_recovery_text,
    should_offer_mistake_recovery,
)


class QuizRecoveryTests(unittest.TestCase):
    def test_recovery_boundary_excludes_historical_and_non_summer_quizzes(self) -> None:
        question = Question(
            skill="add_subtract",
            prompt="8 + 5 = ?",
            correct_answer="13",
            explanation="Add.",
            choices=None,
            visual=None,
        )
        self.assertTrue(
            should_offer_mistake_recovery(
                summer_mode=True, strategy="focused", question=question
            )
        )
        self.assertFalse(
            should_offer_mistake_recovery(
                summer_mode=False, strategy="focused", question=question
            )
        )
        self.assertFalse(
            should_offer_mistake_recovery(
                summer_mode=True, strategy="historical_practice", question=question
            )
        )

    def test_recovery_copy_includes_mistake_redo_and_mental_model(self) -> None:
        explanation = Explanation(
            how_short="",
            how_long="",
            why_short="",
            why_long="",
            mental_model="Think about groups.",
            common_mistake="Mixing up the groups.",
            try_this="Draw 3 groups of 4.",
        )
        text = build_mistake_recovery_text(explanation, phase="redo")
        self.assertIn("Why this mistake happens: Mixing up the groups.", text)
        self.assertIn("Guided redo: Draw 3 groups of 4.", text)
        self.assertIn("Mental model: Think about groups.", text)


if __name__ == "__main__":
    unittest.main()
