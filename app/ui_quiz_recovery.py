"""Guided wrong-answer recovery for quiz sessions."""

from __future__ import annotations

from tkinter import messagebox

from .explanations import ARITHMETIC_MODE_EXPLANATIONS, Explanation
from .quiz_answers import is_correct_answer
from .quiz_engine import Question
from .quiz_recovery import (
    MistakeRecoveryState,
    build_mistake_recovery_text,
    should_offer_mistake_recovery,
)
from .ui_quiz_generation import _question_session_signature
from .ui_settings import load_ui_settings


def _explanation_for(question: Question) -> Explanation:
    known = ARITHMETIC_MODE_EXPLANATIONS.get(question.skill)
    if known is not None:
        return known
    return Explanation(
        how_short=question.explanation,
        how_long=question.explanation,
        why_short=question.explanation,
        why_long=question.explanation,
        mental_model=question.explanation or "Use the same rule one step at a time.",
        common_mistake="Rushing past the operation or question detail.",
        try_this="Work the problem again slowly and check each step.",
    )


class QuizRecoveryMixin:
    def _recovery_active(self) -> bool:
        return self._mistake_recovery is not None

    def _should_offer_mistake_recovery(self, question: Question) -> bool:
        return should_offer_mistake_recovery(
            summer_mode=load_ui_settings().summer_mode,
            strategy=self.strategy_var.get(),
            question=question,
        )

    def _recovery_text(self, question: Question, *, phase: str) -> str:
        return build_mistake_recovery_text(
            _explanation_for(question), phase=phase
        )

    def _current_recovery_question(self) -> Question | None:
        state = self._mistake_recovery
        if state is None:
            return None
        return state.followup_question or state.source_question

    def _render_recovery_question(
        self, question: Question, *, prompt_prefix: str
    ) -> None:
        self.prompt_var.set(f"{prompt_prefix}: {question.prompt}")
        self.meta_var.set(f"[Recovery] [{question.mode}] Skill: {question.skill}")
        self.intuition_var.set("")
        self._build_answer_widget(question)
        self._render_visual(question)

    def _build_mistake_recovery_followup(
        self, question: Question
    ) -> Question | None:
        question_type = "mc" if question.choices else "typed"
        preferred_mode = (
            question.mode
            if question.mode in {"intuition", "expression", "word"}
            else None
        )
        try:
            followup = self._generate_question_with_variation(
                {_question_session_signature(question)},
                question.skill,
                self.level_var.get(),
                question_type,
                subskill=question.subskill,
                preferred_mode=preferred_mode,
            )
        except (LookupError, ValueError):
            return None
        followup.question_label = "Recovery"
        return self._apply_mode_preference(followup, preferred_mode)

    def _start_mistake_recovery(
        self, question: Question, incorrect_answer: str
    ) -> None:
        self._mistake_recovery = MistakeRecoveryState(
            phase="redo",
            source_question=question,
            incorrect_answer=incorrect_answer,
        )
        self.submit_btn.config(text="Try Again")
        self.feedback_var.set("Let's fix this one together.")
        self.recovery_var.set(self._recovery_text(question, phase="redo"))
        self._render_recovery_question(question, prompt_prefix="Try it again")
        self.submit_btn.state(["!disabled"])
        self.stuck_btn.state(["disabled"])
        self.next_btn.state(["disabled"])
        self._persist_quiz_progress()

    def _show_mistake_recovery_followup(self, followup: Question) -> None:
        self.submit_btn.config(text="Submit Follow-up")
        self.feedback_var.set("Nice correction. Now try one like it on your own.")
        self.recovery_var.set(self._recovery_text(followup, phase="followup"))
        self._render_recovery_question(followup, prompt_prefix="Recovery Practice")
        self.submit_btn.state(["!disabled"])
        self.stuck_btn.state(["disabled"])
        self.next_btn.state(["disabled"])
        self._persist_quiz_progress()

    def _complete_mistake_recovery(self, *, correct: bool) -> None:
        state = self._mistake_recovery
        if state is None:
            return
        question = state.followup_question or state.source_question
        if correct:
            self.feedback_var.set("Nice recovery. You fixed it and used it again.")
        else:
            self.feedback_var.set(
                f"Close. For this follow-up, the answer is {question.correct_answer}."
            )
        state.phase = "complete"
        self.submit_btn.config(text="Submit")
        self.submit_btn.state(["disabled"])
        self.stuck_btn.state(["disabled"])
        self.next_btn.state(["!disabled"])
        self.recovery_var.set(
            self._recovery_text(state.source_question, phase="complete")
        )
        self._persist_quiz_progress()

    def _submit_mistake_recovery(self) -> None:
        state = self._mistake_recovery
        question = self._current_recovery_question()
        if state is None or question is None:
            return
        answer = (
            self.choice_var.get().strip()
            if question.choices
            else self.answer_var.get().strip()
        )
        if not answer:
            messagebox.showerror("Missing answer", "Please enter or choose an answer.")
            return
        correct = is_correct_answer(
            question.correct_answer, answer, self.repeat_var.get()
        )
        if state.phase == "redo":
            if not correct:
                self.feedback_var.set("Use the hint and try again.")
                return
            followup = self._build_mistake_recovery_followup(
                state.source_question
            )
            if followup is None:
                self._complete_mistake_recovery(correct=True)
                return
            state.phase = "followup"
            state.followup_question = followup
            self._show_mistake_recovery_followup(followup)
            return
        self._complete_mistake_recovery(correct=correct)

    def _advance_after_mistake_recovery(self) -> bool:
        if self._mistake_recovery is None:
            return False
        if self._mistake_recovery.phase != "complete":
            return True
        self._clear_mistake_recovery()
        return False

    def _clear_mistake_recovery(self) -> None:
        self._mistake_recovery = None
        self.recovery_var.set("")
        self.submit_btn.config(text="Submit")
