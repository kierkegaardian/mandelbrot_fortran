from __future__ import annotations

import json
import tkinter as tk
from tkinter import messagebox, simpledialog, ttk
import webbrowser

from . import (
    content_audit,
    content_audit_report,
    db,
    school_year,
    school_year_assessment,
    summer_program,
    sync_service,
)
from .explanations import PARENT_EXPLANATION
from .parent_worksheets import WorksheetSection
from .quiz_engine import SKILLS
from .skill_graph import SKILL_LABELS, subskills_for
from .summer_program_defs import (
    FOUNDATION_BRIDGE_LANE,
    PLACEMENT_REVIEW_PENDING,
    PREALGEBRA_FINISH_LANE,
    lane_display_name,
    task_kind_label,
    unit_label,
)
from .texas_grade_goals import (
    TEA_MATH_TEKS_URL,
    quiz_ready_goals,
    texas_grade_plan,
    texas_grade_plans,
)
from .time_utils import now_iso
from .ui_explain import ExplanationPanel
from .ui_family_sync import FAMILY_SYNC_BETA_TITLE, FamilySyncSettings
from .ui_settings import (
    load_ui_settings,
    save_accessibility_preset,
    save_default_grade_band,
    save_enforce_offline_mode,
    save_show_external_links,
    save_summer_mode,
)
from .ui_widgets import int_spinbox


class ParentPanel:
    def __init__(
        self,
        controls_parent: tk.Widget,
        view_parent: tk.Widget,
        profile_getter,
        quiz_set_launcher=None,
        settings_changed_callback=None,
        summer_program_task_launcher=None,
    ) -> None:
        self.controls_frame = ttk.Frame(controls_parent)
        self.view_frame = ttk.Frame(view_parent)
        self._profile_getter = profile_getter
        self._quiz_set_launcher = quiz_set_launcher
        self._settings_changed_callback = settings_changed_callback
        self._summer_program_task_launcher = summer_program_task_launcher

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
        self.summer_program_tab = ttk.Frame(self.tabs)
        self.school_year_tab = ttk.Frame(self.tabs)
        self.worksheets_tab = ttk.Frame(self.tabs)
        self.sync_tab = ttk.Frame(self.tabs)
        self.tabs.add(self.profile_tab, text="Profiles")
        self.tabs.add(self.quiz_tab, text="Quiz Sets")
        self.tabs.add(self.grades_tab, text="Grades")
        self.tabs.add(self.assignments_tab, text="Assignments")
        self.tabs.add(self.summer_program_tab, text="Summer Program")
        self.tabs.add(self.school_year_tab, text="School Year")
        self.tabs.add(self.worksheets_tab, text="Worksheets")
        self.tabs.add(self.sync_tab, text="Family Sync")

        self._build_profiles_tab()
        self._build_quiz_tab()
        self._build_grades_tab()
        self._build_assignments_tab()
        self._build_summer_program_tab()
        self._build_school_year_tab()
        self.worksheets = WorksheetSection(self.worksheets_tab, self._profile_getter)
        self.family_sync = FamilySyncSettings(self.sync_tab, self._profile_getter)
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
    def _build_profiles_tab(self) -> None:
        self.profile_list = tk.Listbox(self.profile_tab, height=6)
        self.profile_list.pack(fill=tk.X, padx=10, pady=6)
        ttk.Button(self.profile_tab, text="Refresh", command=self._refresh_profiles).pack(pady=(0, 8))

        form = ttk.Frame(self.profile_tab)
        form.pack(fill=tk.X, padx=10)
        ttk.Label(form, text="Name").grid(row=0, column=0, sticky=tk.W)
        self.profile_name = ttk.Entry(form)
        self.profile_name.grid(row=0, column=1, sticky=tk.EW, pady=4)

        ttk.Label(form, text="Role").grid(row=1, column=0, sticky=tk.W)
        self.profile_role = tk.StringVar(value="child")
        ttk.Radiobutton(form, text="Child", variable=self.profile_role, value="child").grid(row=1, column=1, sticky=tk.W)
        ttk.Radiobutton(form, text="Parent", variable=self.profile_role, value="parent").grid(row=2, column=1, sticky=tk.W)

        form.columnconfigure(1, weight=1)
        self.profile_name.bind("<Return>", lambda _e: self._add_profile())
        self.add_profile_btn = ttk.Button(self.profile_tab, text="Add Profile", command=self._add_profile)
        self.add_profile_btn.pack(pady=6)
        self.delete_profile_btn = ttk.Button(self.profile_tab, text="Delete Selected", command=self._delete_profile)
        self.delete_profile_btn.pack(pady=2)
        settings = load_ui_settings()
        self.show_links_var = tk.BooleanVar(value=settings.show_external_links)
        ttk.Checkbutton(
            self.profile_tab,
            text="Show external learning links (internet)",
            variable=self.show_links_var,
            command=self._toggle_external_links,
        ).pack(anchor=tk.W, padx=10, pady=(8, 4))
        self.offline_mode_var = tk.BooleanVar(value=settings.enforce_offline_mode)
        ttk.Checkbutton(
            self.profile_tab,
            text="Enforce offline mode (disable web launches)",
            variable=self.offline_mode_var,
            command=self._toggle_offline_mode,
        ).pack(anchor=tk.W, padx=10, pady=(4, 4))
        self.summer_mode_var = tk.BooleanVar(value=settings.summer_mode)
        ttk.Checkbutton(
            self.profile_tab,
            text="Summer Mode (simplify child tabs and practice lanes)",
            variable=self.summer_mode_var,
            command=self._toggle_summer_mode,
        ).pack(anchor=tk.W, padx=10, pady=(4, 4))

        preset_row = ttk.Frame(self.profile_tab)
        preset_row.pack(fill=tk.X, padx=10, pady=(2, 4))
        ttk.Label(preset_row, text="Accessibility preset").pack(side=tk.LEFT)
        self.accessibility_var = tk.StringVar(value=settings.accessibility_preset)
        preset_combo = ttk.Combobox(
            preset_row,
            textvariable=self.accessibility_var,
            values=["standard", "large_text", "high_contrast"],
            state="readonly",
            width=14,
        )
        preset_combo.pack(side=tk.LEFT, padx=(8, 0))
        preset_combo.bind("<<ComboboxSelected>>", lambda _e: self._save_accessibility_preset())

        grade_row = ttk.Frame(self.profile_tab)
        grade_row.pack(fill=tk.X, padx=10, pady=(2, 4))
        ttk.Label(grade_row, text="Default grade band").pack(side=tk.LEFT)
        self.default_grade_var = tk.StringVar(value=settings.default_grade_band)
        grade_entry = ttk.Entry(grade_row, textvariable=self.default_grade_var, width=16)
        grade_entry.pack(side=tk.LEFT, padx=(8, 0))
        grade_entry.bind("<FocusOut>", lambda _e: self._save_default_grade_band())
        grade_entry.bind("<Return>", lambda _e: self._save_default_grade_band())

        pin_row = ttk.Frame(self.profile_tab)
        pin_row.pack(fill=tk.X, padx=10, pady=(6, 2))
        self.set_parent_pin_btn = ttk.Button(pin_row, text="Set / Change Parent PIN", command=self._set_parent_pin)
        self.set_parent_pin_btn.pack(side=tk.LEFT)
        self.clear_parent_pin_btn = ttk.Button(pin_row, text="Clear Parent Lockout", command=self._clear_parent_pin_lock)
        self.clear_parent_pin_btn.pack(side=tk.LEFT, padx=(8, 0))

    def _build_quiz_tab(self) -> None:
        self.quiz_list = tk.Listbox(self.quiz_tab, height=6)
        self.quiz_list.pack(fill=tk.X, padx=10, pady=6)
        self.quiz_list.bind("<<ListboxSelect>>", lambda _e: self._load_quiz_set())
        actions = ttk.Frame(self.quiz_tab)
        actions.pack(fill=tk.X, padx=10, pady=(0, 8))
        ttk.Button(actions, text="Refresh", command=self._refresh_quiz_sets).pack(side=tk.LEFT)
        self.start_quiz_set_btn = ttk.Button(actions, text="Start Selected Quiz Set", command=self._start_quiz_set)
        self.start_quiz_set_btn.pack(side=tk.LEFT, padx=(6, 0))
        if self._quiz_set_launcher is None:
            self.start_quiz_set_btn.state(["disabled"])

        form = ttk.Frame(self.quiz_tab)
        form.pack(fill=tk.X, padx=10)
        ttk.Label(form, text="Name").grid(row=0, column=0, sticky=tk.W)
        self.quiz_name = ttk.Entry(form)
        self.quiz_name.grid(row=0, column=1, sticky=tk.EW, pady=4)

        ttk.Label(form, text="Skill").grid(row=1, column=0, sticky=tk.W)
        self.quiz_skill = tk.StringVar(value="counting")
        ttk.Combobox(
            form,
            textvariable=self.quiz_skill,
            values=[*SKILLS, "mixed"],
            state="readonly",
        ).grid(row=1, column=1, sticky=tk.EW, pady=4)

        ttk.Label(form, text="Type").grid(row=2, column=0, sticky=tk.W)
        self.quiz_type = tk.StringVar(value="both")
        ttk.Combobox(form, textvariable=self.quiz_type, values=["mc", "typed", "both"], state="readonly").grid(
            row=2, column=1, sticky=tk.EW, pady=4
        )

        ttk.Label(form, text="Questions").grid(row=3, column=0, sticky=tk.W)
        self.quiz_num = tk.IntVar(value=5)
        int_spinbox(form, self.quiz_num, 3, 20).grid(row=3, column=1, sticky=tk.W)

        ttk.Label(form, text="Level").grid(row=4, column=0, sticky=tk.W)
        self.quiz_level = tk.IntVar(value=1)
        int_spinbox(form, self.quiz_level, 1, 3).grid(row=4, column=1, sticky=tk.W)

        self.quiz_mode_override = tk.BooleanVar(value=False)
        ttk.Checkbutton(form, text="Override mode mix", variable=self.quiz_mode_override).grid(
            row=5, column=0, columnspan=2, sticky=tk.W, pady=(4, 2)
        )
        mode_row = ttk.Frame(form)
        mode_row.grid(row=6, column=0, columnspan=2, sticky=tk.W, pady=(0, 4))
        ttk.Label(mode_row, text="I/E/W").pack(side=tk.LEFT)
        self.quiz_mode_intuition = tk.IntVar(value=30)
        self.quiz_mode_expression = tk.IntVar(value=45)
        self.quiz_mode_word = tk.IntVar(value=25)
        int_spinbox(mode_row, self.quiz_mode_intuition, 0, 100, width=4).pack(side=tk.LEFT, padx=(6, 2))
        int_spinbox(mode_row, self.quiz_mode_expression, 0, 100, width=4).pack(side=tk.LEFT, padx=2)
        int_spinbox(mode_row, self.quiz_mode_word, 0, 100, width=4).pack(side=tk.LEFT, padx=2)

        form.columnconfigure(1, weight=1)
        self.quiz_name.bind("<Return>", lambda _e: self._add_quiz_set())
        self.save_quiz_set_btn = ttk.Button(self.quiz_tab, text="Save Quiz Set", command=self._add_quiz_set)
        self.save_quiz_set_btn.pack(pady=6)
        self.update_quiz_set_btn = ttk.Button(self.quiz_tab, text="Update Selected", command=self._update_quiz_set)
        self.update_quiz_set_btn.pack(pady=2)
        self.delete_quiz_set_btn = ttk.Button(self.quiz_tab, text="Delete Selected", command=self._delete_quiz_set)
        self.delete_quiz_set_btn.pack(pady=2)
        self.add_default_quiz_sets_btn = ttk.Button(
            self.quiz_tab,
            text="Add Default Quiz Sets",
            command=self._add_default_quiz_sets,
        )
        self.add_default_quiz_sets_btn.pack(pady=(6, 2))

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
        self.create_assignment_btn = ttk.Button(btns, text="Create Assignment", command=self._create_assignment)
        self.create_assignment_btn.pack(side=tk.LEFT)
        self.refresh_assignments_btn = ttk.Button(btns, text="Refresh", command=self._refresh_assignments)
        self.refresh_assignments_btn.pack(side=tk.LEFT, padx=6)
        self.complete_assignment_btn = ttk.Button(btns, text="Mark Complete", command=self._complete_assignment)
        self.complete_assignment_btn.pack(side=tk.LEFT)

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
        self.assignment_notes.bind("<Return>", lambda _e: self._create_assignment())

    def _build_summer_program_tab(self) -> None:
        settings_box = ttk.LabelFrame(self.summer_program_tab, text="Plan Settings")
        settings_box.pack(fill=tk.X, padx=10, pady=(8, 6))
        ttk.Label(settings_box, text="Student").pack(anchor=tk.W, padx=10, pady=(8, 0))
        self.program_profile = tk.StringVar(value="")
        self.program_profile_combo = ttk.Combobox(
            settings_box,
            textvariable=self.program_profile,
            values=[],
            state="readonly",
        )
        self.program_profile_combo.pack(fill=tk.X, padx=10, pady=(0, 6))
        self.program_profile_combo.bind("<<ComboboxSelected>>", lambda _e: self._refresh_summer_program())

        form = ttk.Frame(settings_box)
        form.pack(fill=tk.X, padx=10, pady=(4, 6))
        ttk.Label(form, text="Lane").grid(row=0, column=0, sticky=tk.W)
        self.program_lane = tk.StringVar(value=PREALGEBRA_FINISH_LANE)
        ttk.Combobox(
            form,
            textvariable=self.program_lane,
            values=[PREALGEBRA_FINISH_LANE, FOUNDATION_BRIDGE_LANE],
            state="readonly",
        ).grid(row=0, column=1, sticky=tk.EW, pady=2)

        ttk.Label(form, text="Age (years)").grid(row=1, column=0, sticky=tk.W)
        self.program_age = tk.IntVar(value=9)
        int_spinbox(form, self.program_age, 5, 16).grid(row=1, column=1, sticky=tk.W, pady=2)

        ttk.Label(form, text="Start Date").grid(row=2, column=0, sticky=tk.W)
        self.program_start = ttk.Entry(form)
        self.program_start.grid(row=2, column=1, sticky=tk.EW, pady=2)
        self.program_start.insert(0, now_iso()[:10])

        ttk.Label(form, text="End Date").grid(row=3, column=0, sticky=tk.W)
        self.program_end = ttk.Entry(form)
        self.program_end.grid(row=3, column=1, sticky=tk.EW, pady=2)

        ttk.Label(form, text="Days / Week").grid(row=4, column=0, sticky=tk.W)
        self.program_days = tk.IntVar(value=5)
        int_spinbox(form, self.program_days, 1, 7).grid(row=4, column=1, sticky=tk.W, pady=2)

        ttk.Label(form, text="Minutes / Session").grid(row=5, column=0, sticky=tk.W)
        self.program_minutes = tk.IntVar(value=35)
        int_spinbox(form, self.program_minutes, 10, 90).grid(row=5, column=1, sticky=tk.W, pady=2)
        form.columnconfigure(1, weight=1)

        settings_btns = ttk.Frame(settings_box)
        settings_btns.pack(fill=tk.X, padx=10, pady=(0, 8))
        ttk.Button(settings_btns, text="Create / Reset Program", command=self._create_summer_program).pack(side=tk.LEFT)
        ttk.Button(settings_btns, text="Refresh", command=self._refresh_summer_program).pack(side=tk.LEFT, padx=(6, 0))

        decision_box = ttk.LabelFrame(self.summer_program_tab, text="Placement Decision")
        decision_box.pack(fill=tk.X, padx=10, pady=(0, 6))
        self.program_status_var = tk.StringVar(value="Summer program: —")
        ttk.Label(decision_box, textvariable=self.program_status_var, wraplength=560).pack(
            anchor=tk.W, padx=10, pady=(2, 4)
        )
        self.program_recommendation_var = tk.StringVar(value="Placement recommendation: —")
        ttk.Label(
            decision_box,
            textvariable=self.program_recommendation_var,
            foreground="#5b6f84",
            wraplength=560,
        ).pack(anchor=tk.W, padx=10, pady=(0, 4))
        self.program_review_var = tk.StringVar(value="Placement review: —")
        ttk.Label(
            decision_box,
            textvariable=self.program_review_var,
            foreground="#5b6f84",
            wraplength=560,
        ).pack(anchor=tk.W, padx=10, pady=(0, 6))
        decision_actions = ttk.Frame(decision_box)
        decision_actions.pack(fill=tk.X, padx=10, pady=(0, 8))
        self.program_placement_btn = ttk.Button(
            decision_actions,
            text="Run Placement Diagnostic",
            command=self._launch_program_placement,
        )
        self.program_placement_btn.pack(side=tk.LEFT)
        self.program_accept_btn = ttk.Button(
            decision_actions,
            text="Use Recommended Lane",
            command=self._accept_summer_program_recommendation,
        )
        self.program_accept_btn.pack(side=tk.LEFT, padx=(6, 0))
        self.program_keep_lane_btn = ttk.Button(
            decision_actions,
            text="Keep Current Lane",
            command=self._keep_current_summer_program_lane,
        )
        self.program_keep_lane_btn.pack(side=tk.LEFT, padx=(6, 0))
        self.program_rerun_btn = ttk.Button(
            decision_actions,
            text="Reset And Rerun Placement",
            command=self._rerun_program_placement,
        )
        self.program_rerun_btn.pack(side=tk.LEFT, padx=(6, 0))

        progress_box = ttk.LabelFrame(self.summer_program_tab, text="Progress And Reports")
        progress_box.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 8))
        self.program_alert_var = tk.StringVar(value="Program alert: —")
        ttk.Label(
            progress_box,
            textvariable=self.program_alert_var,
            foreground="#8a5b3c",
            wraplength=560,
        ).pack(anchor=tk.W, padx=10, pady=(6, 4))
        progress_actions = ttk.Frame(progress_box)
        progress_actions.pack(fill=tk.X, padx=10, pady=(0, 6))
        self.program_next_btn = ttk.Button(progress_actions, text="Launch Next Task", command=self._launch_next_program_task)
        self.program_next_btn.pack(side=tk.LEFT)
        ttk.Label(progress_box, text="Upcoming Tasks").pack(anchor=tk.W, padx=10, pady=(0, 0))
        self.program_tasks_list = tk.Listbox(progress_box, height=8)
        self.program_tasks_list.pack(fill=tk.X, padx=10, pady=4)

        ttk.Label(progress_box, text="Assessments").pack(anchor=tk.W, padx=10, pady=(6, 0))
        self.program_assessments_list = tk.Listbox(progress_box, height=5)
        self.program_assessments_list.pack(fill=tk.BOTH, expand=True, padx=10, pady=(4, 8))

        resource_box = ttk.LabelFrame(self.summer_program_tab, text="Resource Review")
        resource_box.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 8))
        self.resource_review_var = tk.StringVar(value="Resource Review: create a program to audit coverage.")
        ttk.Label(resource_box, textvariable=self.resource_review_var, wraplength=560).pack(
            anchor=tk.W, padx=10, pady=(6, 4)
        )
        resource_actions = ttk.Frame(resource_box)
        resource_actions.pack(anchor=tk.W, padx=10, pady=(0, 6))
        self.resource_review_export_btn = ttk.Button(
            resource_actions,
            text="Export Printable Review",
            command=self._export_resource_review,
        )
        self.resource_review_export_btn.pack(side=tk.LEFT)
        self.resource_review_export_btn.state(["disabled"])
        self.resource_review_list = tk.Listbox(resource_box, height=7)
        self.resource_review_list.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 8))

    def _build_school_year_tab(self) -> None:
        settings_box = ttk.LabelFrame(self.school_year_tab, text="Texas Grade Goals")
        settings_box.pack(fill=tk.X, padx=10, pady=(8, 6))
        student_row = ttk.Frame(settings_box)
        student_row.pack(fill=tk.X, padx=10, pady=(8, 4))
        ttk.Label(student_row, text="Student").pack(side=tk.LEFT)
        self.school_profile_var = tk.StringVar(value="")
        self.school_profile_combo = ttk.Combobox(
            student_row,
            textvariable=self.school_profile_var,
            values=[],
            state="readonly",
            width=18,
        )
        self.school_profile_combo.pack(side=tk.LEFT, padx=(8, 0))
        self.school_profile_combo.bind("<<ComboboxSelected>>", lambda _e: self._load_school_year_target_for_profile())

        row = ttk.Frame(settings_box)
        row.pack(fill=tk.X, padx=10, pady=(4, 6))
        ttk.Label(row, text="Grade").pack(side=tk.LEFT)
        self.school_grade_var = tk.StringVar(value="1")
        self.school_grade_combo = ttk.Combobox(
            row,
            textvariable=self.school_grade_var,
            values=[str(plan.grade) for plan in texas_grade_plans()],
            state="readonly",
            width=8,
        )
        self.school_grade_combo.pack(side=tk.LEFT, padx=(8, 0))
        self.school_grade_combo.bind("<<ComboboxSelected>>", lambda _e: self._refresh_school_year_goals())
        self.school_stretch_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            row,
            text="Include stretch goals",
            variable=self.school_stretch_var,
            command=self._refresh_school_year_goals,
        ).pack(side=tk.LEFT, padx=(8, 0))
        ttk.Button(row, text="Save Target", command=self._save_school_year_target).pack(side=tk.LEFT, padx=(8, 0))
        ttk.Button(row, text="Refresh", command=self._refresh_school_year_goals).pack(side=tk.LEFT, padx=(8, 0))

        action_row = ttk.Frame(settings_box)
        action_row.pack(fill=tk.X, padx=10, pady=(0, 6))
        ttk.Button(action_row, text="Add Grade Quiz Sets", command=self._add_grade_quiz_sets).pack(side=tk.LEFT)
        ttk.Button(action_row, text="Add Selected Goal Review", command=self._add_selected_goal_review_assignments).pack(
            side=tk.LEFT, padx=(8, 0)
        )
        ttk.Button(action_row, text="Add Next Goal Review", command=self._add_next_goal_review_assignments).pack(
            side=tk.LEFT, padx=(8, 0)
        )
        ttk.Button(action_row, text="Add Goal Assignments", command=self._add_grade_goal_assignments).pack(
            side=tk.LEFT, padx=(8, 0)
        )
        ttk.Button(action_row, text="Generate Test Packet", command=self._generate_school_year_assessment).pack(
            side=tk.LEFT, padx=(8, 0)
        )

        self.school_year_target_var = tk.StringVar(value="Student target: choose a student.")
        ttk.Label(settings_box, textvariable=self.school_year_target_var, wraplength=560).pack(
            anchor=tk.W, padx=10, pady=(0, 4)
        )
        self.school_year_summary_var = tk.StringVar(value="")
        ttk.Label(settings_box, textvariable=self.school_year_summary_var, wraplength=560).pack(
            anchor=tk.W, padx=10, pady=(0, 4)
        )
        self.school_year_source_var = tk.StringVar(value=TEA_MATH_TEKS_URL)
        ttk.Label(settings_box, textvariable=self.school_year_source_var, foreground="#5b6f84", wraplength=560).pack(
            anchor=tk.W, padx=10, pady=(0, 8)
        )

        self.school_year_list = tk.Listbox(self.school_year_tab, height=12)
        self.school_year_list.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 6))

        packets_box = ttk.LabelFrame(self.school_year_tab, text="Saved Assessment Packets")
        packets_box.pack(fill=tk.X, padx=10, pady=(0, 8))
        self.school_year_packets_var = tk.StringVar(value="Choose a student to see saved Texas packets.")
        ttk.Label(packets_box, textvariable=self.school_year_packets_var, wraplength=560).pack(
            anchor=tk.W, padx=10, pady=(6, 4)
        )
        self.school_year_packets_list = tk.Listbox(packets_box, height=4)
        self.school_year_packets_list.pack(fill=tk.X, padx=10, pady=(0, 6))
        packet_actions = ttk.Frame(packets_box)
        packet_actions.pack(anchor=tk.W, padx=10, pady=(0, 8))
        ttk.Button(packet_actions, text="Open Saved Packet", command=self._open_selected_school_year_packet).pack(
            side=tk.LEFT
        )
        ttk.Button(
            packet_actions,
            text="Archive Selected Packet",
            command=self._archive_selected_school_year_packet,
        ).pack(side=tk.LEFT, padx=(8, 0))
        self._refresh_school_year_goals()

    def _select_parent_tab(self, idx: int) -> str:
        if idx < 0 or idx >= self.tabs.index("end"):
            return "break"
        self.tabs.select(idx)
        self.focus_primary_control()
        return "break"

    def _refresh_active_tab_shortcut(self) -> str:
        idx = self.tabs.index(self.tabs.select())
        if idx == 0:
            self._refresh_profiles()
        elif idx == 1:
            self._refresh_quiz_sets()
        elif idx == 2:
            self._refresh_grades()
        elif idx == 3:
            self._refresh_assignments()
        elif idx == 4:
            self._refresh_summer_program()
        elif idx == 5:
            self._refresh_school_year_goals()
        elif idx == 7:
            self.family_sync.refresh()
        return "break"

    def _create_active_item_shortcut(self) -> str:
        idx = self.tabs.index(self.tabs.select())
        if idx == 0:
            self._add_profile()
        elif idx == 1:
            self._add_quiz_set()
        elif idx == 3:
            self._create_assignment()
        elif idx == 4:
            self._create_summer_program()
        elif idx == 5:
            self._add_grade_quiz_sets()
        return "break"

    def focus_primary_control(self) -> None:
        idx = self.tabs.index(self.tabs.select())
        if idx == 0:
            self.profile_name.focus_set()
        elif idx == 1:
            self.quiz_name.focus_set()
        elif idx == 2:
            self.profile_combo.focus_set()
        elif idx == 3:
            self.assignment_profile_combo.focus_set()
        elif idx == 4:
            self.program_profile_combo.focus_set()
        elif idx == 5:
            self.school_grade_combo.focus_set()
        elif idx == 7:
            self.family_sync.focus_primary_control()
        else:
            self.tabs.focus_set()

    def on_module_activated(self) -> None:
        self.focus_primary_control()

    def _refresh_profiles(self) -> None:
        self._profiles = sync_service.list_profiles()
        self.profile_list.delete(0, tk.END)
        for profile in self._profiles:
            self.profile_list.insert(tk.END, f"{profile.name} ({profile.role})")
        self.family_sync.refresh()
        self._refresh_profiles_for_grades()
        self._refresh_profiles_for_assignments()
        self._refresh_profiles_for_summer_programs()
        self._refresh_profiles_for_school_year()

    def _toggle_external_links(self) -> None:
        save_show_external_links(self.show_links_var.get())
        self._notify_settings_changed()

    def _toggle_offline_mode(self) -> None:
        save_enforce_offline_mode(self.offline_mode_var.get())
        self._notify_settings_changed()

    def _save_accessibility_preset(self) -> None:
        save_accessibility_preset(self.accessibility_var.get())
        self._notify_settings_changed()

    def _save_default_grade_band(self) -> None:
        save_default_grade_band(self.default_grade_var.get())
        self._notify_settings_changed()

    def _toggle_summer_mode(self) -> None:
        save_summer_mode(self.summer_mode_var.get())
        self._notify_settings_changed()
        messagebox.showinfo(
            "Summer Mode",
            "Summer Mode updates quiz and lesson filtering right away. Tab layout changes apply on the next launch.",
        )

    def _notify_settings_changed(self) -> None:
        if self._settings_changed_callback is None:
            return
        try:
            self._settings_changed_callback()
        except Exception:
            return

    def _set_parent_pin(self) -> None:
        current = self._profile_getter()
        if current is None:
            messagebox.showerror("No profile", "No active profile available.")
            return
        if current.role != "parent":
            messagebox.showerror("Parent profile required", "Switch to a parent profile to set or change the parent PIN.")
            return

        if db.parent_pin_configured():
            previous = simpledialog.askstring("Current PIN", "Enter current parent PIN:", show="*", parent=self.profile_tab)
            if previous is None:
                return
            if not db.verify_parent_pin(previous):
                messagebox.showerror("Incorrect PIN", "Current PIN was incorrect.")
                return
            db.clear_parent_lock(now_iso())

        first = simpledialog.askstring("New PIN", "Enter a new numeric PIN (4-12 digits):", show="*", parent=self.profile_tab)
        if first is None:
            return
        second = simpledialog.askstring("Confirm PIN", "Re-enter the new PIN:", show="*", parent=self.profile_tab)
        if second is None:
            return
        if first != second:
            messagebox.showerror("PIN mismatch", "PIN values did not match.")
            return
        try:
            db.set_parent_pin(current.id, first, now_iso())
        except ValueError as exc:
            messagebox.showerror("Invalid PIN", str(exc))
            return
        messagebox.showinfo("PIN updated", "Parent PIN has been set.")

    def _clear_parent_pin_lock(self) -> None:
        current = self._profile_getter()
        if current is None:
            return
        if current.role != "parent":
            messagebox.showerror("Parent profile required", "Switch to a parent profile to clear lockout.")
            return
        if db.parent_pin_configured():
            pin = simpledialog.askstring("Verify PIN", "Enter parent PIN to clear lockout:", show="*", parent=self.profile_tab)
            if pin is None:
                return
            if not db.verify_parent_pin(pin):
                messagebox.showerror("Incorrect PIN", "PIN verification failed.")
                return
        db.clear_parent_lock(now_iso())
        messagebox.showinfo("Lockout cleared", "Parent PIN lockout has been cleared.")

    def _add_profile(self) -> None:
        name = self.profile_name.get().strip()
        role = self.profile_role.get().strip()
        if not name:
            messagebox.showerror("Missing name", "Please enter a name.")
            return
        sync_service.create_profile(name, role, now_iso())
        self.profile_name.delete(0, tk.END)
        self._refresh_profiles()
    def _delete_profile(self) -> None:
        selection = self.profile_list.curselection()
        if not selection:
            messagebox.showerror("Select a profile", "Choose a profile to delete.")
            return
        profile = self._profiles[selection[0]]
        if not messagebox.askyesno("Confirm delete", f"Delete profile '{profile.name}' and its grades?"):
            return
        sync_service.delete_profile(profile.id, now_iso())
        self._refresh_profiles()
    def _refresh_quiz_sets(self) -> None:
        self._quiz_sets = sync_service.list_quiz_sets()
        self.quiz_list.delete(0, tk.END)
        for qset in self._quiz_sets:
            mix = ""
            if (
                qset.mode_intuition_pct is not None
                and qset.mode_expression_pct is not None
                and qset.mode_word_pct is not None
            ):
                mix = (
                    f" | I/E/W "
                    f"{qset.mode_intuition_pct}/{qset.mode_expression_pct}/{qset.mode_word_pct}"
                )
            self.quiz_list.insert(tk.END, f"{qset.name} ({qset.skill}, {qset.num_questions}q){mix}")
        self.worksheets.refresh_quiz_sets()

    def _start_quiz_set(self) -> None:
        if self._quiz_set_launcher is None:
            return
        selection = self.quiz_list.curselection()
        if not selection:
            messagebox.showerror("Select a quiz", "Choose a quiz set to start.")
            return
        qset = self._quiz_sets[selection[0]]
        self._quiz_set_launcher(
            qset.skill,
            qset.num_questions,
            qset.level,
            qset.question_type,
            qset.mode_intuition_pct,
            qset.mode_expression_pct,
            qset.mode_word_pct,
        )
    def _add_quiz_set(self) -> None:
        name = self.quiz_name.get().strip()
        if not name:
            messagebox.showerror("Missing name", "Please enter a quiz name.")
            return
        sync_service.create_quiz_set(
            name,
            self.quiz_skill.get(),
            self.quiz_type.get(),
            int(self.quiz_num.get()),
            int(self.quiz_level.get()),
            now_iso(),
            *_mode_mix_or_none(
                self.quiz_mode_override.get(),
                self.quiz_mode_intuition.get(),
                self.quiz_mode_expression.get(),
                self.quiz_mode_word.get(),
            ),
        )
        self.quiz_name.delete(0, tk.END)
        self._refresh_quiz_sets()

    def _add_default_quiz_sets(self) -> None:
        existing = {q.name for q in sync_service.list_quiz_sets()}
        defaults = [
            ("Counting Basics", "counting"),
            ("Add/Subtract Basics", "add_subtract"),
            ("Multiply Basics", "multiply"),
            ("Divide Basics", "divide"),
            ("Ratios Basics", "ratios"),
            ("Fractions (Circles)", "fractions"),
            ("Long Addition", "long_addition"),
            ("Long Subtraction", "long_subtraction"),
            ("Long Multiplication", "long_multiplication"),
            ("Long Division", "long_division"),
            ("Money Basics", "money"),
            ("Integers Basics", "integers"),
            ("Order of Operations", "order_of_operations"),
            ("Linear Equations Basics", "algebra_linear"),
            ("Geometry Area Basics", "geometry_area"),
            ("Right-Triangle Trig Basics", "trig_right_triangle"),
            ("Percent and Ratios", "stats_percent"),
            ("Averages", "stats_mean"),
            ("Probabilities", "stats_probability"),
            ("Calculus I Foundations", "calculus_1"),
            ("Calculus II Integrals and Series", "calculus_2"),
            ("Calculus III Multivariable", "calculus_3"),
        ]
        added = 0
        for name, skill in defaults:
            if name in existing:
                continue
            sync_service.create_quiz_set(name, skill, "both", 8, 1, now_iso())
            added += 1
        if added == 0:
            messagebox.showinfo("Defaults", "Default quiz sets already exist.")
        else:
            messagebox.showinfo("Defaults", f"Added {added} default quiz sets.")
        self._refresh_quiz_sets()

    def _delete_quiz_set(self) -> None:
        selection = self.quiz_list.curselection()
        if not selection:
            messagebox.showerror("Select a quiz", "Choose a quiz set to delete.")
            return
        qset = self._quiz_sets[selection[0]]
        if not messagebox.askyesno("Confirm delete", f"Delete quiz set '{qset.name}'?"):
            return
        sync_service.delete_quiz_set(qset.id, now_iso())
        self._refresh_quiz_sets()
    def _load_quiz_set(self) -> None:
        selection = self.quiz_list.curselection()
        if not selection:
            return
        qset = self._quiz_sets[selection[0]]
        self.quiz_name.delete(0, tk.END)
        self.quiz_name.insert(0, qset.name)
        self.quiz_skill.set(qset.skill)
        self.quiz_type.set(qset.question_type)
        self.quiz_num.set(qset.num_questions)
        self.quiz_level.set(qset.level)
        has_override = (
            qset.mode_intuition_pct is not None
            and qset.mode_expression_pct is not None
            and qset.mode_word_pct is not None
        )
        self.quiz_mode_override.set(has_override)
        if has_override:
            self.quiz_mode_intuition.set(int(qset.mode_intuition_pct))
            self.quiz_mode_expression.set(int(qset.mode_expression_pct))
            self.quiz_mode_word.set(int(qset.mode_word_pct))

    def _update_quiz_set(self) -> None:
        selection = self.quiz_list.curselection()
        if not selection:
            messagebox.showerror("Select a quiz", "Choose a quiz set to update.")
            return
        qset = self._quiz_sets[selection[0]]
        name = self.quiz_name.get().strip()
        if not name:
            messagebox.showerror("Missing name", "Please enter a quiz name.")
            return
        sync_service.update_quiz_set(
            qset.id,
            name,
            self.quiz_skill.get(),
            self.quiz_type.get(),
            int(self.quiz_num.get()),
            int(self.quiz_level.get()),
            *_mode_mix_or_none(
                self.quiz_mode_override.get(),
                self.quiz_mode_intuition.get(),
                self.quiz_mode_expression.get(),
                self.quiz_mode_word.get(),
            ),
        )
        self._refresh_quiz_sets()

    def _refresh_profiles_for_grades(self) -> None:
        if not hasattr(self, "profile_combo"):
            return
        profiles = sync_service.list_profiles()
        labels = [p.name for p in profiles]
        self._profile_map = {p.name: p for p in profiles}
        self.profile_combo.configure(values=labels)

    def _refresh_profiles_for_assignments(self) -> None:
        if not hasattr(self, "assignment_profile_combo"):
            return
        profiles = [p for p in sync_service.list_profiles() if p.role == "child"]
        labels = [p.name for p in profiles]
        self._assignment_profile_map = {p.name: p for p in profiles}
        self.assignment_profile_combo.configure(values=labels)
        if labels and self.assignment_profile.get() not in self._assignment_profile_map:
            self.assignment_profile.set(labels[0])
        self._refresh_assignments()

    def _refresh_profiles_for_summer_programs(self) -> None:
        if not hasattr(self, "program_profile_combo"):
            return
        profiles = [p for p in sync_service.list_profiles() if p.role == "child"]
        labels = [p.name for p in profiles]
        self._summer_program_profile_map = {p.name: p for p in profiles}
        self.program_profile_combo.configure(values=labels)
        if labels and self.program_profile.get() not in self._summer_program_profile_map:
            self.program_profile.set(labels[0])
        self._refresh_summer_program()

    def _refresh_profiles_for_school_year(self) -> None:
        if not hasattr(self, "school_profile_combo"):
            return
        profiles = [p for p in sync_service.list_profiles() if p.role == "child"]
        labels = [p.name for p in profiles]
        self._school_profile_map = {p.name: p for p in profiles}
        self.school_profile_combo.configure(values=labels)
        if labels and self.school_profile_var.get() not in self._school_profile_map:
            self.school_profile_var.set(labels[0])
        self._load_school_year_target_for_profile()

    def _refresh_assignment_subskills(self) -> None:
        skill = self.assignment_skill.get()
        options = ["Any", *subskills_for(skill)]
        if self.assignment_subskill.get() not in options:
            self.assignment_subskill.set("Any")
        self.assignment_subskill_combo.configure(values=options)

    def _create_assignment(self) -> None:
        profile = self._assignment_profile_map.get(self.assignment_profile.get())
        if profile is None:
            messagebox.showerror("Missing student", "Choose a student profile first.")
            return
        target_type = self.assignment_target_type.get().strip()
        target_value = float(self.assignment_target_value.get())
        subskill = None if self.assignment_subskill.get() == "Any" else self.assignment_subskill.get()
        if target_type == "subskill_mastered" and not subskill:
            messagebox.showerror("Missing subskill", "Subskill-mastered assignments require a subskill.")
            return
        mode_mix = _mode_mix_or_none(
            self.assignment_mode_override.get(),
            self.assignment_mode_intuition.get(),
            self.assignment_mode_expression.get(),
            self.assignment_mode_word.get(),
        )
        sync_service.create_assignment(
            profile_id=profile.id,
            skill=self.assignment_skill.get().strip(),
            subskill=subskill,
            target_type=target_type,
            target_value=target_value,
            level=int(self.assignment_level.get()),
            num_questions=int(self.assignment_questions.get()),
            question_type=self.assignment_question_type.get().strip(),
            mode_intuition_pct=mode_mix[0],
            mode_expression_pct=mode_mix[1],
            mode_word_pct=mode_mix[2],
            notes=self.assignment_notes.get().strip(),
            created_at=now_iso(),
        )
        self.assignment_notes.delete(0, tk.END)
        self._refresh_assignments()

    def _refresh_assignments(self) -> None:
        if not hasattr(self, "assignments_active_list"):
            return
        self.assignments_active_list.delete(0, tk.END)
        self.assignments_done_list.delete(0, tk.END)
        profile = self._assignment_profile_map.get(self.assignment_profile.get())
        if profile is None:
            self.assignment_analytics_var.set("Assignments analytics: —")
            return
        skill_filter = None if self.assignment_filter_skill.get() == "All" else self.assignment_filter_skill.get()
        target_filter = None if self.assignment_filter_target.get() == "All" else self.assignment_filter_target.get()
        done_limit = int(self.assignment_done_limit.get())
        self._active_assignments = sync_service.list_assignments(
            profile.id,
            active_only=True,
            skill=skill_filter,
            target_type=target_filter,
        )
        self._done_assignments = sync_service.list_assignments(
            profile.id,
            active_only=False,
            skill=skill_filter,
            target_type=target_filter,
            limit=done_limit,
        )
        for a in self._active_assignments:
            self.assignments_active_list.insert(tk.END, _assignment_label(a))
        for a in self._done_assignments:
            self.assignments_done_list.insert(tk.END, _assignment_label(a))
        analytics = sync_service.assignment_completion_analytics(profile.id, recent_days=int(self.assignment_recent_days.get()))
        avg_hours = analytics.get("avg_completion_hours")
        avg_text = "n/a" if avg_hours is None else f"{(float(avg_hours) / 24.0):.1f}d avg complete"
        top = analytics.get("top_completed_skills", [])
        if top:
            top_text = ", ".join(f"{SKILL_LABELS.get(skill, skill)} ({count})" for skill, count in top)
        else:
            top_text = "none yet"
        self.assignment_analytics_var.set(
            "Assignments analytics: "
            f"active {analytics.get('active_count', 0)} | "
            f"completed {analytics.get('completed_count', 0)} | "
            f"completed {analytics.get('completed_recent_count', 0)} in {int(self.assignment_recent_days.get())}d | "
            f"{avg_text} | top: {top_text}"
        )

    def _complete_assignment(self) -> None:
        profile = self._assignment_profile_map.get(self.assignment_profile.get())
        if profile is None:
            return
        sel = self.assignments_active_list.curselection()
        if not sel:
            messagebox.showerror("Select assignment", "Choose an active assignment to complete.")
            return
        assignment = self._active_assignments[sel[0]]
        sync_service.complete_assignment(assignment.id, now_iso())
        self._refresh_assignments()

    def _create_summer_program(self) -> None:
        if not load_ui_settings().summer_mode:
            messagebox.showinfo("Summer Program", "Turn on Summer Mode before creating a Summer Program.")
            return
        profile = self._summer_program_profile_map.get(self.program_profile.get())
        if profile is None:
            messagebox.showerror("Missing student", "Choose a child profile first.")
            return
        try:
            program = summer_program.create_summer_program(
                profile_id=profile.id,
                lane=self.program_lane.get().strip(),
                start_date=self.program_start.get().strip(),
                end_date=self.program_end.get().strip() or None,
                days_per_week=int(self.program_days.get()),
                minutes_per_session=int(self.program_minutes.get()),
                student_age_years=int(self.program_age.get()),
                created_at=now_iso(),
            )
        except ValueError as exc:
            messagebox.showerror("Summer Program", str(exc))
            return
        self.program_end.delete(0, tk.END)
        self.program_end.insert(0, program.end_date)
        self._refresh_summer_program()

    def _refresh_summer_program(self) -> None:
        if not hasattr(self, "program_tasks_list"):
            return
        self.program_tasks_list.delete(0, tk.END)
        self.program_assessments_list.delete(0, tk.END)
        self._set_resource_review_empty("Resource Review: choose a student to audit coverage.")
        profile = self._summer_program_profile_map.get(self.program_profile.get())
        if profile is None:
            self.program_status_var.set("Summer program: —")
            self.program_recommendation_var.set("Placement recommendation: —")
            self.program_review_var.set("Placement review: —")
            self.program_alert_var.set("Program alert: —")
            self.program_placement_btn.state(["disabled"])
            self.program_accept_btn.state(["disabled"])
            self.program_keep_lane_btn.state(["disabled"])
            self.program_rerun_btn.state(["disabled"])
            self.program_next_btn.state(["disabled"])
            return
        program = summer_program.get_active_summer_program(profile.id)
        self._current_summer_program = program
        if program is None:
            self.program_status_var.set("Summer program: none active")
            self.program_recommendation_var.set("Placement recommendation: create a program to begin.")
            self.program_review_var.set("Placement review: create a program, then run placement.")
            self.program_alert_var.set("Program alert: none")
            self.program_placement_btn.state(["disabled"])
            self.program_accept_btn.state(["disabled"])
            self.program_keep_lane_btn.state(["disabled"])
            self.program_rerun_btn.state(["disabled"])
            self.program_next_btn.state(["disabled"])
            self._set_resource_review_empty("Resource Review: create a program to audit coverage.")
            return
        self.program_lane.set(program.lane)
        self.program_age.set(program.student_age_years or self.program_age.get())
        self.program_start.delete(0, tk.END)
        self.program_start.insert(0, program.start_date)
        self.program_end.delete(0, tk.END)
        self.program_end.insert(0, program.end_date)
        self.program_days.set(program.days_per_week)
        self.program_minutes.set(program.minutes_per_session)

        summary = summer_program.summer_program_status_summary(profile.id, program.id)
        if summary is None:
            self.program_status_var.set("Summer program: none active")
            self.program_recommendation_var.set("Placement recommendation: —")
            self.program_review_var.set("Placement review: —")
            self.program_alert_var.set("Program alert: —")
            self.program_placement_btn.state(["disabled"])
            self.program_accept_btn.state(["disabled"])
            self.program_keep_lane_btn.state(["disabled"])
            self.program_rerun_btn.state(["disabled"])
            self.program_next_btn.state(["disabled"])
            self._set_resource_review_empty("Resource Review: no active program to audit.")
            return
        review = summary.review_state
        block = summary.block_summary
        next_task = summary.current_task
        next_text = "none"
        if next_task is not None:
            next_text = f"{unit_label(program.lane, next_task.unit_code)} • {task_kind_label(next_task.task_kind)}"
        self.program_status_var.set(
            f"Summer program: {lane_display_name(program.lane)} • Next: {next_text} • "
            f"Pace: {summary.pace_label} • Finish: {summary.finish_state}"
        )
        if summary.projected_finish_note:
            self.program_status_var.set(f"{self.program_status_var.get()} • {summary.projected_finish_note}")
        if summary.catch_up_note:
            self.program_status_var.set(f"{self.program_status_var.get()} • {summary.catch_up_note}")
        recommendation = review.recommended_lane or "Pending placement diagnostic"
        recommendation_text = (
            lane_display_name(recommendation)
            if recommendation in {PREALGEBRA_FINISH_LANE, FOUNDATION_BRIDGE_LANE}
            else recommendation
        )
        weak_text = f" • weak strands: {', '.join(review.weak_strands)}" if review.weak_strands else ""
        self.program_recommendation_var.set(
            f"Placement recommendation: current lane {lane_display_name(review.current_lane)} • "
            f"recommended {recommendation_text}{weak_text}"
        )
        review_text = "placement not run yet"
        if review.recommended_lane is None:
            review_text = "placement not run yet"
        elif review.review_status == PLACEMENT_REVIEW_PENDING:
            review_text = "parent review needed"
        elif review.review_status == "accepted":
            review_text = "reviewed and accepted"
        elif review.review_status == "overridden":
            review_text = "parent kept the current lane"
        age_note = f" • {review.age_gate_note}" if review.age_gate_note else ""
        self.program_review_var.set(f"Placement review: {review_text}{age_note}")
        alert = "Program alert: none"
        if block.reason == "awaiting_parent_review":
            alert = "Program alert: Parent review needed after placement. Use the decision buttons above."
        elif block.reason is not None:
            score_text = ""
            if block.score_pct is not None and block.required_score_pct is not None:
                score_text = f" Score {block.score_pct:.0f}% of {block.required_score_pct:.0f}% needed."
            weak_detail = f" Weak strands: {', '.join(block.weak_strands)}." if block.weak_strands else ""
            next_action = f" {block.next_action}" if block.next_action else ""
            alert = (
                f"Program alert: {block.reason.replace('_', ' ')}."
                f"{score_text}{weak_detail}{next_action}"
            )
        if summary.remediation_note:
            alert = f"{alert} {summary.remediation_note}"
        if summary.projected_finish_note and summary.projected_finish_note not in alert:
            alert = f"{alert} {summary.projected_finish_note}"
        if summary.catch_up_note and summary.catch_up_note not in alert:
            alert = f"{alert} {summary.catch_up_note}"
        self.program_alert_var.set(alert)

        reports = summer_program.latest_assessment_reports(program.id)

        blocked_index = None
        current_index = None
        for idx, task in enumerate(db.list_summer_program_tasks(program.id)):
            status_text = task.status
            task_block = ""
            if block.task_id == task.id and block.reason is not None:
                status_text = block.reason.replace("_", " ")
                blocked_index = idx
            if next_task is not None and next_task.id == task.id:
                current_index = idx
            self.program_tasks_list.insert(
                tk.END,
                f"{task.sequence_index + 1}. {unit_label(program.lane, task.unit_code)} • "
                f"{task_kind_label(task.task_kind)} • {status_text} • {task.scheduled_date}{task_block}",
            )
        if blocked_index is not None:
            self.program_tasks_list.selection_clear(0, tk.END)
            self.program_tasks_list.selection_set(blocked_index)
        elif current_index is not None:
            self.program_tasks_list.selection_clear(0, tk.END)
            self.program_tasks_list.selection_set(current_index)
        for report in reports:
            pct = f"{report.score_pct:.0f}%"
            result = "pass" if report.passed else "retry"
            detail = ""
            next_action = ""
            try:
                strands = json.loads(report.strand_results_json)
            except json.JSONDecodeError:
                strands = {}
            if strands:
                weakest = sorted(strands.items(), key=lambda item: item[1])[:2]
                detail = " • weak: " + ", ".join(f"{name} {score:.0f}%" for name, score in weakest)
            if report.assessment_type == "placement":
                next_action = " • next: parent review"
            elif report.passed:
                next_action = " • next: continue"
            elif report.assessment_type == "midpoint":
                next_action = " • next: guided review, then retry midpoint"
            elif report.assessment_type == "exit":
                next_action = " • next: targeted review, then retry exit"
            else:
                next_action = " • next: retry checkpoint path"
            if report is reports[-1] and summary.remediation_note:
                next_action += f" • remediation: {summary.remediation_note}"
            self.program_assessments_list.insert(
                tk.END,
                f"{report.completed_at[:10]} • {report.assessment_type} • {pct} • {result}{detail}{next_action}",
            )

        launch_task = summer_program.launchable_summer_program_task(program.id)
        if launch_task is not None and self._summer_program_task_launcher is not None:
            self.program_next_btn.state(["!disabled"])
        else:
            self.program_next_btn.state(["disabled"])
        placement_task = next(
            (task for task in db.list_summer_program_tasks(program.id) if task.task_kind == "placement_assessment"),
            None,
        )
        if (
            placement_task is not None
            and placement_task.status in {"pending", "blocked"}
            and self._summer_program_task_launcher is not None
        ):
            self.program_placement_btn.state(["!disabled"])
        else:
            self.program_placement_btn.state(["disabled"])
        if review.review_status == PLACEMENT_REVIEW_PENDING and review.recommended_lane is not None:
            self.program_accept_btn.state(["!disabled"])
            self.program_keep_lane_btn.state(["!disabled"])
        else:
            self.program_accept_btn.state(["disabled"])
            self.program_keep_lane_btn.state(["disabled"])
        self.program_rerun_btn.state(["!disabled"])
        self._refresh_resource_review(program.lane)

    def _set_resource_review_empty(self, message: str) -> None:
        if not hasattr(self, "resource_review_list"):
            return
        self.resource_review_var.set(message)
        self.resource_review_list.delete(0, tk.END)
        if hasattr(self, "resource_review_export_btn"):
            self.resource_review_export_btn.state(["disabled"])

    def _refresh_resource_review(self, lane: str) -> None:
        review = content_audit.summer_resource_review(lane)
        self.resource_review_list.delete(0, tk.END)
        self.resource_review_var.set(
            "Resource Review: "
            f"{review.ready_count} ready • {review.thin_count} thin • {review.missing_count} missing. "
            "Weakest rows shown first."
        )
        self.resource_review_export_btn.state(["!disabled"])
        if not review.rows:
            self.resource_review_list.insert(tk.END, "No auditable Summer Program resources for this lane.")
            return
        for row in review.weakest_rows[:18]:
            lane_part = "Bonus" if row.optional else "Core"
            link_part = "Khan yes" if row.has_khan_link else "Khan missing"
            source_part = "source yes" if row.has_open_resource else "source missing"
            scaffold_part = f"scaffold {row.scaffold_step_count}" if row.scaffold_step_count else "scaffold none"
            note = f" • {row.notes[0]}" if row.notes else ""
            self.resource_review_list.insert(
                tk.END,
                f"{row.readiness} • {lane_part} • {row.unit_label} • {row.subskill} • "
                f"E{row.expression_template_count}/W{row.word_template_count} • "
                f"{scaffold_part} • {link_part} • {source_part}{note}",
            )

    def _export_resource_review(self) -> None:
        program = getattr(self, "_current_summer_program", None)
        if program is None:
            messagebox.showerror("Resource Review", "Choose a student with an active Summer Program first.")
            return
        report = content_audit_report.generate_resource_review_report(program.lane)
        webbrowser.open(f"file://{report.path}")
        messagebox.showinfo(
            "Resource Review",
            f"Printable review saved to {report.path}. "
            f"{report.ready_count} ready, {report.thin_count} thin, {report.missing_count} missing.",
        )

    def _selected_school_profile(self):
        profile_map = getattr(self, "_school_profile_map", {})
        return profile_map.get(self.school_profile_var.get())

    def _load_school_year_target_for_profile(self) -> None:
        if not hasattr(self, "school_grade_var"):
            return
        profile = self._selected_school_profile()
        if profile is None:
            self.school_year_target_var.set("Student target: choose a student.")
            self._refresh_school_year_goals()
            return
        target = db.get_school_year_target(profile.id)
        if target is not None:
            self.school_grade_var.set(str(target.grade))
            self.school_stretch_var.set(bool(target.stretch_enabled))
        self._refresh_school_year_goals()

    def _save_school_year_target(self) -> None:
        profile = self._selected_school_profile()
        if profile is None:
            messagebox.showerror("School Year", "Choose a child profile first.")
            return
        try:
            db.save_school_year_target(
                profile.id,
                self._selected_school_grade(),
                self.school_stretch_var.get(),
                now_iso(),
            )
        except ValueError as exc:
            messagebox.showerror("School Year", str(exc))
            return
        self._refresh_school_year_goals()
        messagebox.showinfo("School Year", f"Saved Texas grade target for {profile.name}.")

    def _selected_school_grade(self) -> int:
        try:
            return int(self.school_grade_var.get())
        except (TypeError, ValueError):
            self.school_grade_var.set("1")
            return 1

    def _refresh_school_year_goals(self) -> None:
        if not hasattr(self, "school_year_list"):
            return
        try:
            plan = texas_grade_plan(self._selected_school_grade())
        except ValueError:
            self.school_grade_var.set("1")
            plan = texas_grade_plan(1)
        self.school_year_list.delete(0, tk.END)
        self._school_goal_by_index = {}
        self.school_year_summary_var.set(
            f"{plan.label} • {plan.tac_section} • "
            f"{plan.quiz_ready_count} quiz-ready goals • {plan.gap_count} content gap(s)"
        )
        status = None
        profile = self._selected_school_profile()
        if profile is not None:
            status = school_year.school_year_status(profile.id)
        if profile is None:
            self.school_year_target_var.set("Student target: choose a student.")
        elif status is None:
            self.school_year_target_var.set(f"Student target: {profile.name} has no saved Texas grade target yet.")
        else:
            stretch = "stretch on" if status.target.stretch_enabled else "stretch paused"
            if status.next_goal is None:
                next_text = "all quiz-ready goals complete"
            else:
                next_text = f"next: {status.next_goal.label}"
            self.school_year_target_var.set(
                f"Student target: {profile.name} • Grade {status.target.grade} • "
                f"{status.completed_count}/{status.total_count} quiz-ready goals complete • "
                f"{next_text} • {stretch}"
            )
        self.school_year_source_var.set(f"TEA source: {plan.source_url}")
        self.school_year_list.insert(tk.END, "Focal areas: " + " | ".join(plan.focal_areas))
        for goal in plan.goals:
            if goal.stretch and not self.school_stretch_var.get():
                continue
            status = "quiz-ready" if goal.quiz_ready else "content gap"
            stretch = " • stretch" if goal.stretch else ""
            refs = ", ".join(goal.standard_refs)
            if goal.skill is None:
                target = "new content needed"
            else:
                target = goal.skill
                if goal.subskills:
                    target = f"{target}: {', '.join(goal.subskills)}"
            row_index = self.school_year_list.size()
            self.school_year_list.insert(
                tk.END,
                f"{status}{stretch} • {refs} • {goal.label} • {target}",
            )
            self._school_goal_by_index[row_index] = goal
            mental_index = self.school_year_list.size()
            self.school_year_list.insert(tk.END, f"  Mental model: {goal.mental_model}")
            self._school_goal_by_index[mental_index] = goal
        self._refresh_school_year_packets()

    def _refresh_school_year_packets(self) -> None:
        if not hasattr(self, "school_year_packets_list"):
            return
        self.school_year_packets_list.delete(0, tk.END)
        self._school_year_packets = []
        profile = self._selected_school_profile()
        if profile is None:
            self.school_year_packets_var.set("Choose a student to see saved Texas packets.")
            return
        packets = db.list_worksheets(profile.id, skill_prefix="texas_grade_", limit=12)
        self._school_year_packets = packets
        if not packets:
            self.school_year_packets_var.set(f"Saved packets: none yet for {profile.name}.")
            return
        self.school_year_packets_var.set(f"Saved packets: {len(packets)} latest active Texas packet(s) for {profile.name}.")
        for packet in packets:
            grade_label = packet.skill.replace("texas_grade_", "Grade ")
            self.school_year_packets_list.insert(
                tk.END,
                f"{packet.created_at[:10]} • TX {grade_label} • {packet.num_questions}q • {packet.file_path}",
            )

    def _open_selected_school_year_packet(self) -> None:
        selection = self.school_year_packets_list.curselection()
        if not selection:
            messagebox.showerror("School Year", "Choose a saved assessment packet first.")
            return
        packet = self._school_year_packets[selection[0]]
        webbrowser.open(f"file://{packet.file_path}")

    def _archive_selected_school_year_packet(self) -> None:
        selection = self.school_year_packets_list.curselection()
        if not selection:
            messagebox.showerror("School Year", "Choose a saved assessment packet first.")
            return
        profile = self._selected_school_profile()
        if profile is None:
            messagebox.showerror("School Year", "Choose a child profile first.")
            return
        packet = self._school_year_packets[selection[0]]
        if not messagebox.askyesno(
            "School Year",
            "Archive this packet from the saved packet list? The HTML file stays on disk.",
        ):
            return
        archived = db.archive_worksheet(packet.id, profile_id=profile.id, archived_at=now_iso())
        if not archived:
            messagebox.showerror("School Year", "This packet was already archived or could not be found.")
            return
        messagebox.showinfo("School Year", "Packet archived from the saved packet list.")
        self._refresh_school_year_packets()

    def _selected_school_goal(self):
        selection = self.school_year_list.curselection()
        if not selection:
            return None
        return getattr(self, "_school_goal_by_index", {}).get(selection[0])

    def _add_grade_quiz_sets(self) -> None:
        try:
            plan = texas_grade_plan(self._selected_school_grade())
        except ValueError:
            messagebox.showerror("School Year", "Choose a Texas grade from 1 to 7.")
            return
        existing = {quiz_set.name for quiz_set in sync_service.list_quiz_sets()}
        added = 0
        for goal in quiz_ready_goals(plan.grade):
            if goal.stretch and not self.school_stretch_var.get():
                continue
            if goal.skill is None:
                continue
            name = f"TX Grade {plan.grade}: {goal.label}"
            if name in existing:
                continue
            sync_service.create_quiz_set(name, goal.skill, "both", 8, goal.quiz_level, now_iso())
            existing.add(name)
            added += 1
        if added:
            messagebox.showinfo("School Year", f"Added {added} Texas grade quiz set(s).")
            self._refresh_quiz_sets()
        else:
            messagebox.showinfo("School Year", "Texas grade quiz sets already exist for this grade.")
        self._refresh_school_year_goals()

    def _create_review_assignments_for_goal(self, profile, grade: int, goal, note_kind: str) -> int:
        if goal.skill is None or not goal.subskills:
            raise ValueError(f"{goal.label} is not quiz-ready yet.")
        existing = {
            (assignment.skill, assignment.subskill, assignment.target_type)
            for assignment in sync_service.list_assignments(profile.id, active_only=True)
        }
        refs = ", ".join(goal.standard_refs)
        added = 0
        for subskill in goal.subskills:
            key = (goal.skill, subskill, "subskill_mastered")
            if key in existing:
                continue
            sync_service.create_assignment(
                profile_id=profile.id,
                skill=goal.skill,
                subskill=subskill,
                target_type="subskill_mastered",
                target_value=1.0,
                level=goal.quiz_level,
                num_questions=6,
                question_type="both",
                mode_intuition_pct=None,
                mode_expression_pct=None,
                mode_word_pct=None,
                notes=f"TX Grade {grade} {note_kind}: {goal.label} ({refs})",
                created_at=now_iso(),
            )
            existing.add(key)
            added += 1
        return added

    def _add_selected_goal_review_assignments(self) -> None:
        profile = self._selected_school_profile()
        if profile is None:
            messagebox.showerror("School Year", "Choose a child profile first.")
            return
        goal = self._selected_school_goal()
        if goal is None:
            messagebox.showerror("School Year", "Choose a Texas goal from the list first.")
            return
        try:
            grade = self._selected_school_grade()
            added = self._create_review_assignments_for_goal(profile, grade, goal, "Selected Goal")
        except ValueError as exc:
            messagebox.showerror("School Year", str(exc))
            return
        if added:
            messagebox.showinfo("School Year", f"Added {added} selected-goal review assignment(s) for {profile.name}.")
            self._refresh_assignments()
        else:
            messagebox.showinfo("School Year", "Active review assignments already exist for the selected Texas goal.")
        self._refresh_school_year_goals()

    def _add_next_goal_review_assignments(self) -> None:
        profile = self._selected_school_profile()
        if profile is None:
            messagebox.showerror("School Year", "Choose a child profile first.")
            return
        status = school_year.school_year_status(profile.id)
        if status is None:
            messagebox.showerror("School Year", "Save a Texas grade target for this child first.")
            return
        goal = status.next_goal
        if goal is None:
            messagebox.showinfo("School Year", f"{profile.name} has completed all active Texas grade goals.")
            self._refresh_school_year_goals()
            return
        try:
            added = self._create_review_assignments_for_goal(
                profile,
                status.target.grade,
                goal,
                "Next Goal",
            )
        except ValueError as exc:
            messagebox.showerror("School Year", str(exc))
            return

        self.school_grade_var.set(str(status.target.grade))
        if added:
            messagebox.showinfo("School Year", f"Added {added} next-goal review assignment(s) for {profile.name}.")
            self._refresh_assignments()
        else:
            messagebox.showinfo("School Year", "Active review assignments already exist for the next Texas goal.")
        self._refresh_school_year_goals()

    def _add_grade_goal_assignments(self) -> None:
        profile = self._selected_school_profile()
        if profile is None:
            messagebox.showerror("School Year", "Choose a child profile first.")
            return
        try:
            plan = texas_grade_plan(self._selected_school_grade())
        except ValueError:
            messagebox.showerror("School Year", "Choose a Texas grade from 1 to 7.")
            return
        existing = {
            (assignment.skill, assignment.subskill, assignment.target_type)
            for assignment in sync_service.list_assignments(profile.id, active_only=True)
        }
        added = 0
        for goal in quiz_ready_goals(plan.grade):
            if goal.stretch and not self.school_stretch_var.get():
                continue
            if goal.skill is None:
                continue
            refs = ", ".join(goal.standard_refs)
            for subskill in goal.subskills:
                key = (goal.skill, subskill, "subskill_mastered")
                if key in existing:
                    continue
                sync_service.create_assignment(
                    profile_id=profile.id,
                    skill=goal.skill,
                    subskill=subskill,
                    target_type="subskill_mastered",
                    target_value=1.0,
                    level=goal.quiz_level,
                    num_questions=6,
                    question_type="both",
                    mode_intuition_pct=None,
                    mode_expression_pct=None,
                    mode_word_pct=None,
                    notes=f"TX Grade {plan.grade}: {goal.label} ({refs})",
                    created_at=now_iso(),
                )
                existing.add(key)
                added += 1
        if added:
            messagebox.showinfo("School Year", f"Added {added} Texas goal assignment(s) for {profile.name}.")
            self._refresh_assignments()
        else:
            messagebox.showinfo("School Year", "Active Texas goal assignments already exist for this grade.")
        self._refresh_school_year_goals()

    def _generate_school_year_assessment(self) -> None:
        profile = self._selected_school_profile()
        if profile is None:
            messagebox.showerror("School Year", "Choose a child profile first.")
            return
        try:
            grade = self._selected_school_grade()
            packet = school_year_assessment.generate_texas_grade_assessment(
                grade,
                include_stretch=self.school_stretch_var.get(),
                questions_per_subskill=1,
            )
        except ValueError as exc:
            messagebox.showerror("School Year", str(exc))
            return
        if not packet.items:
            messagebox.showerror("School Year", "No quiz-ready questions could be generated for this grade.")
            return
        db.create_worksheet(
            profile.id,
            None,
            f"texas_grade_{grade}",
            "typed",
            len(packet.items),
            grade,
            packet.path,
            now_iso(),
        )
        webbrowser.open(f"file://{packet.path}")
        note = f" Skipped {len(packet.skipped)} coverage note(s)." if packet.skipped else ""
        messagebox.showinfo("School Year", f"Assessment packet saved to {packet.path}.{note}")
        self._refresh_school_year_packets()
        self._refresh_school_year_goals()

    def _launch_next_program_task(self) -> None:
        profile = self._summer_program_profile_map.get(self.program_profile.get())
        program = getattr(self, "_current_summer_program", None)
        if profile is None or program is None or self._summer_program_task_launcher is None:
            return
        task = summer_program.launchable_summer_program_task(program.id)
        if task is None:
            summary = summer_program.summer_program_status_summary(profile.id, program.id)
            if summary is not None and summary.current_blocker == "awaiting_parent_review":
                messagebox.showinfo("Summer Program", "Parent review is required before the next task can launch.")
                return
            messagebox.showinfo("Summer Program", "No remaining Summer Program tasks.")
            return
        self._summer_program_task_launcher(task.id, profile)

    def _launch_program_placement(self) -> None:
        profile = self._summer_program_profile_map.get(self.program_profile.get())
        program = getattr(self, "_current_summer_program", None)
        if profile is None or program is None or self._summer_program_task_launcher is None:
            return
        for task in db.list_summer_program_tasks(program.id):
            if task.task_kind == "placement_assessment" and task.status in {"pending", "blocked"}:
                self._summer_program_task_launcher(task.id, profile)
                return
        messagebox.showinfo("Summer Program", "Placement diagnostic is already complete for this program.")

    def _accept_summer_program_recommendation(self) -> None:
        program = getattr(self, "_current_summer_program", None)
        if program is None:
            return
        summer_program.accept_summer_program_recommendation(program.id, now_iso())
        self._refresh_summer_program()

    def _keep_current_summer_program_lane(self) -> None:
        program = getattr(self, "_current_summer_program", None)
        if program is None:
            return
        summer_program.override_summer_program_lane(program.id, now_iso())
        self._refresh_summer_program()

    def _rerun_program_placement(self) -> None:
        program = getattr(self, "_current_summer_program", None)
        if program is None:
            return
        if not messagebox.askyesno(
            "Reset and rerun placement",
            "This will archive the current Summer Program and start a fresh copy with a new placement diagnostic.",
        ):
            return
        summer_program.rerun_summer_program_placement(program.id, now_iso())
        self._refresh_summer_program()

    def _refresh_grades(self) -> None:
        name = self.grades_profile.get()
        profile = self._profile_map.get(name)
        if profile is None:
            return
        attempts = sync_service.list_attempts(profile.id)
        self.grades_list.delete(0, tk.END)
        for attempt in attempts:
            self.grades_list.insert(
                tk.END, f"{attempt.created_at[:10]} | {attempt.skill} | {attempt.score}/{attempt.num_questions}"
            )


def _assignment_label(assignment) -> str:
    skill = SKILL_LABELS.get(assignment.skill, assignment.skill)
    target = assignment.target_type
    if target == "quiz_score_pct":
        target_text = "score = 100%"
    elif target == "subskill_mastered":
        target_text = "master subskill"
    else:
        target_text = target
    sub = f" [{assignment.subskill}]" if assignment.subskill else ""
    mix = ""
    if (
        assignment.mode_intuition_pct is not None
        and assignment.mode_expression_pct is not None
        and assignment.mode_word_pct is not None
    ):
        mix = f" | I/E/W {assignment.mode_intuition_pct}/{assignment.mode_expression_pct}/{assignment.mode_word_pct}"
    done = f" (done {assignment.completed_at[:10]})" if assignment.completed_at else ""
    return f"#{assignment.id} {skill}{sub} | {target_text}{mix}{done}"


def _mode_mix_or_none(enabled: bool, intuition: int, expression: int, word: int) -> tuple[int | None, int | None, int | None]:
    if not enabled:
        return (None, None, None)
    values = [max(0, int(intuition)), max(0, int(expression)), max(0, int(word))]
    total = sum(values)
    if total <= 0:
        return (30, 45, 25)
    scaled = [round((float(v) / float(total)) * 100.0) for v in values]
    drift = 100 - sum(scaled)
    idx = 0
    order = [1, 0, 2]
    while drift != 0:
        target = order[idx % len(order)]
        if drift > 0:
            scaled[target] += 1
            drift -= 1
        elif scaled[target] > 0:
            scaled[target] -= 1
            drift += 1
        idx += 1
    return (scaled[0], scaled[1], scaled[2])
