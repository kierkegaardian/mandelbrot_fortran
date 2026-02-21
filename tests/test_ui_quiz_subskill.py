from __future__ import annotations

import unittest

from app.quiz_engine import Question
from app.ui_quiz import _subskill_for_question


class SubskillMappingTests(unittest.TestCase):
    def test_same_template_stable_across_labels(self) -> None:
        core = Question(
            skill="add_subtract",
            prompt="8 + 5 = ?",
            correct_answer="13",
            explanation="",
            choices=None,
            visual=None,
            template_id=42,
            question_label="Core",
            mode="expression",
        )
        prereq = Question(
            skill="add_subtract",
            prompt="Story context (src): text\nQuestion: 8 + 5 = ?",
            correct_answer="13",
            explanation="",
            choices=None,
            visual=None,
            template_id=42,
            question_label="Prereq",
            mode="word",
        )
        review = Question(
            skill="add_subtract",
            prompt="Story context (src): other text\nQuestion: 8 + 5 = ?",
            correct_answer="13",
            explanation="",
            choices=None,
            visual=None,
            template_id=42,
            question_label="Review",
            mode="word",
        )
        self.assertEqual(_subskill_for_question(core), _subskill_for_question(prereq))
        self.assertEqual(_subskill_for_question(prereq), _subskill_for_question(review))

    def test_non_template_wrapper_and_plain_prompt_map_same(self) -> None:
        wrapped = Question(
            skill="add_subtract",
            prompt="Story context (source): A child has 8 apples and gets 5 more.\nQuestion: 8 + 5 = ?",
            correct_answer="13",
            explanation="",
            choices=None,
            visual=None,
            template_id=None,
            question_label="Core",
            mode="word",
        )
        plain = Question(
            skill="add_subtract",
            prompt="8 + 5 = ?",
            correct_answer="13",
            explanation="",
            choices=None,
            visual=None,
            template_id=None,
            question_label="Review",
            mode="expression",
        )
        self.assertEqual(_subskill_for_question(wrapped), _subskill_for_question(plain))


if __name__ == "__main__":
    unittest.main()
