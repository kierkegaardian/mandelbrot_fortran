from __future__ import annotations

import unittest

from app.quiz_engine import Question
from app.quiz_flow import submit_answer
from app.quiz_recovery import build_mistake_recovery_text


class _Var:
    def __init__(self, value="") -> None:
        self.value = value

    def get(self):
        return self.value

    def set(self, value) -> None:
        self.value = value


class _Button:
    def __init__(self) -> None:
        self.states: list[tuple[str, ...]] = []

    def state(self, states) -> None:
        self.states.append(tuple(states))


class _PanelStub:
    def __init__(self, *, question: Question, answer: str, offer_recovery: bool) -> None:
        self._questions = [question]
        self._index = 0
        self.answer_var = _Var(answer)
        self.choice_var = _Var("")
        self.repeat_var = _Var(False)
        self.feedback_var = _Var("")
        self.intuition_var = _Var("")
        self.recovery_var = _Var("")
        self.submit_btn = _Button()
        self.stuck_btn = _Button()
        self.next_btn = _Button()
        self._score = 0
        self._answers: list[tuple[Question, str, bool]] = []
        self._persisted = False
        self._recovery_started = False
        self._recovery_answer = ""
        self._feedback_state = None
        self._offer_recovery = offer_recovery
        self._recorded_streak: list[bool] = []

    def _recovery_active(self) -> bool:
        return False

    def _submit_mistake_recovery(self) -> None:
        raise AssertionError("recovery submit should not be used in this test")

    def _should_offer_mistake_recovery(self, _question: Question) -> bool:
        return self._offer_recovery

    def _start_mistake_recovery(self, question: Question, incorrect_answer: str) -> None:
        self._recovery_started = True
        self._recovery_answer = incorrect_answer
        self.recovery_var.set(f"Recover {question.skill}")

    def _record_streak(self, *, correct: bool) -> None:
        self._recorded_streak.append(correct)

    def _persist_quiz_progress(self) -> None:
        self._persisted = True

    def _set_feedback_state(self, *, correct: bool | None) -> None:
        self._feedback_state = correct

    def _play_correct_animation(self) -> None:
        return None

    @property
    def _answers_recorded(self) -> list[tuple[Question, str, bool]]:
        return self._answers


class QuizRecoveryTests(unittest.TestCase):
    def test_wrong_answer_starts_recovery_when_enabled(self) -> None:
        question = Question(
            skill="add_subtract",
            prompt="8 + 5 = ?",
            correct_answer="13",
            explanation="Add the two numbers.",
            choices=None,
            visual=None,
        )
        panel = _PanelStub(question=question, answer="12", offer_recovery=True)

        submit_answer(panel)

        self.assertTrue(panel._recovery_started)
        self.assertEqual(panel._recovery_answer, "12")
        self.assertEqual(panel.feedback_var.get(), "Let's fix this one together.")
        self.assertEqual(panel._answers_recorded, [(question, "12", False)])
        self.assertEqual(panel._recorded_streak, [False])
        self.assertTrue(panel._persisted)
        self.assertEqual(panel._feedback_state, False)
        self.assertNotIn(("!disabled",), panel.next_btn.states)

    def test_wrong_answer_without_recovery_reveals_answer_and_advances(self) -> None:
        question = Question(
            skill="add_subtract",
            prompt="8 + 5 = ?",
            correct_answer="13",
            explanation="Add the two numbers.",
            choices=None,
            visual=None,
        )
        panel = _PanelStub(question=question, answer="12", offer_recovery=False)

        submit_answer(panel)

        self.assertFalse(panel._recovery_started)
        self.assertIn("13", panel.feedback_var.get())
        self.assertIn(("!disabled",), panel.next_btn.states)

    def test_build_recovery_text_emphasizes_mistake_and_guided_redo(self) -> None:
        explanation = build_mistake_recovery_text(
            type(
                "_Explanation",
                (),
                {
                    "mental_model": "Think about groups.",
                    "common_mistake": "Mixing up the groups.",
                    "try_this": "Draw 3 groups of 4.",
                },
            )(),
            phase="redo",
        )

        self.assertIn("Why this mistake happens: Mixing up the groups.", explanation)
        self.assertIn("Guided redo: Draw 3 groups of 4.", explanation)
        self.assertIn("Mental model: Think about groups.", explanation)


if __name__ == "__main__":
    unittest.main()
