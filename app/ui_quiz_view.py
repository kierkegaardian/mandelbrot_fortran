"""Tk construction for the quiz panel."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from .explanations import QUIZ_EXPLANATION
from .quiz_engine import QUESTION_TYPES
from .skill_graph import track_names
from .ui_explain import ExplanationPanel
from .ui_widgets import int_spinbox


class QuizViewMixin:
    def _build_controls(self) -> None:
        frame = ttk.Frame(self.controls_frame, padding=10)
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text="Skill").pack(anchor=tk.W)
        track_combo = ttk.Combobox(
            frame,
            textvariable=self.track_var,
            values=["All", *track_names()],
            state="readonly",
            width=20,
        )
        track_combo.pack(fill=tk.X, pady=(0, 8))
        track_combo.bind("<<ComboboxSelected>>", lambda _e: self._on_track_change())

        self.skill_combo = ttk.Combobox(
            frame,
            textvariable=self.skill_var,
            values=self._quiz_skill_values_for_track("All"),
            state="readonly",
            width=20,
        )
        self.skill_combo.pack(fill=tk.X, pady=(0, 8))
        self.skill_combo.bind("<<ComboboxSelected>>", lambda _e: self._on_skill_change())

        ttk.Label(frame, text="Subskill (optional)").pack(anchor=tk.W)
        self.subskill_combo = ttk.Combobox(
            frame, textvariable=self.subskill_var, values=["Any"], state="readonly", width=24
        )
        self.subskill_combo.pack(fill=tk.X, pady=(0, 8))
        ttk.Label(frame, text="Curriculum source:").pack(anchor=tk.W)
        self.curriculum_label = ttk.Label(
            frame, text="No source mapped", foreground="#4f6b7a"
        )
        self.curriculum_label.pack(anchor=tk.W, pady=(0, 4))
        ttk.Button(
            frame, text="Open Source PDF", command=self._open_curriculum_pdf
        ).pack(anchor=tk.W)
        ttk.Label(frame, text="(Choose a skill to refresh)").pack(
            anchor=tk.W, padx=2, pady=(0, 8)
        )

        ttk.Separator(frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=(2, 8))
        ttk.Label(frame, text="Historical full tests (offline PDFs)").pack(anchor=tk.W)
        self.historical_combo = ttk.Combobox(
            frame,
            textvariable=self.historical_test_var,
            values=[],
            state="readonly",
            width=24,
        )
        self.historical_combo.pack(fill=tk.X, pady=(4, 4))
        test_btns = ttk.Frame(frame)
        test_btns.pack(fill=tk.X, pady=(0, 8))
        for label, command in (
            ("Open Full Test", self._open_historical_test),
            ("Print Test Mode", self._print_historical_test),
            ("Ingest PDFs", self._ingest_historical_pdfs),
            ("Ingest Answer Keys", self._ingest_historical_answer_keys),
            ("Refresh", self._refresh_historical_tests),
        ):
            ttk.Button(test_btns, text=label, command=command).pack(
                side=tk.LEFT, padx=(0 if label == "Open Full Test" else 6, 0)
            )

        filters = ttk.Frame(frame)
        filters.pack(fill=tk.X, pady=(0, 8))
        ttk.Label(filters, text="Hist Exam").pack(side=tk.LEFT)
        ttk.Combobox(
            filters,
            textvariable=self.historical_exam_filter_var,
            values=["all", "sat", "psat", "gre"],
            state="readonly",
            width=8,
        ).pack(side=tk.LEFT, padx=(6, 10))
        ttk.Label(filters, text="Hist Category").pack(side=tk.LEFT)
        ttk.Combobox(
            filters,
            textvariable=self.historical_category_var,
            values=["all", "math", "verbal", "writing", "unknown"],
            state="readonly",
            width=10,
        ).pack(side=tk.LEFT, padx=(6, 0))

        ttk.Label(frame, text="Question Type").pack(anchor=tk.W)
        ttk.Combobox(
            frame, textvariable=self.type_var, values=QUESTION_TYPES, state="readonly"
        ).pack(fill=tk.X, pady=(0, 8))
        ttk.Label(frame, text="Strategy").pack(anchor=tk.W)
        ttk.Combobox(
            frame,
            textvariable=self.strategy_var,
            values=[
                "focused",
                "learning_blend",
                "free_mode",
                "sat_psat_unit",
                "historical_practice",
            ],
            state="readonly",
        ).pack(fill=tk.X, pady=(0, 8))
        ttk.Label(frame, text="Number of Questions").pack(anchor=tk.W)
        int_spinbox(frame, self.num_var, 3, 20).pack(anchor=tk.W, pady=(0, 8))
        ttk.Label(frame, text="Level").pack(anchor=tk.W)
        int_spinbox(frame, self.level_var, 1, 3).pack(anchor=tk.W, pady=(0, 8))
        ttk.Checkbutton(
            frame,
            text="Vary numbers / avoid repeats in this session",
            variable=self.vary_numbers_var,
        ).pack(anchor=tk.W, pady=(0, 8))
        ttk.Button(frame, text="Start Quiz", command=self.start_quiz).pack(
            fill=tk.X, pady=(6, 12)
        )
        self.explain = ExplanationPanel(frame)
        self.explain.set_explanation(QUIZ_EXPLANATION)
        self.explain.frame.pack(fill=tk.X, pady=(12, 0))
        self._update_curriculum_label()
        self._refresh_subskills()
        self._refresh_historical_tests()
        self._apply_track_filter()

    def _build_view(self) -> None:
        self.prompt_var = tk.StringVar(
            value="Choose settings on the left to start a quiz."
        )
        ttk.Label(
            self.view_frame,
            textvariable=self.prompt_var,
            font=("Helvetica", 14, "bold"),
        ).pack(pady=12)
        self.meta_var = tk.StringVar(value="")
        ttk.Label(
            self.view_frame, textvariable=self.meta_var, foreground="#2d5d7c"
        ).pack(pady=(0, 4))
        self.visual_canvas = tk.Canvas(
            self.view_frame, bg="#f7f7f7", height=260
        )
        self.visual_canvas.pack(fill=tk.X, padx=16)
        self.answer_frame = ttk.Frame(self.view_frame)
        self.answer_frame.pack(fill=tk.X, padx=16, pady=10)
        self.answer_var = tk.StringVar(value="")
        self.choice_var = tk.StringVar(value="")
        self.repeat_var = tk.BooleanVar(value=False)
        self.feedback_var = tk.StringVar(value="")
        ttk.Label(
            self.view_frame, textvariable=self.feedback_var, foreground="#2f6f3e"
        ).pack(pady=(6, 4))
        self.intuition_var = tk.StringVar(value="")
        ttk.Label(
            self.view_frame,
            textvariable=self.intuition_var,
            foreground="#2d5d7c",
            wraplength=780,
        ).pack(pady=(0, 4))
        self.recovery_var = tk.StringVar(value="")
        ttk.Label(
            self.view_frame,
            textvariable=self.recovery_var,
            foreground="#704c16",
            wraplength=780,
            justify=tk.LEFT,
        ).pack(fill=tk.X, padx=16, pady=(0, 4))

        buttons = ttk.Frame(self.view_frame)
        buttons.pack(pady=6)
        self.submit_btn = ttk.Button(
            buttons, text="Submit", command=self.submit_answer
        )
        self.stuck_btn = ttk.Button(
            buttons, text="Show intuition (I'm stuck)", command=self._show_intuition
        )
        self.next_btn = ttk.Button(buttons, text="Next", command=self.next_question)
        for button in (self.submit_btn, self.stuck_btn, self.next_btn):
            button.pack(side=tk.LEFT, padx=4)
        self.next_btn.state(["disabled"])
        self.stuck_btn.state(["disabled"])
        self.summary_box = tk.Text(
            self.view_frame, height=8, wrap=tk.WORD, font=("Helvetica", 10)
        )
        self.summary_box.pack(fill=tk.BOTH, expand=True, padx=16, pady=8)
        self.summary_box.config(state=tk.DISABLED)
