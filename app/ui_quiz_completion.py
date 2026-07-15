"""Atomic quiz completion and summary rendering."""

from __future__ import annotations

import time
import tkinter as tk
from tkinter import messagebox

from . import db, sync_service
from .learning_engine import build_skill_stats, recommend_next_skill_paths
from .skill_graph import (
    SKILL_LABELS,
    SKILL_ORDER,
    SKILL_PREREQUISITE_WEIGHTS,
    SUBSKILL_STREAK_TO_MASTER,
)
from .time_utils import now_iso
from .ui_quiz_generation import _subskill_coverage_by_skill, _subskill_for_question


class QuizCompletionMixin:
    def _finish_quiz(self) -> None:
        profile = self._profile_getter()
        if profile is None:
            return
        if not self._record_attempt:
            self._clear_quiz_progress()
            self.prompt_var.set("Practice complete.")
            self.feedback_var.set("")
            self.next_btn.state(["disabled"])
            return

        if self._completion_created_at is None:
            self._completion_created_at = now_iso()
        completed_at = self._completion_created_at
        elapsed_seconds = None
        if self._quiz_started_monotonic is not None:
            elapsed_seconds = max(
                0.0, time.monotonic() - self._quiz_started_monotonic
            )
        question_results = tuple(
            sync_service.QuestionResultInput(
                skill=question.skill,
                subskill=_subskill_for_question(question),
                question_label=question.question_label,
                mode=question.mode,
                prompt=question.prompt,
                correct_answer=question.correct_answer,
                user_answer=answer,
                is_correct=correct,
                explanation=question.explanation,
            )
            for question, answer, correct in self._answers
        )
        try:
            # Persist the stable completion timestamp before the atomic write so
            # a cleanup failure and later app restart cannot create a duplicate.
            self._persist_quiz_progress()
            result = sync_service.record_completed_quiz(
                profile_id=profile.id,
                quiz_set_id=None,
                skill=self._attempt_skill or self.skill_var.get(),
                question_type=self.type_var.get(),
                num_questions=len(self._questions),
                level=self.level_var.get(),
                score=self._score,
                created_at=completed_at,
                elapsed_seconds=elapsed_seconds,
                question_results=question_results,
                record_progress=self._record_progress,
                streak_to_master=SUBSKILL_STREAK_TO_MASTER,
                record_daily_review=self._launch_context == "daily_review",
            )
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror(
                "Could not save quiz",
                "Nothing was saved. Your in-progress quiz is still available.\n\n"
                f"Failure type: {type(exc).__name__}",
            )
            return

        try:
            self._clear_quiz_progress()
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror(
                "Quiz saved, resume cleanup failed",
                "The quiz was saved. Retry completion to clear its resume record.\n\n"
                f"Failure type: {type(exc).__name__}",
            )
            return
        self._show_quiz_summary(profile.id, result.completed_assignments)

    def _show_quiz_summary(
        self, profile_id: int, completed_assignments: int
    ) -> None:
        summary = f"Score: {self._score} / {len(self._questions)}\n\n"
        keyed_total = sum(
            1
            for question, _answer, _correct in self._answers
            if question.correct_answer
        )
        if keyed_total < len(self._questions):
            summary += (
                f"Items with answer keys: {keyed_total} / {len(self._questions)} "
                "(others were recorded as practice only)\n\n"
            )
        if self._attempt_skill != "historical_practice" and self._score < len(
            self._questions
        ):
            summary += (
                "Retake required: mastery completion needs 100% on a quiz attempt.\n\n"
            )
        if completed_assignments:
            summary += f"Assignments completed: {completed_assignments}\n\n"
        recommendations = recommend_next_skill_paths(
            tuple(SKILL_ORDER),
            SKILL_PREREQUISITE_WEIGHTS,
            build_skill_stats(db.list_attempts(profile_id), tuple(SKILL_ORDER)),
            subskill_coverage=_subskill_coverage_by_skill(profile_id),
            limit=3,
        )
        if recommendations:
            summary += "Suggested next paths:\n"
            for item in recommendations:
                reason = item.reasons[0] if item.reasons else "Strong next step."
                summary += (
                    f"- {SKILL_LABELS.get(item.skill, item.skill)}: {reason}\n"
                )
            summary += "\n"
        summary += "Mistake explanations:\n"
        for question, answer, correct in self._answers:
            if not correct:
                summary += (
                    f"- {question.prompt}\n  Your answer: {answer}\n"
                    f"  {question.explanation}\n\n"
                )

        self.summary_box.config(state=tk.NORMAL)
        self.summary_box.delete("1.0", tk.END)
        self.summary_box.insert(tk.END, summary)
        self.summary_box.config(state=tk.DISABLED)
        if self._attempt_skill == "historical_practice":
            self.prompt_var.set("Historical practice complete.")
        elif self._score == len(self._questions):
            self.prompt_var.set("Quiz complete (100%)!")
        else:
            self.prompt_var.set("Quiz complete (retake needed for mastery).")
        self.feedback_var.set("")
        self.next_btn.state(["disabled"])
        self._launch_context = "manual"
        self._quiz_started_monotonic = None
        self._attempt_skill = None
