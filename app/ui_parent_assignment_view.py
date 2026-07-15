"""Parent grades and assignments widget construction."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from .quiz_engine import SKILLS
from .skill_graph import SKILL_LABELS, subskills_for
from .ui_widgets import int_spinbox


class ParentAssignmentViewMixin:
    def _build_grades_tab(self) -> None:
        ttk.Label(self.grades_tab, text="Profile").pack(anchor=tk.W, padx=10, pady=(8, 0))
        self.grades_profile = tk.StringVar(value="")
        self.profile_combo = ttk.Combobox(self.grades_tab, textvariable=self.grades_profile, values=[], state="readonly")
        self.profile_combo.pack(fill=tk.X, padx=10)
        self.profile_combo.bind("<<ComboboxSelected>>", lambda _e: self._refresh_grades())

        self.grades_list = tk.Listbox(self.grades_tab, height=8)
        self.grades_list.pack(fill=tk.BOTH, expand=True, padx=10, pady=6)

        self._refresh_profiles_for_grades()

    def _build_assignments_tab(self) -> None:
        ttk.Label(self.assignments_tab, text="Student").pack(anchor=tk.W, padx=10, pady=(8, 0))
        self.assignment_profile = tk.StringVar(value="")
        self.assignment_profile_combo = ttk.Combobox(
            self.assignments_tab, textvariable=self.assignment_profile, values=[], state="readonly"
        )
        self.assignment_profile_combo.pack(fill=tk.X, padx=10, pady=(0, 6))
        self.assignment_profile_combo.bind("<<ComboboxSelected>>", lambda _e: self._refresh_assignments())

        form = ttk.Frame(self.assignments_tab)
        form.pack(fill=tk.X, padx=10, pady=(4, 6))
        ttk.Label(form, text="Skill").grid(row=0, column=0, sticky=tk.W)
        self.assignment_skill = tk.StringVar(value="counting")
        skill_combo = ttk.Combobox(form, textvariable=self.assignment_skill, values=SKILLS, state="readonly")
        skill_combo.grid(row=0, column=1, sticky=tk.EW, pady=2)
        skill_combo.bind("<<ComboboxSelected>>", lambda _e: self._refresh_assignment_subskills())

        ttk.Label(form, text="Subskill").grid(row=1, column=0, sticky=tk.W)
        self.assignment_subskill = tk.StringVar(value="Any")
        self.assignment_subskill_combo = ttk.Combobox(
            form, textvariable=self.assignment_subskill, values=["Any"], state="readonly"
        )
        self.assignment_subskill_combo.grid(row=1, column=1, sticky=tk.EW, pady=2)

        ttk.Label(form, text="Target Type").grid(row=2, column=0, sticky=tk.W)
        self.assignment_target_type = tk.StringVar(value="quiz_score_pct")
        ttk.Combobox(
            form,
            textvariable=self.assignment_target_type,
            values=["quiz_score_pct", "subskill_mastered"],
            state="readonly",
        ).grid(row=2, column=1, sticky=tk.EW, pady=2)

        ttk.Label(form, text="Target Value").grid(row=3, column=0, sticky=tk.W)
        self.assignment_target_value = tk.IntVar(value=100)
        int_spinbox(form, self.assignment_target_value, 1, 100).grid(row=3, column=1, sticky=tk.W, pady=2)

        ttk.Label(form, text="Quiz Level").grid(row=4, column=0, sticky=tk.W)
        self.assignment_level = tk.IntVar(value=1)
        int_spinbox(form, self.assignment_level, 1, 3).grid(row=4, column=1, sticky=tk.W, pady=2)

        ttk.Label(form, text="Questions").grid(row=5, column=0, sticky=tk.W)
        self.assignment_questions = tk.IntVar(value=5)
        int_spinbox(form, self.assignment_questions, 3, 20).grid(row=5, column=1, sticky=tk.W, pady=2)

        ttk.Label(form, text="Quiz Type").grid(row=6, column=0, sticky=tk.W)
        self.assignment_question_type = tk.StringVar(value="both")
        ttk.Combobox(
            form, textvariable=self.assignment_question_type, values=["mc", "typed", "both"], state="readonly"
        ).grid(row=6, column=1, sticky=tk.EW, pady=2)

        self.assignment_mode_override = tk.BooleanVar(value=False)
        ttk.Checkbutton(form, text="Override mode mix", variable=self.assignment_mode_override).grid(
            row=7, column=0, columnspan=2, sticky=tk.W, pady=(4, 2)
        )
        mode_row = ttk.Frame(form)
        mode_row.grid(row=8, column=0, columnspan=2, sticky=tk.W, pady=(0, 2))
        ttk.Label(mode_row, text="I/E/W").pack(side=tk.LEFT)
        self.assignment_mode_intuition = tk.IntVar(value=30)
        self.assignment_mode_expression = tk.IntVar(value=45)
        self.assignment_mode_word = tk.IntVar(value=25)
        int_spinbox(mode_row, self.assignment_mode_intuition, 0, 100, width=4).pack(side=tk.LEFT, padx=(6, 2))
        int_spinbox(mode_row, self.assignment_mode_expression, 0, 100, width=4).pack(side=tk.LEFT, padx=2)
        int_spinbox(mode_row, self.assignment_mode_word, 0, 100, width=4).pack(side=tk.LEFT, padx=2)

        ttk.Label(form, text="Notes").grid(row=9, column=0, sticky=tk.W)
        self.assignment_notes = ttk.Entry(form)
        self.assignment_notes.grid(row=9, column=1, sticky=tk.EW, pady=2)
        form.columnconfigure(1, weight=1)

        btns = ttk.Frame(self.assignments_tab)
        btns.pack(fill=tk.X, padx=10, pady=(0, 4))
        ttk.Button(btns, text="Create Assignment", command=self._create_assignment).pack(side=tk.LEFT)
        ttk.Button(btns, text="Refresh", command=self._refresh_assignments).pack(side=tk.LEFT, padx=6)
        ttk.Button(btns, text="Mark Complete", command=self._complete_assignment).pack(side=tk.LEFT)

        filters = ttk.Frame(self.assignments_tab)
        filters.pack(fill=tk.X, padx=10, pady=(2, 4))
        ttk.Label(filters, text="Filter Skill").grid(row=0, column=0, sticky=tk.W)
        self.assignment_filter_skill = tk.StringVar(value="All")
        skill_filter_combo = ttk.Combobox(
            filters,
            textvariable=self.assignment_filter_skill,
            values=["All", *SKILLS],
            state="readonly",
            width=18,
        )
        skill_filter_combo.grid(row=0, column=1, sticky=tk.W, padx=(6, 8))
        skill_filter_combo.bind("<<ComboboxSelected>>", lambda _e: self._refresh_assignments())

        ttk.Label(filters, text="Filter Target").grid(row=0, column=2, sticky=tk.W)
        self.assignment_filter_target = tk.StringVar(value="All")
        target_filter_combo = ttk.Combobox(
            filters,
            textvariable=self.assignment_filter_target,
            values=["All", "quiz_score_pct", "subskill_mastered"],
            state="readonly",
            width=16,
        )
        target_filter_combo.grid(row=0, column=3, sticky=tk.W, padx=(6, 8))
        target_filter_combo.bind("<<ComboboxSelected>>", lambda _e: self._refresh_assignments())

        ttk.Label(filters, text="Done Limit").grid(row=0, column=4, sticky=tk.W)
        self.assignment_done_limit = tk.IntVar(value=40)
        int_spinbox(
            filters,
            self.assignment_done_limit,
            5,
            200,
            width=5,
            command=self._refresh_assignments,
        ).grid(row=0, column=5, sticky=tk.W, padx=(6, 8))

        ttk.Label(filters, text="Analytics Days").grid(row=0, column=6, sticky=tk.W)
        self.assignment_recent_days = tk.IntVar(value=30)
        int_spinbox(
            filters,
            self.assignment_recent_days,
            7,
            365,
            width=5,
            command=self._refresh_assignments,
        ).grid(row=0, column=7, sticky=tk.W, padx=(6, 0))

        self.assignment_analytics_var = tk.StringVar(value="Assignments analytics: —")
        ttk.Label(
            self.assignments_tab,
            textvariable=self.assignment_analytics_var,
            foreground="#5b6f84",
            wraplength=560,
        ).pack(anchor=tk.W, padx=10, pady=(2, 4))

        ttk.Label(self.assignments_tab, text="Active Assignments").pack(anchor=tk.W, padx=10, pady=(6, 0))
        self.assignments_active_list = tk.Listbox(self.assignments_tab, height=6)
        self.assignments_active_list.pack(fill=tk.X, padx=10, pady=4)

        ttk.Label(self.assignments_tab, text="Completed Assignments").pack(anchor=tk.W, padx=10, pady=(6, 0))
        self.assignments_done_list = tk.Listbox(self.assignments_tab, height=5)
        self.assignments_done_list.pack(fill=tk.BOTH, expand=True, padx=10, pady=(4, 8))
        self._refresh_assignment_subskills()
