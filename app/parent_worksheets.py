from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk
import webbrowser

from . import db
from .time_utils import now_iso
from .ui_widgets import int_spinbox
from .worksheet import generate_custom_worksheet, generate_worksheet


CUSTOM_TOPIC_SKILLS = [
    "counting",
    "add_subtract",
    "multiply",
    "divide",
    "ratios",
    "fractions",
    "long_addition",
    "long_subtraction",
    "long_multiplication",
    "long_division",
    "money",
]


class WorksheetSection:
    def __init__(self, parent: tk.Widget, profile_getter) -> None:
        self.tab = parent
        self._profile_getter = profile_getter
        self.ws_topic_rows: list[dict] = []
        self._ws_map: dict[str, object] = {}
        self._build()

    def _build(self) -> None:
        ttk.Label(self.tab, text="From Quiz Set (optional)").pack(anchor=tk.W, padx=10, pady=(8, 0))
        self.ws_quiz_set = tk.StringVar(value="")
        self.ws_combo = ttk.Combobox(self.tab, textvariable=self.ws_quiz_set, values=[], state="readonly")
        self.ws_combo.pack(fill=tk.X, padx=10, pady=4)

        ttk.Button(self.tab, text="Generate from Quiz Set", command=self._generate_from_quiz_set).pack(pady=(4, 8))

        ttk.Separator(self.tab).pack(fill=tk.X, padx=10, pady=8)

        ttk.Label(self.tab, text="Custom Worksheet Builder").pack(anchor=tk.W, padx=10, pady=(4, 4))

        self.ws_topics_container = ttk.Frame(self.tab)
        self.ws_topics_container.pack(fill=tk.BOTH, expand=True, padx=10)
        self.ws_topics_canvas = tk.Canvas(self.ws_topics_container, height=180, highlightthickness=0)
        self.ws_topics_scroll = ttk.Scrollbar(
            self.ws_topics_container, orient=tk.VERTICAL, command=self.ws_topics_canvas.yview
        )
        self.ws_topics_canvas.configure(yscrollcommand=self.ws_topics_scroll.set)
        self.ws_topics_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.ws_topics_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.ws_topics_frame = ttk.Frame(self.ws_topics_canvas)
        self._topics_window = self.ws_topics_canvas.create_window((0, 0), window=self.ws_topics_frame, anchor="nw")
        self.ws_topics_frame.bind("<Configure>", self._sync_topics_scroll)
        self.ws_topics_canvas.bind("<Configure>", self._resize_topics_frame)

        header = ttk.Frame(self.ws_topics_frame)
        header.pack(fill=tk.X)
        ttk.Label(header, text="Topic", width=16).grid(row=0, column=0, sticky=tk.W)
        ttk.Label(header, text="# Questions", width=10).grid(row=0, column=1, sticky=tk.W)
        ttk.Label(header, text="Level", width=6).grid(row=0, column=2, sticky=tk.W)
        ttk.Label(header, text="# Graphical", width=12).grid(row=0, column=3, sticky=tk.W)

        self._add_topic_row(default_skill="counting")
        self._add_topic_row(default_skill="add_subtract")
        self._add_topic_row(default_skill="multiply")

        ttk.Button(self.tab, text="Add Topic Row", command=self._add_topic_row).pack(pady=(6, 2))
        ttk.Button(self.tab, text="Generate Custom Worksheet", command=self._generate_custom_worksheet).pack(pady=6)

        self.refresh_quiz_sets()

    def refresh_quiz_sets(self) -> None:
        quiz_sets = db.list_quiz_sets()
        labels = [q.name for q in quiz_sets]
        self._ws_map = {q.name: q for q in quiz_sets}
        self.ws_combo.configure(values=labels)

    def _add_topic_row(self, default_skill: str | None = None) -> None:
        row = ttk.Frame(self.ws_topics_frame)
        row.pack(fill=tk.X, pady=2)

        skill_var = tk.StringVar(value=default_skill or "counting")
        count_var = tk.IntVar(value=5)
        level_var = tk.IntVar(value=1)
        graphical_var = tk.IntVar(value=2)

        ttk.Combobox(
            row,
            textvariable=skill_var,
            values=CUSTOM_TOPIC_SKILLS,
            state="readonly",
            width=16,
        ).grid(row=0, column=0, sticky=tk.W)

        int_spinbox(row, count_var, 0, 30, width=8).grid(row=0, column=1, padx=4, sticky=tk.W)
        int_spinbox(row, level_var, 1, 3, width=6).grid(row=0, column=2, padx=4, sticky=tk.W)
        int_spinbox(row, graphical_var, 0, 30, width=10).grid(row=0, column=3, padx=4, sticky=tk.W)

        self.ws_topic_rows.append(
            {
                "skill": skill_var,
                "count": count_var,
                "level": level_var,
                "graphical": graphical_var,
            }
        )
        self._sync_topics_scroll()

    def _sync_topics_scroll(self, _event: tk.Event | None = None) -> None:
        self.ws_topics_canvas.configure(scrollregion=self.ws_topics_canvas.bbox("all"))

    def _resize_topics_frame(self, event: tk.Event) -> None:
        self.ws_topics_canvas.itemconfigure(self._topics_window, width=event.width)

    def _generate_from_quiz_set(self) -> None:
        profile = self._profile_getter()
        if profile is None:
            messagebox.showerror("No profile", "Please select a profile first.")
            return

        selected = self._ws_map.get(self.ws_quiz_set.get())
        if selected is None:
            messagebox.showerror("Choose a quiz set", "Pick a quiz set to generate a worksheet.")
            return

        skill = selected.skill
        q_type = selected.question_type
        num_questions = selected.num_questions
        level = selected.level
        title = f"Worksheet: {selected.name}"
        quiz_set_id = selected.id

        path, _questions = generate_worksheet(skill, q_type, num_questions, level, title)
        db.create_worksheet(profile.id, quiz_set_id, skill, q_type, num_questions, level, path, now_iso())
        webbrowser.open(f"file://{path}")
        messagebox.showinfo("Worksheet ready", f"Worksheet saved to {path}")

    def _generate_custom_worksheet(self) -> None:
        profile = self._profile_getter()
        if profile is None:
            messagebox.showerror("No profile", "Please select a profile first.")
            return

        specs: list[dict] = []
        total_questions = 0
        for row in self.ws_topic_rows:
            count = int(row["count"].get())
            if count <= 0:
                continue
            spec = {
                "skill": row["skill"].get(),
                "count": count,
                "level": int(row["level"].get()),
                "graphical": int(row["graphical"].get()),
            }
            specs.append(spec)
            total_questions += count

        if not specs:
            messagebox.showerror("No topics", "Add at least one topic with questions.")
            return

        title = "Custom Worksheet"
        path, _questions = generate_custom_worksheet(specs, title)
        db.create_worksheet(profile.id, None, "custom", "typed", total_questions, 0, path, now_iso())
        webbrowser.open(f"file://{path}")
        messagebox.showinfo("Worksheet ready", f"Worksheet saved to {path}")
