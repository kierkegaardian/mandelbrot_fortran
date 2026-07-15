from __future__ import annotations

from collections.abc import Callable
import tkinter as tk
from tkinter import ttk

from .models import Assignment, Profile
from .skill_graph import SKILL_LABELS, SKILL_ORDER
from .theme import COLORS, FONTS, MASTERY_COLORS
from .ui_dashboard_render import DashboardRenderMixin

ProfileGetter = Callable[[], Profile | None]
QuizLauncher = Callable[[str, str | None], None]
AssignmentLauncher = Callable[..., None]


class DashboardPanel(DashboardRenderMixin):
    def __init__(
        self,
        controls_parent: tk.Widget,
        view_parent: tk.Widget,
        profile_getter: ProfileGetter,
        quiz_launcher: QuizLauncher | None = None,
        assignment_launcher: AssignmentLauncher | None = None,
    ) -> None:
        self.controls_frame = ttk.Frame(controls_parent)
        self.view_frame = ttk.Frame(view_parent)
        self._profile_getter = profile_getter
        self._quiz_launcher = quiz_launcher
        self._assignment_launcher = assignment_launcher
        self._daily_target: tuple[str, str] | None = None
        self._assignment_target: Assignment | None = None
        self._build_controls()
        self._build_view()

    def _build_controls(self) -> None:
        frame = ttk.Frame(self.controls_frame, padding=10)
        frame.pack(fill=tk.BOTH, expand=True)
        ttk.Label(
            frame, text="Student Dashboard", font=FONTS["subheading"]
        ).pack(anchor=tk.W, pady=(0, 6))
        ttk.Label(
            frame,
            text="See progress, mastery level, and suggested next skills.",
            wraplength=260,
        ).pack(anchor=tk.W, pady=(0, 8))
        ttk.Button(frame, text="Refresh", command=self.render).pack(anchor=tk.W)
        self.daily_btn = ttk.Button(
            frame,
            text="Start Daily Review",
            style="Accent.TButton",
            command=self._start_daily_review,
        )
        self.daily_btn.pack(anchor=tk.W, pady=(8, 0))
        self.assignment_btn = ttk.Button(
            frame,
            text="Start Assignment",
            command=self._start_assignment,
        )
        self.assignment_btn.pack(anchor=tk.W, pady=(8, 0))

    def _build_view(self) -> None:
        header = ttk.Frame(self.view_frame)
        header.pack(fill=tk.X, pady=(10, 6))
        self.summary_var = tk.StringVar(value="No data yet.")
        ttk.Label(
            header, textvariable=self.summary_var, font=FONTS["subheading"]
        ).pack(anchor=tk.W, padx=10)

        self.tiles_frame = ttk.Frame(self.view_frame)
        self.tiles_frame.pack(fill=tk.X, padx=10, pady=(0, 6))
        self.tile_vars: dict[str, tk.StringVar] = {}
        for label, color in MASTERY_COLORS.items():
            tile = tk.Frame(self.tiles_frame, bg=color, bd=1, relief=tk.RIDGE)
            tile.pack(side=tk.LEFT, padx=4, pady=2, ipadx=6, ipady=4)
            value = tk.StringVar(value=f"{label}: 0")
            tk.Label(
                tile,
                textvariable=value,
                bg=color,
                fg=COLORS["text_primary"],
                font=FONTS["small"] + ("bold",),
            ).pack()
            self.tile_vars[label] = value

        self.progress_frame = ttk.Frame(self.view_frame)
        self.progress_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=4)
        self.progress_rows: dict[str, dict[str, object]] = {}
        for skill in SKILL_ORDER:
            row = ttk.Frame(self.progress_frame)
            row.pack(fill=tk.X, pady=2)
            ttk.Label(
                row, text=SKILL_LABELS.get(skill, skill), width=18
            ).pack(side=tk.LEFT)
            progress_var = tk.DoubleVar(value=0)
            progress_bar = ttk.Progressbar(
                row, variable=progress_var, maximum=100
            )
            progress_bar.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=6)
            percent_var = tk.StringVar(value="0%")
            ttk.Label(row, textvariable=percent_var, width=6).pack(side=tk.LEFT)
            mastery_var = tk.StringVar(value="Not started")
            ttk.Label(
                row, textvariable=mastery_var, width=12
            ).pack(side=tk.LEFT, padx=(6, 0))
            self.progress_rows[skill] = {
                "progress_var": progress_var,
                "progress_bar": progress_bar,
                "percent_var": percent_var,
                "mastery_var": mastery_var,
            }

        self._build_status_labels()

    def _build_status_labels(self) -> None:
        specs = (
            ("reco_var", "Recommended next: —", COLORS["accent_strong"]),
            ("reco_detail_var", "", COLORS["text_secondary"]),
            ("subskill_var", "", COLORS["text_secondary"]),
            ("daily_var", "Daily review: —", COLORS["success"]),
            ("assignment_var", "Assignment: —", COLORS["assignment"]),
        )
        for attr, initial, color in specs:
            value = tk.StringVar(value=initial)
            setattr(self, attr, value)
            ttk.Label(
                self.view_frame,
                textvariable=value,
                foreground=color,
                wraplength=520,
            ).pack(anchor=tk.W, padx=10, pady=(0, 10))

    def _refresh_shortcut(self) -> None:
        self.render()

    def _daily_shortcut(self) -> None:
        self._start_daily_review()

    def _assignment_shortcut(self) -> None:
        self._start_assignment()

    def focus_primary_control(self) -> None:
        self.daily_btn.focus_set()

    def on_module_activated(self) -> None:
        self.render()

    def _start_daily_review(self) -> None:
        if self._quiz_launcher is None or self._daily_target is None:
            return
        skill, subskill = self._daily_target
        self._quiz_launcher(skill, subskill)

    def _start_assignment(self) -> None:
        if self._assignment_launcher is None or self._assignment_target is None:
            return
        assignment = self._assignment_target
        self._assignment_launcher(
            assignment.skill,
            assignment.subskill,
            assignment.level,
            assignment.num_questions,
            assignment.question_type,
            assignment.mode_intuition_pct,
            assignment.mode_expression_pct,
            assignment.mode_word_pct,
        )
