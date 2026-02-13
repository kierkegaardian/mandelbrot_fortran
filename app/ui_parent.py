from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk

from . import db
from .explanations import PARENT_EXPLANATION
from .parent_worksheets import WorksheetSection
from .quiz_engine import SKILLS
from .time_utils import now_iso
from .ui_explain import ExplanationPanel
from .ui_widgets import int_spinbox


class ParentPanel:
    def __init__(self, controls_parent: tk.Widget, view_parent: tk.Widget, profile_getter) -> None:
        self.controls_frame = ttk.Frame(controls_parent)
        self.view_frame = ttk.Frame(view_parent)
        self._profile_getter = profile_getter

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
        self.worksheets_tab = ttk.Frame(self.tabs)
        self.tabs.add(self.profile_tab, text="Profiles")
        self.tabs.add(self.quiz_tab, text="Quiz Sets")
        self.tabs.add(self.grades_tab, text="Grades")
        self.tabs.add(self.worksheets_tab, text="Worksheets")

        self._build_profiles_tab()
        self._build_quiz_tab()
        self._build_grades_tab()
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

    def _build_quiz_tab(self) -> None:
        self.quiz_list = tk.Listbox(self.quiz_tab, height=6)
        self.quiz_list.pack(fill=tk.X, padx=10, pady=6)
        self.quiz_list.bind("<<ListboxSelect>>", lambda _e: self._load_quiz_set())
        ttk.Button(self.quiz_tab, text="Refresh", command=self._refresh_quiz_sets).pack(pady=(0, 8))

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

    def _refresh_profiles(self) -> None:
        self._profiles = db.list_profiles()
        self.profile_list.delete(0, tk.END)
        for profile in self._profiles:
            self.profile_list.insert(tk.END, f"{profile.name} ({profile.role})")
        self._refresh_profiles_for_grades()

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
            self.quiz_list.insert(tk.END, f"{qset.name} ({qset.skill}, {qset.num_questions}q)")
        self.worksheets.refresh_quiz_sets()
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
            ("Slope and Rates", "calculus_slope"),
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
        )
        self._refresh_quiz_sets()

    def _refresh_profiles_for_grades(self) -> None:
        if not hasattr(self, "profile_combo"):
            return
        profiles = db.list_profiles()
        labels = [p.name for p in profiles]
        self._profile_map = {p.name: p for p in profiles}
        self.profile_combo.configure(values=labels)

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
