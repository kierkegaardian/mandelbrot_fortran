from __future__ import annotations

from datetime import datetime, timezone
import tkinter as tk
from tkinter import ttk

from . import db, school_year, summer_program
from .learning_engine import build_skill_stats, recommend_next_skill_paths
from .skill_graph import (
    SKILL_LABELS,
    SKILL_ORDER,
    SKILL_PREREQUISITE_WEIGHTS,
    SUBSKILL_STREAK_TO_MASTER,
    subskills_for,
)
from .summer_mode import filter_skills
from .summer_program_defs import is_optional_unit, lane_display_name, task_kind_label, unit_label
from .theme import COLORS, FONTS, MASTERY_COLORS, progress_style_for_mastery
from .ui_settings import load_ui_settings


class DashboardPanel:
    def __init__(
        self,
        controls_parent: tk.Widget,
        view_parent: tk.Widget,
        profile_getter,
        quiz_launcher=None,
        assignment_launcher=None,
        summer_program_task_launcher=None,
        bonus_launcher=None,
    ) -> None:
        self.controls_frame = ttk.Frame(controls_parent)
        self.view_frame = ttk.Frame(view_parent)
        self._profile_getter = profile_getter
        self._quiz_launcher = quiz_launcher
        self._assignment_launcher = assignment_launcher
        self._summer_program_task_launcher = summer_program_task_launcher
        self._bonus_launcher = bonus_launcher
        self._daily_target: tuple[str, str] | None = None
        self._assignment_target = None
        self._summer_program_task = None
        self._practice_target: tuple[str, int] | None = None
        self._school_goal_target: tuple[str, str, int] | None = None
        self._visible_skills: tuple[str, ...] = tuple(SKILL_ORDER)

        self._build_controls()
        self._build_view()

    def _build_controls(self) -> None:
        frame = ttk.Frame(self.controls_frame, padding=10)
        frame.pack(fill=tk.BOTH, expand=True)
        self.heading_var = tk.StringVar(value="Student Dashboard")
        ttk.Label(frame, textvariable=self.heading_var, font=FONTS["heading"]).pack(anchor=tk.W, pady=(0, 6))
        self.helper_var = tk.StringVar(value="See progress, mastery level, and suggested next skills.")
        ttk.Label(
            frame,
            textvariable=self.helper_var,
            wraplength=260,
        ).pack(anchor=tk.W, pady=(0, 8))
        self.refresh_btn = ttk.Button(frame, text="Refresh", command=self.render)
        self.refresh_btn.pack(anchor=tk.W)
        self.daily_btn = ttk.Button(frame, text="Start Daily Review", command=self._start_daily_review)
        self.daily_btn.pack(anchor=tk.W, pady=(8, 0))
        self.assignment_btn = ttk.Button(frame, text="Start Assignment", command=self._start_assignment)
        self.assignment_btn.pack(anchor=tk.W, pady=(8, 0))
        self.practice_btn_pack = {"anchor": tk.W, "pady": (8, 0)}
        self.assignment_btn_pack = {"anchor": tk.W, "pady": (8, 0)}

    def _build_view(self) -> None:
        # --- Welcome card (shown for new profiles with 0 attempts) ---
        self.welcome_frame = tk.Frame(
            self.view_frame, bg="#e8f0fe", bd=1, relief=tk.RIDGE,
            highlightbackground=COLORS["accent"], highlightthickness=1,
        )
        ttk.Label(
            self.welcome_frame,
            text="🎯 Welcome to MandelQuest!",
            font=FONTS["heading"],
            background="#e8f0fe",
        ).pack(anchor=tk.W, padx=14, pady=(12, 4))
        ttk.Label(
            self.welcome_frame,
            text="Start with a quick Counting quiz to see how practice works.",
            background="#e8f0fe",
            wraplength=500,
        ).pack(anchor=tk.W, padx=14, pady=(0, 8))
        self.welcome_start_btn = ttk.Button(
            self.welcome_frame,
            text="▶ Start First Quiz",
            style="Accent.TButton",
            command=self._start_welcome_quiz,
        )
        self.welcome_start_btn.pack(anchor=tk.W, padx=14, pady=(0, 12))
        # Initially hidden; render() shows/hides it

        self.header_frame = ttk.Frame(self.view_frame)
        self.header_frame.pack(fill=tk.X, pady=(10, 6))
        self.summary_var = tk.StringVar(value="No data yet.")
        ttk.Label(self.header_frame, textvariable=self.summary_var, font=FONTS["heading"]).pack(anchor=tk.W, padx=10)

        self.child_next_frame = tk.Frame(
            self.view_frame,
            bg="#e8f7f0",
            bd=1,
            relief=tk.RIDGE,
            highlightbackground=COLORS["success"],
            highlightthickness=1,
        )
        self.child_next_title_var = tk.StringVar(value="Today's Next Step")
        tk.Label(
            self.child_next_frame,
            textvariable=self.child_next_title_var,
            bg="#e8f7f0",
            fg=COLORS["text_primary"],
            font=FONTS["subheading"],
        ).pack(anchor=tk.W, padx=14, pady=(12, 4))
        self.child_next_detail_var = tk.StringVar(value="")
        tk.Label(
            self.child_next_frame,
            textvariable=self.child_next_detail_var,
            bg="#e8f7f0",
            fg=COLORS["text_primary"],
            wraplength=620,
            justify=tk.LEFT,
        ).pack(anchor=tk.W, padx=14, pady=(0, 6))
        self.child_progress_var = tk.StringVar(value="")
        tk.Label(
            self.child_next_frame,
            textvariable=self.child_progress_var,
            bg="#e8f7f0",
            fg=COLORS["text_secondary"],
            wraplength=620,
            justify=tk.LEFT,
        ).pack(anchor=tk.W, padx=14, pady=(0, 8))
        self.child_goal_focus_var = tk.StringVar(value="")
        tk.Label(
            self.child_next_frame,
            textvariable=self.child_goal_focus_var,
            bg="#e8f7f0",
            fg=COLORS["text_primary"],
            wraplength=620,
            justify=tk.LEFT,
        ).pack(anchor=tk.W, padx=14, pady=(0, 8))
        self.child_next_btn = ttk.Button(
            self.child_next_frame,
            text="Start Next Step",
            style="Accent.TButton",
            command=self._start_daily_review,
        )
        self.child_next_btn.pack(anchor=tk.W, padx=14, pady=(0, 12))
        self.child_next_frame.pack_forget()

        self.tiles_frame = ttk.Frame(self.view_frame)
        self.tiles_frame.pack(fill=tk.X, padx=10, pady=(0, 6))
        self.tile_vars: dict[str, tk.StringVar] = {}
        tile_specs = [(label, MASTERY_COLORS[label]) for label in ("Not started", "Needs work", "Developing", "Proficient", "Mastered")]
        for label, color in tile_specs:
            tile = tk.Frame(self.tiles_frame, bg=color, bd=1, relief=tk.RIDGE)
            tile.pack(side=tk.LEFT, padx=4, pady=2, ipadx=6, ipady=4)
            var = tk.StringVar(value=f"{label}: 0")
            tk.Label(tile, textvariable=var, bg=color, fg=COLORS["text_primary"], font=FONTS["small"]).pack()
            self.tile_vars[label] = var

        self.progress_frame = ttk.Frame(self.view_frame)
        self.progress_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=4)
        self.progress_rows: dict[str, dict[str, object]] = {}
        columns = 3
        for i, skill in enumerate(SKILL_ORDER):
            r, c = divmod(i, columns)
            # Use tk.Frame for border/bg control
            card = tk.Frame(self.progress_frame, bg="#ffffff", bd=1, relief=tk.SOLID)
            card.grid(row=r, column=c, padx=6, pady=6, sticky="nsew")
            self.progress_frame.columnconfigure(c, weight=1)

            card_inner = tk.Frame(card, bg="#ffffff", padx=8, pady=6)
            card_inner.pack(fill=tk.BOTH, expand=True)

            ttk.Label(card_inner, text=SKILL_LABELS.get(skill, skill), font=("Segoe UI", 10, "bold"), background="#ffffff").pack(anchor=tk.W)

            bar_row = tk.Frame(card_inner, bg="#ffffff")
            bar_row.pack(fill=tk.X, pady=(4, 2))
            progress_var = tk.DoubleVar(value=0)
            bar = ttk.Progressbar(bar_row, variable=progress_var, maximum=100, style="TProgressbar")
            bar.pack(side=tk.LEFT, fill=tk.X, expand=True)
            percent_var = tk.StringVar(value="0%")
            ttk.Label(bar_row, textvariable=percent_var, font=("Segoe UI", 9), background="#ffffff").pack(side=tk.LEFT, padx=(6, 0))

            mastery_var = tk.StringVar(value="Not started")
            ttk.Label(card_inner, textvariable=mastery_var, font=("Segoe UI", 9, "italic"), background="#ffffff", foreground=COLORS["text_secondary"]).pack(anchor=tk.W)

            self.progress_rows[skill] = {
                "progress_var": progress_var,
                "percent_var": percent_var,
                "mastery_var": mastery_var,
                "bar": bar,
                "card": card,
            }

        # --- Recommendation row with Practice Now button ---
        self.reco_row = ttk.Frame(self.view_frame)
        self.reco_row.pack(fill=tk.X, padx=10, pady=(6, 2))
        self.reco_var = tk.StringVar(value="Recommended next: —")
        ttk.Label(self.reco_row, textvariable=self.reco_var, foreground=COLORS["accent_strong"]).pack(
            side=tk.LEFT,
        )
        self.practice_btn = ttk.Button(
            self.reco_row, text="▶ Practice Now", style="Accent.TButton",
            command=self._start_practice,
        )
        self.practice_btn.pack(side=tk.LEFT, padx=(12, 0))

        self.reco_detail_var = tk.StringVar(value="")
        self.reco_detail_label = ttk.Label(
            self.view_frame,
            textvariable=self.reco_detail_var,
            foreground=COLORS["text_secondary"],
            wraplength=520,
        )
        self.reco_detail_label.pack(
            anchor=tk.W, padx=10, pady=(0, 6)
        )
        self.subskill_var = tk.StringVar(value="")
        self.subskill_label = ttk.Label(
            self.view_frame,
            textvariable=self.subskill_var,
            foreground=COLORS["text_secondary"],
            wraplength=520,
        )
        self.subskill_label.pack(
            anchor=tk.W, padx=10, pady=(0, 6)
        )
        self.daily_var = tk.StringVar(value="Daily review: —")
        self.daily_label = ttk.Label(
            self.view_frame,
            textvariable=self.daily_var,
            foreground=COLORS["success"],
            wraplength=520,
        )
        self.daily_label.pack(
            anchor=tk.W, padx=10, pady=(0, 6)
        )
        self.assignment_var = tk.StringVar(value="Assignment: —")
        self.assignment_label = ttk.Label(
            self.view_frame,
            textvariable=self.assignment_var,
            foreground=COLORS["assignment"],
            wraplength=520,
        )
        self.assignment_label.pack(
            anchor=tk.W, padx=10, pady=(0, 6)
        )
        self.program_var = tk.StringVar(value="Summer program: —")
        self.program_label = ttk.Label(
            self.view_frame,
            textvariable=self.program_var,
            foreground=COLORS["accent_strong"],
            wraplength=520,
        )
        self.program_label.pack(
            anchor=tk.W, padx=10, pady=(0, 6)
        )
        self.school_year_var = tk.StringVar(value="School year: —")
        self.school_year_label = ttk.Label(
            self.view_frame,
            textvariable=self.school_year_var,
            foreground=COLORS["text_secondary"],
            wraplength=520,
        )
        self.school_year_label.pack(
            anchor=tk.W, padx=10, pady=(0, 6)
        )
        self.bonus_frame = tk.Frame(
            self.view_frame,
            bg="#fff7db",
            bd=1,
            relief=tk.RIDGE,
            highlightbackground=COLORS["accent"],
            highlightthickness=1,
        )
        self.bonus_var = tk.StringVar(value="Bonus Explore is locked until today's practice is done.")
        tk.Label(
            self.bonus_frame,
            text="Bonus Explore",
            bg="#fff7db",
            fg=COLORS["text_primary"],
            font=FONTS["subheading"],
        ).pack(anchor=tk.W, padx=14, pady=(12, 4))
        tk.Label(
            self.bonus_frame,
            textvariable=self.bonus_var,
            bg="#fff7db",
            fg=COLORS["text_secondary"],
            wraplength=520,
            justify=tk.LEFT,
        ).pack(anchor=tk.W, padx=14, pady=(0, 8))
        self.bonus_btn = ttk.Button(
            self.bonus_frame,
            text="Open Bonus Explore",
            command=self._start_bonus_explore,
        )
        self.bonus_btn.pack(anchor=tk.W, padx=14, pady=(0, 12))
        self.bonus_frame.pack_forget()

    def _refresh_shortcut(self) -> str:
        self.render()
        return "break"

    def _daily_shortcut(self) -> str:
        self._start_daily_review()
        return "break"

    def _assignment_shortcut(self) -> str:
        self._start_assignment()
        return "break"

    def focus_primary_control(self) -> None:
        self.refresh_btn.focus_set()

    def on_module_activated(self) -> None:
        self.focus_primary_control()

    def _start_daily_review(self) -> None:
        if self._summer_program_task is not None and self._summer_program_task_launcher is not None:
            self._summer_program_task_launcher(self._summer_program_task.id)
            return
        if self._quiz_launcher is None or self._daily_target is None:
            return
        skill, subskill = self._daily_target
        self._quiz_launcher(skill, subskill)

    def _start_practice(self) -> None:
        """Launch a learning-blend quiz for the top recommended skill."""
        if self._quiz_launcher is None or self._practice_target is None:
            return
        skill, _level = self._practice_target
        self._quiz_launcher(skill, None)

    def _start_school_year_goal(self) -> None:
        if self._quiz_launcher is None or self._school_goal_target is None:
            return
        skill, subskill, level = self._school_goal_target
        self._quiz_launcher(skill, subskill, level)

    def _start_welcome_quiz(self) -> None:
        """Launch a beginner counting quiz for first-time users."""
        if self._quiz_launcher is None:
            return
        self._quiz_launcher("counting", None)

    def _start_assignment(self) -> None:
        if self._assignment_launcher is None or self._assignment_target is None:
            return
        self._assignment_launcher(
            self._assignment_target.skill,
            self._assignment_target.subskill,
            self._assignment_target.level,
            self._assignment_target.num_questions,
            self._assignment_target.question_type,
            self._assignment_target.mode_intuition_pct,
            self._assignment_target.mode_expression_pct,
            self._assignment_target.mode_word_pct,
        )

    def _start_bonus_explore(self) -> None:
        if self._bonus_launcher is None:
            return
        self._bonus_launcher()

    def _configure_child_summer_layout(self, enabled: bool) -> None:
        profile = self._profile_getter()
        child_profile = bool(profile is not None and getattr(profile, "role", "") == "child")
        self.heading_var.set("Today's Math" if child_profile else "Student Dashboard")
        if enabled:
            self.helper_var.set("Start one short session first. Bonus Explore unlocks after today's practice.")
        elif child_profile:
            self.helper_var.set("Start a math session first. Bonus Explore unlocks after today's practice.")
        else:
            self.helper_var.set("See progress, mastery level, and suggested next skills.")
        self._configure_optional_sections(enabled)

    def _configure_optional_sections(self, child_summer: bool) -> None:
        for widget in (
            self.child_next_frame,
            self.tiles_frame,
            self.progress_frame,
            self.reco_row,
            self.reco_detail_label,
            self.subskill_label,
            self.daily_label,
            self.assignment_label,
            self.program_label,
            self.school_year_label,
        ):
            widget.pack_forget()
        if child_summer:
            self.child_next_frame.pack(fill=tk.X, padx=10, pady=(0, 8), after=self.header_frame)
            self.reco_row.pack(fill=tk.X, padx=10, pady=(6, 2))
            self.daily_label.pack(anchor=tk.W, padx=10, pady=(0, 6))
            self.program_label.pack(anchor=tk.W, padx=10, pady=(0, 6))
            self.school_year_label.pack(anchor=tk.W, padx=10, pady=(0, 6))
        else:
            self.tiles_frame.pack(fill=tk.X, padx=10, pady=(0, 6))
            self.progress_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=4)
            self.reco_row.pack(fill=tk.X, padx=10, pady=(6, 2))
            self.reco_detail_label.pack(anchor=tk.W, padx=10, pady=(0, 6))
            self.subskill_label.pack(anchor=tk.W, padx=10, pady=(0, 6))
            self.daily_label.pack(anchor=tk.W, padx=10, pady=(0, 6))
            self.assignment_label.pack(anchor=tk.W, padx=10, pady=(0, 6))
            self.program_label.pack(anchor=tk.W, padx=10, pady=(0, 6))
            self.school_year_label.pack(anchor=tk.W, padx=10, pady=(0, 6))
        if child_summer:
            self.practice_btn.pack_forget()
            self.assignment_btn.pack_forget()
        else:
            if not self.practice_btn.winfo_manager():
                self.practice_btn.pack(side=tk.LEFT, padx=(12, 0))
            if not self.assignment_btn.winfo_manager():
                self.assignment_btn.pack(**self.assignment_btn_pack)

    def _render_bonus_explore(self, *, child_profile: bool, unlocked: bool) -> None:
        if not child_profile or not unlocked:
            self.bonus_frame.pack_forget()
            return
        self.bonus_var.set(
            "Today's practice is done. Bonus Explore opens the Mandel viewer as a just-for-fun pattern lab."
        )
        self.bonus_btn.state(["!disabled"])
        self.bonus_frame.pack(fill=tk.X, padx=10, pady=(6, 8))

    def _render_child_next_step_card(
        self,
        *,
        child_profile: bool,
        profile_id: int,
        completed: int,
        total_visible: int,
        today_count: int,
    ) -> None:
        if not child_profile:
            self.child_next_frame.pack_forget()
            return
        if not self.child_next_frame.winfo_manager():
            self.child_next_frame.pack(fill=tk.X, padx=10, pady=(0, 8), after=self.header_frame)

        self._school_goal_target = None
        status = school_year.school_year_status(profile_id)
        if status is None:
            school_text = "Ask a parent to choose your Texas grade goal."
            focus_text = "Goal focus: ask a parent to choose your Texas grade target."
        elif status.next_goal is None:
            school_text = f"Texas Grade {status.target.grade}: all quiz-ready goals complete."
            focus_text = "Goal focus: all grade goals are complete; stretch practice can keep you moving."
        else:
            next_step = next((step for step in status.next_goal_steps if not step.mastered), None)
            try_text = next_step.subskill if next_step is not None else status.next_goal.label
            steps_text = _school_goal_steps_text(status.next_goal_steps)
            school_text = (
                f"Texas Grade {status.target.grade}: "
                f"{status.completed_count}/{status.total_count} goals complete; "
                f"next goal is {status.next_goal.label}."
            )
            focus_text = f"Why it matters: {status.next_goal.mental_model} Try this next: {try_text}."
            if steps_text:
                focus_text = f"{focus_text} {steps_text}"
            if status.next_goal.skill is not None and next_step is not None:
                self._school_goal_target = (
                    status.next_goal.skill,
                    next_step.subskill,
                    status.next_goal.quiz_level,
                )

        if self._summer_program_task is not None:
            title = "Today's Program Step"
            detail = self.daily_var.get().replace("Today's practice: ", "", 1)
            button_enabled = True
            button_text = "Start Next Step"
            button_command = self._start_daily_review
        elif self._assignment_target is not None:
            title = "Assignment Ready"
            detail = self.assignment_var.get().replace("Assignment: ", "", 1)
            button_enabled = True
            button_text = "Start Assignment"
            button_command = self._start_assignment
        elif self._school_goal_target is not None:
            skill, subskill, _level = self._school_goal_target
            title = "Next Texas Goal"
            detail = f"{SKILL_LABELS.get(skill, skill)}: {subskill}"
            button_enabled = True
            button_text = "Practice Next Goal"
            button_command = self._start_school_year_goal
        elif self._daily_target is not None:
            skill, subskill = self._daily_target
            title = "Today's Practice"
            detail = f"{SKILL_LABELS.get(skill, skill)}: {subskill}"
            button_enabled = True
            button_text = "Start Practice"
            button_command = self._start_daily_review
        else:
            title = "All Caught Up"
            detail = "You have no required practice waiting right now."
            button_enabled = False
            button_text = "Start Next Step"
            button_command = self._start_daily_review

        bonus_text = "Bonus Explore unlocked." if today_count > 0 else "Bonus Explore unlocks after practice."
        self.child_next_title_var.set(title)
        self.child_next_detail_var.set(detail)
        self.child_progress_var.set(
            f"Progress: {completed}/{total_visible} skills mastered. {school_text} {bonus_text}"
        )
        self.child_goal_focus_var.set(focus_text)
        self.child_next_btn.config(text=button_text, command=button_command)
        if button_enabled:
            self.child_next_btn.state(["!disabled"])
        else:
            self.child_next_btn.state(["disabled"])

    def render(self) -> None:
        settings = load_ui_settings()
        summer_mode = settings.summer_mode
        visible_skills = tuple(
            filter_skills(
                tuple(SKILL_ORDER),
                grade_band=settings.default_grade_band,
                summer_mode=summer_mode,
            )
        ) or ("counting",)
        self._visible_skills = visible_skills
        self.daily_btn.config(text="Start Today's Practice" if summer_mode else "Start Daily Review")
        self.practice_btn.config(text="▶ Keep Practicing" if summer_mode else "▶ Practice Now")
        profile = self._profile_getter()
        child_profile = bool(profile is not None and getattr(profile, "role", "") == "child")
        child_summer = bool(child_profile and summer_mode)
        self._configure_child_summer_layout(child_summer)
        if profile is None:
            self.welcome_frame.pack_forget()
            self.summary_var.set("No profile selected.")
            self.reco_var.set("Today's focus: —" if summer_mode else "Recommended next: —")
            self.reco_detail_var.set("")
            self.daily_var.set("Today's practice: —" if summer_mode else "Daily review: —")
            self.assignment_var.set("Assignment: —")
            self.program_var.set("Summer program: —")
            self.school_year_var.set("School year: —")
            self._render_bonus_explore(child_profile=False, unlocked=False)
            for skill, row in self.progress_rows.items():
                card: tk.Frame = row["card"]
                if skill in visible_skills:
                    card.grid()
                else:
                    card.grid_remove()
                row["progress_var"].set(0)
                row["percent_var"].set("0%")
                row["mastery_var"].set("Not started")
            for label, var in self.tile_vars.items():
                var.set(f"{label}: 0")
            self.daily_btn.state(["disabled"])
            self.assignment_btn.state(["disabled"])
            self.practice_btn.state(["disabled"])
            self._practice_target = None
            return
        attempts = db.list_attempts(profile.id)
        skill_stats = build_skill_stats(attempts, visible_skills)
        activity = db.skill_progress_pipeline(profile.id)
        stats = {
            skill: {"score": item.correct_questions, "total": item.total_questions, "attempts": item.attempts}
            for skill, item in skill_stats.items()
        }
        subskill_coverage = _subskill_coverage_by_skill(profile.id)
        today_count, streak = db.daily_goal_status(profile.id)

        mastery_map: dict[str, str] = {}
        counts = {label: 0 for label in self.tile_vars}
        for skill, row in self.progress_rows.items():
            card: tk.Frame = row["card"]
            if skill in visible_skills:
                card.grid()
            else:
                card.grid_remove()
                row["progress_var"].set(0)
                row["percent_var"].set("0%")
                row["mastery_var"].set("Not started")

        for skill in visible_skills:
            item = skill_stats.get(skill)
            if item is None:
                avg = 0.0
                mastery = "Not started"
            else:
                avg = item.weighted_accuracy
                mastery = item.mastery
            mastery_map[skill] = mastery
            if mastery in counts:
                counts[mastery] += 1
            row = self.progress_rows.get(skill)
            if row:
                row["progress_var"].set(avg)
                row["percent_var"].set(f"{avg:.0f}%")
                row["mastery_var"].set(mastery)
                row["bar"].configure(style=progress_style_for_mastery(mastery))
                card: tk.Frame = row["card"]
                card.configure(bg=MASTERY_COLORS.get(mastery, "#ffffff"))

        for label, var in self.tile_vars.items():
            var.set(f"{label}: {counts.get(label, 0)}")

        completed = sum(1 for s in visible_skills if mastery_map.get(s) == "Mastered")
        solid = sum(1 for s in visible_skills if mastery_map.get(s) in {"Proficient", "Mastered"})
        total_questions = sum(activity.get(skill, {}).get("questions", 0) for skill in visible_skills)
        total_worksheets = sum(activity.get(skill, {}).get("worksheets", 0) for skill in visible_skills)

        # UX2: Show/hide welcome card for new profiles
        if total_questions == 0:
            self.welcome_frame.pack(fill=tk.X, padx=10, pady=(8, 4), before=self.header_frame)
        else:
            self.welcome_frame.pack_forget()

        if child_summer:
            self.summary_var.set(f"{profile.name}: one clear step today, then a bonus explore unlock.")
        elif summer_mode:
            self.summary_var.set(
                f"{profile.name}: {solid}/{len(visible_skills)} skills feeling solid • {total_questions} quiz Qs"
            )
        else:
            # UX9: Dynamic XP calculation
            xp = (total_questions * 10) + (completed * 200) + (total_worksheets * 50)
            self.summary_var.set(
                f"{profile.name}: {completed}/{len(visible_skills)} mastered • {total_questions} quiz Qs • 🌟 {xp} XP"
            )
        branch_recommendations = recommend_next_skill_paths(
            visible_skills,
            SKILL_PREREQUISITE_WEIGHTS,
            skill_stats,
            subskill_coverage=subskill_coverage,
        )
        recommendations = [item.skill for item in branch_recommendations]
        if recommendations:
            labels = [SKILL_LABELS.get(skill, skill) for skill in recommendations]
            reco_prefix = "Today's focus" if summer_mode else "Recommended next"
            self.reco_var.set(f"{reco_prefix}: {', '.join(labels)}")
            reason_lines: list[str] = []
            for item in branch_recommendations[:3]:
                label = SKILL_LABELS.get(item.skill, item.skill)
                reason = item.reasons[0] if item.reasons else "Strong next step."
                reason_lines.append(f"{label}: {reason}")
            detail_prefix = "Practice path" if summer_mode else "Branch paths"
            self.reco_detail_var.set(f"{detail_prefix}: " + " | ".join(reason_lines))
            top_recommendation = recommendations[0]
            # UX3: enable Practice Now button with the top recommendation
            top_item = skill_stats.get(top_recommendation)
            reco_level = 1
            if top_item is not None and top_item.weighted_accuracy >= 70:
                reco_level = 2
            self._practice_target = (top_recommendation, reco_level)
            if self._quiz_launcher is not None:
                self.practice_btn.state(["!disabled"])
            else:
                self.practice_btn.state(["disabled"])
            subskills = subskills_for(top_recommendation)
            progress = {
                item.subskill: item
                for item in db.list_subskill_progress(profile.id, top_recommendation)
            }
            if subskills:
                subskill_status: list[str] = []
                for subskill in subskills:
                    item = progress.get(subskill)
                    if item is None:
                        icon = "◻"
                    elif item.mastered:
                        icon = "🏅"
                    elif item.current_streak > 0:
                        icon = _streak_graph(item.current_streak, SUBSKILL_STREAK_TO_MASTER)
                    else:
                        icon = _streak_graph(0, SUBSKILL_STREAK_TO_MASTER)
                    subskill_status.append(f"{icon} {subskill}")
                subskill_prefix = "Small steps" if summer_mode else "Subskills to build"
                self.subskill_var.set(f"{subskill_prefix}: " + " • ".join(subskill_status))
            else:
                self.subskill_var.set("")
        else:
            self.reco_var.set("Today's focus: Mixed review" if summer_mode else "Recommended next: Mixed review")
            self.reco_detail_var.set("")
            self.subskill_var.set("")
            self._practice_target = None
            self.practice_btn.state(["disabled"])

        program_active = False
        if summer_mode:
            program_active = self._render_summer_program(profile.id)
        if not program_active:
            self._render_daily_review(profile.id, mastery_map, stats, recommendations, visible_skills, summer_mode)
        self._render_assignment(profile.id)
        self._render_school_year(profile.id)
        self._render_child_next_step_card(
            child_profile=child_profile,
            profile_id=profile.id,
            completed=completed,
            total_visible=len(visible_skills),
            today_count=today_count,
        )
        self._render_bonus_explore(child_profile=child_profile, unlocked=today_count > 0)

    def _render_summer_program(self, profile_id: int) -> bool:
        program = summer_program.get_active_summer_program(profile_id)
        self._summer_program_task = None
        self._daily_target = None
        if program is None:
            self.program_var.set("Summer program: none active")
            return False
        summary = summer_program.summer_program_status_summary(profile_id, program.id)
        if summary is None:
            self.program_var.set("Summer program: none active")
            return False
        task = summary.current_task
        if task is None:
            self.program_var.set(
                f"Summer program: {lane_display_name(program.lane)} • Pace: {summary.pace_label} • Finish: {summary.finish_state}"
            )
            self.daily_var.set("Today's practice: Summer program complete")
            self.daily_btn.state(["disabled"])
            return True
        launch_task = summer_program.launchable_summer_program_task(program.id)
        self._summer_program_task = launch_task
        preview_task = is_optional_unit(program.lane, task.unit_code) and summary.finish_state == "completed"
        next_task_label = task_kind_label(task.task_kind)
        if summary.current_blocker == "awaiting_parent_review":
            next_task_label = "Parent review needed"
        elif summary.current_blocker == "checkpoint_below_target":
            next_task_label = "Retry checkpoint"
        elif summary.current_blocker == "midpoint_below_target":
            next_task_label = "Retry midpoint"
        elif summary.current_blocker == "exit_below_target":
            next_task_label = "Retry exit"
        unit_prefix = "Bonus preview" if preview_task else "Current unit"
        self.program_var.set(
            "Summer program: "
            f"{lane_display_name(program.lane)} • {unit_prefix}: {unit_label(program.lane, task.unit_code)} • "
            f"Next task: {next_task_label} • Pace: {summary.pace_label} • Finish: {summary.finish_state}"
        )
        if summary.projected_finish_note and not preview_task:
            self.program_var.set(f"{self.program_var.get()} • {summary.projected_finish_note}")
        if summary.catch_up_note and not preview_task:
            self.program_var.set(f"{self.program_var.get()} • {summary.catch_up_note}")
        if summary.current_blocker == "awaiting_parent_review":
            self.daily_var.set("Today's practice: Parent review needed after placement")
            self.daily_btn.config(text="Waiting On Parent Review")
        elif preview_task:
            self.daily_var.set(f"Today's practice: Bonus preview • {unit_label(program.lane, task.unit_code)}")
            self.daily_btn.config(text="Retry Bonus Preview" if task.status == "blocked" else "Start Bonus Preview")
        elif summary.current_blocker in {"checkpoint_below_target", "midpoint_below_target", "exit_below_target"}:
            detail = summary.remediation_note or next_task_label
            self.daily_var.set(
                f"Today's practice: {unit_label(program.lane, task.unit_code)} • {detail}"
            )
            self.daily_btn.config(text="Retry Program Task")
        else:
            detail = summary.remediation_note or task_kind_label(task.task_kind)
            self.daily_var.set(
                f"Today's practice: {unit_label(program.lane, task.unit_code)} • {detail}"
            )
            self.daily_btn.config(text="Start Today's Program")
        if not preview_task and summary.catch_up_note and summary.catch_up_note not in self.daily_var.get():
            self.daily_var.set(f"{self.daily_var.get()} • {summary.catch_up_note}")
        if not preview_task and summary.projected_finish_note and summary.projected_finish_note not in self.daily_var.get():
            self.daily_var.set(f"{self.daily_var.get()} • {summary.projected_finish_note}")
        if self._summer_program_task_launcher is None or launch_task is None:
            self.daily_btn.state(["disabled"])
        else:
            self.daily_btn.state(["!disabled"])
        return True

    def _render_daily_review(
        self,
        profile_id: int,
        mastery_map: dict[str, str],
        stats: dict[str, dict],
        recommendations: list[str],
        visible_skills: tuple[str, ...],
        summer_mode: bool,
    ) -> None:
        now = datetime.now(timezone.utc)
        started = {skill for skill in visible_skills if int(stats.get(skill, {}).get("attempts", 0)) > 0}
        solid = {skill for skill in visible_skills if mastery_map.get(skill) in {"Proficient", "Mastered"}}
        candidate_skills = started | solid | set(recommendations)
        if not candidate_skills:
            candidate_skills = {"counting"}

        progress = {
            (item.skill, item.subskill): item for item in db.list_subskill_progress(profile_id)
        }

        due: list[tuple[int, int, str, str, str]] = []
        # tuple: (priority, age_days, skill, subskill, status_text)
        for skill in visible_skills:
            if skill not in candidate_skills:
                continue
            for subskill in subskills_for(skill):
                item = progress.get((skill, subskill))
                if item is None:
                    due.append((0, 9999, skill, subskill, "new practice" if summer_mode else "new"))
                    continue
                try:
                    updated = datetime.fromisoformat(item.updated_at)
                except (ValueError, TypeError):
                    continue
                if updated.tzinfo is None:
                    updated = updated.replace(tzinfo=timezone.utc)
                age_days = int((now - updated).total_seconds() // 86400)
                if item.mastered and age_days >= 21:
                    label = f"refresh {age_days}d" if summer_mode else f"maintenance {age_days}d"
                    due.append((3, age_days, skill, subskill, label))
                elif (not item.mastered) and item.current_streak <= 0 and age_days >= 3:
                    label = f"restart {age_days}d" if summer_mode else f"rebuild {age_days}d"
                    due.append((1, age_days, skill, subskill, label))
                elif (not item.mastered) and item.current_streak < SUBSKILL_STREAK_TO_MASTER and age_days >= 5:
                    label = f"keep going {age_days}d" if summer_mode else f"streak {age_days}d"
                    due.append((2, age_days, skill, subskill, label))
                elif (not item.mastered) and age_days >= 10:
                    label = f"review {age_days}d" if summer_mode else f"stale {age_days}d"
                    due.append((3, age_days, skill, subskill, label))

        today_count, streak = db.daily_goal_status(profile_id)
        goal_text = (
            f"Practice streak: {streak} day(s), today: {today_count} session(s)"
            if summer_mode
            else f"Goal streak: {streak} day(s), today: {today_count} review(s)"
        )
        daily_prefix = "Today's practice" if summer_mode else "Daily review"

        if not due:
            self._daily_target = None
            self.daily_var.set(f"{daily_prefix}: all caught up • {goal_text}")
            self.daily_btn.state(["disabled"])
            return

        due.sort(key=lambda t: (t[0], -t[1], visible_skills.index(t[2])))
        _priority, _age, skill, subskill, status = due[0]
        self._daily_target = (skill, subskill)
        self.daily_var.set(f"{daily_prefix}: {SKILL_LABELS.get(skill, skill)} – {subskill} ({status}) • {goal_text}")
        if self._quiz_launcher is None:
            self.daily_btn.state(["disabled"])
        else:
            self.daily_btn.state(["!disabled"])

    def _render_assignment(self, profile_id: int) -> None:
        assignment = db.get_next_active_assignment(profile_id)
        self._assignment_target = assignment
        if assignment is None:
            self.assignment_var.set("Assignment: none active")
            self.assignment_btn.state(["disabled"])
            return
        target = assignment.target_type
        if target == "quiz_score_pct":
            target_text = "score = 100%"
        elif target == "subskill_mastered":
            target_text = "master subskill"
        else:
            target_text = target
        detail = f"{SKILL_LABELS.get(assignment.skill, assignment.skill)}"
        if assignment.subskill:
            detail += f" – {assignment.subskill}"
        self.assignment_var.set(f"Assignment: {detail} ({target_text})")
        if self._assignment_launcher is None:
            self.assignment_btn.state(["disabled"])
        else:
            self.assignment_btn.state(["!disabled"])

    def _render_school_year(self, profile_id: int) -> None:
        status = school_year.school_year_status(profile_id)
        if status is None:
            self.school_year_var.set("School year: parent has not chosen a Texas grade target yet.")
            return
        stretch = "stretch on" if status.target.stretch_enabled else "stretch paused"
        if status.next_goal is None:
            next_text = "all quiz-ready goals complete"
        else:
            refs = ", ".join(status.next_goal.standard_refs)
            next_text = f"next: {status.next_goal.label} ({refs})"
        gap_text = f" • {len(status.content_gaps)} content gap(s)" if status.content_gaps else ""
        self.school_year_var.set(
            f"School year: Texas Grade {status.target.grade} • "
            f"{status.completed_count}/{status.total_count} goals complete • {next_text} • {stretch}{gap_text}"
        )


def _streak_graph(current: int, target: int) -> str:
    blocks = min(max(current, 0), target)
    return ("🔥" * blocks) + ("⬜" * (target - blocks))


def _school_goal_steps_text(steps: tuple[school_year.SchoolYearGoalStep, ...]) -> str:
    if not steps:
        return ""
    done = [step.subskill for step in steps if step.mastered]
    waiting = [step for step in steps if not step.mastered]
    prefix = f"Goal steps: {len(done)}/{len(steps)} done."
    if not waiting:
        return f"{prefix} Every step is complete."
    next_step = waiting[0]
    if next_step.current_streak > 0:
        streak = min(next_step.current_streak, next_step.target_streak)
        progress = f"{streak}/{next_step.target_streak} practice streak"
    else:
        progress = "not started yet"
    done_text = f" Done: {', '.join(done)}." if done else ""
    return f"{prefix} Next step: {next_step.subskill} ({progress}).{done_text}"


def _subskill_coverage_by_skill(profile_id: int) -> dict[str, float]:
    progress = db.list_subskill_progress(profile_id)
    by_skill: dict[str, dict[str, int]] = {}
    for item in progress:
        if item.skill not in by_skill:
            by_skill[item.skill] = {"mastered": 0, "total": 0}
        by_skill[item.skill]["total"] += 1
        if item.mastered:
            by_skill[item.skill]["mastered"] += 1
    coverage: dict[str, float] = {}
    for skill, counts in by_skill.items():
        total = max(1, counts["total"])
        coverage[skill] = float(counts["mastered"]) / float(total)
    return coverage
