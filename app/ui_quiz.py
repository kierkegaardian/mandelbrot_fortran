"""Stable public quiz panel assembled from bounded behavior modules."""

from __future__ import annotations

import tkinter as tk
from pathlib import Path
from tkinter import ttk
from typing import Callable

from .models import Profile
from .quiz_engine import Question
from .quiz_recovery import MistakeRecoveryState
from .ui_quiz_completion import QuizCompletionMixin
from .ui_quiz_flow import QuizFlowMixin
from .ui_quiz_generation import QuizGenerationMixin, _subskill_for_question
from .ui_quiz_recovery import QuizRecoveryMixin
from .ui_quiz_session import QuizSessionMixin
from .ui_quiz_setup import QuizSetupMixin
from .ui_quiz_start import QuizStartMixin
from .ui_quiz_view import QuizViewMixin


class QuizPanel(
    QuizViewMixin,
    QuizSetupMixin,
    QuizStartMixin,
    QuizFlowMixin,
    QuizGenerationMixin,
    QuizRecoveryMixin,
    QuizSessionMixin,
    QuizCompletionMixin,
):
    def __init__(
        self,
        controls_parent: tk.Widget,
        view_parent: tk.Widget,
        profile_getter: Callable[[], Profile | None],
    ) -> None:
        self.controls_frame = ttk.Frame(controls_parent)
        self.view_frame = ttk.Frame(view_parent)
        self._profile_getter = profile_getter

        self.skill_var = tk.StringVar(value="counting")
        self.track_var = tk.StringVar(value="All")
        self.subskill_var = tk.StringVar(value="Any")
        self.type_var = tk.StringVar(value="both")
        self.strategy_var = tk.StringVar(value="focused")
        self.num_var = tk.IntVar(value=5)
        self.level_var = tk.IntVar(value=1)
        self.vary_numbers_var = tk.BooleanVar(value=True)
        self.historical_test_var = tk.StringVar(value="")
        self.historical_exam_filter_var = tk.StringVar(value="all")
        self.historical_category_var = tk.StringVar(value="all")
        self._historical_tests: dict[str, Path] = {}

        self._questions: list[Question] = []
        self._index = 0
        self._score = 0
        self._answers: list[tuple[Question, str, bool]] = []
        self._mode_mix_override: tuple[int, int, int] | None = None
        self._launch_context = "manual"
        self._quiz_started_monotonic: float | None = None
        self._attempt_skill: str | None = None
        self._record_attempt = True
        self._record_progress = True
        self._quiz_progress_attempt_id: int | None = None
        self._resume_checked_profile_id: int | None = None
        self._completion_created_at: str | None = None
        self._mistake_recovery: MistakeRecoveryState | None = None

        self._build_controls()
        self._build_view()

    def _start_quiz_shortcut(self) -> str:
        self.start_quiz()
        return "break"

    def _submit_or_next_shortcut(self) -> str:
        if not self._questions:
            self.start_quiz()
        elif self.next_btn.instate(["!disabled"]):
            self.next_question()
        elif self.submit_btn.instate(["!disabled"]):
            self.submit_answer()
        return "break"

    def _show_intuition_shortcut(self) -> str:
        if self.stuck_btn.instate(["!disabled"]):
            self._show_intuition()
        return "break"

    def focus_primary_control(self) -> None:
        self.skill_combo.focus_set()

    def on_module_activated(self) -> None:
        self._apply_track_filter()
        profile = self._profile_getter()
        if profile is not None and self._resume_checked_profile_id != profile.id:
            self._resume_checked_profile_id = profile.id
            self._try_resume_saved_quiz(profile.id)
        self.focus_primary_control()

    def shutdown(self) -> None:
        if self._questions and self._quiz_progress_attempt_id is not None:
            self._persist_quiz_progress()


__all__ = ("QuizPanel", "_subskill_for_question")
