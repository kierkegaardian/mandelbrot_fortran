from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk

from . import db
from .explanations import PARENT_EXPLANATION
from .parent_worksheets import WorksheetSection
from .quiz_engine import SKILLS
from .skill_graph import SKILL_LABELS, subskills_for
from .time_utils import now_iso
from .ui_explain import ExplanationPanel
from .ui_settings import load_ui_settings, save_show_external_links
from .ui_widgets import int_spinbox


class ParentPanel:
    def __init__(self, controls_parent: tk.Widget, view_parent: tk.Widget, profile_getter, quiz_set_launcher=None) -> None:
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
        self.worksheets = WorksheetSection(self.worksheets_tab, self._profile_getter)
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
        ttk.Button(self.profile_tab, text="Add Profile", command=self._add_profile).pack(pady=6)
        ttk.Button(self.profile_tab, text="Delete Selected", command=self._delete_profile).pack(pady=2)
        settings = load_ui_settings()
        self.show_links_var = tk.BooleanVar(value=settings.show_external_links)
        ttk.Checkbutton(
            self.profile_tab,
            text="Show external learning links (internet)",
            variable=self.show_links_var,
            command=self._toggle_external_links,
        ).pack(anchor=tk.W, padx=10, pady=(8, 4))

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
        ttk.Button(self.quiz_tab, text="Save Quiz Set", command=self._add_quiz_set).pack(pady=6)
        ttk.Button(self.quiz_tab, text="Update Selected", command=self._update_quiz_set).pack(pady=2)
        ttk.Button(self.quiz_tab, text="Delete Selected", command=self._delete_quiz_set).pack(pady=2)
        ttk.Button(self.quiz_tab, text="Add Default Quiz Sets", command=self._add_default_quiz_sets).pack(pady=(6, 2))

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

    def _refresh_profiles(self) -> None:
        self._profiles = db.list_profiles()
        self.profile_list.delete(0, tk.END)
        for profile in self._profiles:
            self.profile_list.insert(tk.END, f"{profile.name} ({profile.role})")
        self._refresh_profiles_for_grades()
        self._refresh_profiles_for_assignments()

    def _toggle_external_links(self) -> None:
        save_show_external_links(self.show_links_var.get())

    def _add_profile(self) -> None:
        name = self.profile_name.get().strip()
        role = self.profile_role.get().strip()
        if not name:
            messagebox.showerror("Missing name", "Please enter a name.")
            return
        db.create_profile(name, role, now_iso())
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
        db.delete_profile(profile.id)
        self._refresh_profiles()
    def _refresh_quiz_sets(self) -> None:
        self._quiz_sets = db.list_quiz_sets()
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
        db.create_quiz_set(
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
        existing = {q.name for q in db.list_quiz_sets()}
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
            db.create_quiz_set(name, skill, "both", 8, 1, now_iso())
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
        db.delete_quiz_set(qset.id)
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
        db.update_quiz_set(
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
        profiles = db.list_profiles()
        labels = [p.name for p in profiles]
        self._profile_map = {p.name: p for p in profiles}
        self.profile_combo.configure(values=labels)

    def _refresh_profiles_for_assignments(self) -> None:
        if not hasattr(self, "assignment_profile_combo"):
            return
        profiles = [p for p in db.list_profiles() if p.role == "child"]
        labels = [p.name for p in profiles]
        self._assignment_profile_map = {p.name: p for p in profiles}
        self.assignment_profile_combo.configure(values=labels)
        if labels and self.assignment_profile.get() not in self._assignment_profile_map:
            self.assignment_profile.set(labels[0])
        self._refresh_assignments()

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
        db.create_assignment(
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
        self._active_assignments = db.list_assignments(
            profile.id,
            active_only=True,
            skill=skill_filter,
            target_type=target_filter,
        )
        self._done_assignments = db.list_assignments(
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
        analytics = db.assignment_completion_analytics(profile.id, recent_days=int(self.assignment_recent_days.get()))
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
        db.set_assignment_active(assignment.id, False, completed_at=now_iso())
        self._refresh_assignments()

    def _refresh_grades(self) -> None:
        name = self.grades_profile.get()
        profile = self._profile_map.get(name)
        if profile is None:
            return
        attempts = db.list_attempts(profile.id)
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
