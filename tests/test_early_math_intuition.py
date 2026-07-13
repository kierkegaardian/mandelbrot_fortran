from __future__ import annotations

import unittest

from app.early_math_catalog import early_math_specs
from app.explanations import ARITHMETIC_MODE_EXPLANATIONS, explanation_for
from app.quiz_engine import Question
from app.quiz_flow import question_intuition_preview, show_intuition


class _FakeStringVar:
    def __init__(self) -> None:
        self.value = ""

    def get(self) -> str:
        return self.value

    def set(self, value: str) -> None:
        self.value = value


class _FakePanel:
    def __init__(self, question: Question, *, child: bool = True) -> None:
        self._questions = [question]
        self._index = 0
        self.intuition_var = _FakeStringVar()
        self.child = child

    def _is_child_profile(self) -> bool:
        return self.child

    def _subskill_for_question(self, question: Question) -> str | None:
        return question.subskill


class EarlyMathIntuitionTests(unittest.TestCase):
    def test_every_early_math_subskill_has_complete_intuition(self) -> None:
        for spec in early_math_specs():
            with self.subTest(skill=spec.skill, subskill=spec.subskill):
                explanation = explanation_for(spec.skill, spec.subskill)
                self.assertTrue(explanation.mental_model.strip())
                self.assertTrue(explanation.common_mistake.strip())
                self.assertTrue(explanation.try_this.strip())

    def test_show_intuition_prefers_subskill_specific_content(self) -> None:
        question = Question(
            skill="place_value",
            prompt="Compare 3.4 and 3.09.",
            correct_answer="3.4",
            explanation="",
            choices=None,
            visual=None,
            subskill="Decimal place value and comparison",
        )
        panel = _FakePanel(question)

        show_intuition(panel)

        text = panel.intuition_var.get()
        skill_level = ARITHMETIC_MODE_EXPLANATIONS["place_value"]
        subskill_level = explanation_for("place_value", "Decimal place value and comparison")
        self.assertIn("Subskill: Decimal place value and comparison", text)
        self.assertIn(subskill_level.mental_model, text)
        self.assertIn(subskill_level.common_mistake, text)
        self.assertIn(subskill_level.try_this, text)
        self.assertNotEqual(skill_level.mental_model, subskill_level.mental_model)

    def test_child_question_preview_surfaces_subskill_mental_model(self) -> None:
        question = Question(
            skill="place_value",
            prompt="Compare 3.4 and 3.09.",
            correct_answer="3.4",
            explanation="",
            choices=None,
            visual=None,
            subskill="Decimal place value and comparison",
        )
        panel = _FakePanel(question)

        text = question_intuition_preview(panel, question)

        subskill_level = explanation_for("place_value", "Decimal place value and comparison")
        self.assertIn("Practice focus: Decimal place value and comparison", text)
        self.assertIn(f"Think: {subskill_level.mental_model}", text)

    def test_parent_question_preview_stays_empty(self) -> None:
        question = Question(
            skill="counting",
            prompt="Count the dots.",
            correct_answer="4",
            explanation="",
            choices=None,
            visual=None,
        )
        panel = _FakePanel(question, child=False)

        self.assertEqual("", question_intuition_preview(panel, question))


if __name__ == "__main__":
    unittest.main()
