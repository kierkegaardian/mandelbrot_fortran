from __future__ import annotations

from collections.abc import Callable
import tkinter as tk
from tkinter import ttk

from .explanations import PARENT_EXPLANATION
from .models import Profile
from .parent_worksheets import WorksheetSection
from .ui_explain import ExplanationPanel
from .ui_parent_assignment_actions import ParentAssignmentActionsMixin
from .ui_parent_assignment_view import ParentAssignmentViewMixin
from .ui_parent_profiles import ParentProfilesMixin
from .ui_parent_quiz_sets import ParentQuizSetsMixin

ProfileGetter = Callable[[], Profile | None]
QuizSetLauncher = Callable[..., None]


class ParentPanel(
    ParentProfilesMixin,
    ParentQuizSetsMixin,
    ParentAssignmentViewMixin,
    ParentAssignmentActionsMixin,
):
    def __init__(
        self,
        controls_parent: tk.Widget,
        view_parent: tk.Widget,
        profile_getter: ProfileGetter,
        quiz_set_launcher: QuizSetLauncher | None = None,
    ) -> None:
        self.controls_frame = ttk.Frame(controls_parent)
        self.view_frame = ttk.Frame(view_parent)
        self._profile_getter = profile_getter
        self._quiz_set_launcher = quiz_set_launcher
        self._build_controls()
        self._build_view()

    def _build_controls(self) -> None:
        frame = ttk.Frame(self.controls_frame, padding=10)
        frame.pack(fill=tk.BOTH, expand=True)
        self.tabs = ttk.Notebook(frame)
        self.tabs.pack(fill=tk.BOTH, expand=True)
        self.profile_tab = ttk.Frame(self.tabs)
        self.quiz_tab = ttk.Frame(self.tabs)
        self.grades_tab = ttk.Frame(self.tabs)
        self.assignments_tab = ttk.Frame(self.tabs)
        self.worksheets_tab = ttk.Frame(self.tabs)
        self.tabs.add(self.profile_tab, text="Profiles")
        self.tabs.add(self.quiz_tab, text="Quiz Sets")
        self.tabs.add(self.grades_tab, text="Grades")
        self.tabs.add(self.assignments_tab, text="Assignments")
        self.tabs.add(self.worksheets_tab, text="Worksheets")

        self._build_profiles_tab()
        self._build_quiz_tab()
        self._build_grades_tab()
        self._build_assignments_tab()
        self.worksheets = WorksheetSection(
            self.worksheets_tab, self._profile_getter
        )
        self._refresh_profiles()
        self._refresh_quiz_sets()
        self.explain = ExplanationPanel(frame)
        self.explain.set_explanation(PARENT_EXPLANATION)
        self.explain.frame.pack(fill=tk.X, pady=(10, 0))

    def _build_view(self) -> None:
        ttk.Label(
            self.view_frame,
            text="Parent tools appear on the left. Use them to manage profiles and learning.",
            wraplength=500,
        ).pack(pady=30)

    def _active_parent_tab_index(self) -> int:
        return self.tabs.index(self.tabs.select())

    def _select_parent_tab(self, index: int) -> None:
        if 0 <= index < self.tabs.index("end"):
            self.tabs.select(index)
            self._refresh_active_tab_shortcut()

    def _refresh_active_tab_shortcut(self) -> None:
        refreshers = {
            0: self._refresh_profiles,
            1: self._refresh_quiz_sets,
            2: self._refresh_grades,
            3: self._refresh_assignments,
            4: self.worksheets.refresh_quiz_sets,
        }
        refreshers[self._active_parent_tab_index()]()

    def _create_active_item_shortcut(self) -> None:
        creators = {
            0: self._add_profile,
            1: self._add_quiz_set,
            3: self._create_assignment,
            4: self.worksheets._add_topic_row,
        }
        create = creators.get(self._active_parent_tab_index())
        if create is not None:
            create()

    def focus_primary_control(self) -> None:
        controls = {
            0: self.profile_name,
            1: self.quiz_name,
            2: self.profile_combo,
            3: self.assignment_profile_combo,
            4: self.worksheets.ws_combo,
        }
        controls[self._active_parent_tab_index()].focus_set()

    def on_module_activated(self) -> None:
        self._refresh_active_tab_shortcut()
