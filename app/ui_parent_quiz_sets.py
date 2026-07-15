"""Parent quiz-set controls."""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk

from . import sync_service
from .quiz_engine import SKILLS
from .time_utils import now_iso
from .ui_widgets import int_spinbox


class ParentQuizSetsMixin:
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
            updated_at=now_iso(),
        )
        self._refresh_quiz_sets()
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
