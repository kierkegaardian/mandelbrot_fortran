from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from .ui_arithmetic import ArithmeticPanel
from .ui_dashboard import DashboardPanel
from .ui_fractals import FractalPanel
from .ui_parent import ParentPanel
from .ui_quiz import QuizPanel
from .ui_skill_map import SkillMapPanel


class AppShell:
    def __init__(self, root: tk.Tk, profile) -> None:
        self.root = root
        self.profile = profile

        self.root.title("MandelQuest")
        self.root.geometry("1200x720")

        self._build_header()
        self._build_layout()

    def _build_header(self) -> None:
        bar = ttk.Frame(self.root)
        bar.pack(fill=tk.X)
        self.profile_var = tk.StringVar(value=f"Profile: {self.profile.name}")
        ttk.Label(bar, textvariable=self.profile_var, font=("Helvetica", 11, "bold")).pack(side=tk.LEFT, padx=10, pady=6)

    def _build_layout(self) -> None:
        self.paned = ttk.Panedwindow(self.root, orient=tk.HORIZONTAL)
        self.paned.pack(fill=tk.BOTH, expand=True)

        self.left_panel = ttk.Frame(self.paned, width=320)
        self.right_panel = ttk.Frame(self.paned)
        self.paned.add(self.left_panel, weight=1)
        self.paned.add(self.right_panel, weight=3)

        self.notebook = ttk.Notebook(self.left_panel)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        self.view_stack = ttk.Frame(self.right_panel)
        self.view_stack.pack(fill=tk.BOTH, expand=True)
        self.view_stack.rowconfigure(0, weight=1)
        self.view_stack.columnconfigure(0, weight=1)

        self.fractal = FractalPanel(self.notebook, self.view_stack)
        self.arithmetic = ArithmeticPanel(self.notebook, self.view_stack)
        self.quiz = QuizPanel(self.notebook, self.view_stack, self.get_profile)
        self.parent = ParentPanel(self.notebook, self.view_stack, self.get_profile, self.launch_quiz_set)
        self.dashboard = DashboardPanel(
            self.notebook,
            self.view_stack,
            self.get_profile,
            self.launch_daily_review,
            self.launch_assignment_quiz,
        )
        self.skill_map = SkillMapPanel(
            self.notebook,
            self.view_stack,
            self.get_profile,
            self.launch_skill_map_quiz,
        )

        self._modules = [
            ("Fractals", self.fractal),
            ("Math Skills", self.arithmetic),
            ("Quizzes", self.quiz),
            ("Parent", self.parent),
            ("Dashboard", self.dashboard),
            ("Skill Map", self.skill_map),
        ]

        for name, module in self._modules:
            self.notebook.add(module.controls_frame, text=name)
            module.view_frame.grid(row=0, column=0, sticky="nsew")

        self.notebook.bind("<<NotebookTabChanged>>", self._on_tab_changed)
        self._show_module(0)

    def _on_tab_changed(self, _event) -> None:
        idx = self.notebook.index(self.notebook.select())
        self._show_module(idx)

    def _show_module(self, idx: int) -> None:
        module = self._modules[idx][1]
        module.view_frame.tkraise()
        if hasattr(module, "render"):
            module.render()

    def get_profile(self):
        return self.profile

    def launch_daily_review(self, skill: str, subskill: str | None) -> None:
        self.notebook.select(self.quiz.controls_frame)
        self.quiz.apply_preset(
            track="All",
            skill=skill,
            subskill=subskill,
            num_questions=5,
            level=1,
            question_type="both",
            launch_context="daily_review",
        )
        self.quiz.start_quiz()

    def launch_assignment_quiz(
        self,
        skill: str,
        subskill: str | None,
        level: int,
        num_questions: int,
        question_type: str,
        mode_intuition_pct: int | None = None,
        mode_expression_pct: int | None = None,
        mode_word_pct: int | None = None,
    ) -> None:
        self.notebook.select(self.quiz.controls_frame)
        mode_mix = None
        if mode_intuition_pct is not None and mode_expression_pct is not None and mode_word_pct is not None:
            mode_mix = (int(mode_intuition_pct), int(mode_expression_pct), int(mode_word_pct))
        self.quiz.apply_preset(
            track="All",
            skill=skill,
            subskill=subskill,
            num_questions=num_questions,
            level=level,
            question_type=question_type,
            strategy="learning_blend",
            mode_mix_override=mode_mix,
            launch_context="assignment",
        )
        self.quiz.start_quiz()

    def launch_quiz_set(
        self,
        skill: str,
        num_questions: int,
        level: int,
        question_type: str,
        mode_intuition_pct: int | None = None,
        mode_expression_pct: int | None = None,
        mode_word_pct: int | None = None,
    ) -> None:
        self.notebook.select(self.quiz.controls_frame)
        mode_mix = None
        if mode_intuition_pct is not None and mode_expression_pct is not None and mode_word_pct is not None:
            mode_mix = (int(mode_intuition_pct), int(mode_expression_pct), int(mode_word_pct))
        self.quiz.apply_preset(
            track="All",
            skill=skill,
            subskill="Any",
            num_questions=num_questions,
            level=level,
            question_type=question_type,
            strategy="focused",
            mode_mix_override=mode_mix,
            launch_context="quiz_set",
        )
        self.quiz.start_quiz()

    def launch_skill_map_quiz(self, skill: str) -> None:
        self.notebook.select(self.quiz.controls_frame)
        self.quiz.apply_preset(
            track="All",
            skill=skill,
            subskill="Any",
            num_questions=5,
            level=1,
            question_type="both",
            strategy="learning_blend",
            launch_context="skill_map",
        )
        self.quiz.start_quiz()

    def shutdown(self) -> None:
        if hasattr(self.fractal, "shutdown"):
            self.fractal.shutdown()
