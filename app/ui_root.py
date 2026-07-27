from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, simpledialog, ttk

from . import db, summer_program
from .theme import FONTS, apply_theme
from .time_utils import now_iso
from .summer_mode import preferred_track_for_skill
from .summer_program_quiz import SummerProgramLaunch
from .ui_arithmetic import ArithmeticPanel
from .ui_dashboard import DashboardPanel
from .ui_fractals import FractalPanel
from .ui_parent import ParentPanel
from .ui_quiz import QuizPanel
from .ui_settings import load_ui_settings
from .ui_skill_map import SkillMapPanel
from .skill_graph import skills_in_track, track_names


class AppShell:
    def __init__(self, root: tk.Tk, profile) -> None:
        self.root = root
        self.profile = profile
        self._settings = load_ui_settings()
        self._summer_mode = self._settings.summer_mode
        self._parent_unlocked = False
        self._last_tab_index = 0
        self._handling_tab_change = False
        self._parent_tab_index: int | None = None
        self._bonus_explore_unlocked = False

        self.root.title("MandelQuest")
        self.root.geometry("1200x720")
        self.root.minsize(960, 580)
        apply_theme(self.root)

        self._build_header()
        self._build_layout()
        self._bind_global_shortcuts()

    def _build_header(self) -> None:
        bar = ttk.Frame(self.root)
        bar.pack(fill=tk.X)
        self.profile_var = tk.StringVar(value=f"Profile: {self.profile.name}")
        ttk.Label(bar, textvariable=self.profile_var, font=FONTS["subheading"]).pack(side=tk.LEFT, padx=10, pady=6)
        self.offline_var = tk.StringVar(value="")
        ttk.Label(bar, textvariable=self.offline_var, foreground="#5b6f84").pack(side=tk.RIGHT, padx=10, pady=6)
        self._refresh_offline_status()

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
        self.parent = ParentPanel(
            self.notebook,
            self.view_stack,
            self.get_profile,
            self.launch_quiz_set,
            self._refresh_offline_status,
            self.launch_summer_program_task,
        )
        self.dashboard = DashboardPanel(
            self.notebook,
            self.view_stack,
            self.get_profile,
            self.launch_daily_review,
            self.launch_assignment_quiz,
            self.launch_summer_program_task,
            self.launch_bonus_explore,
        )
        self.skill_map = SkillMapPanel(
            self.notebook,
            self.view_stack,
            self.get_profile,
            self.launch_skill_map_quiz,
        )

        if self._summer_mode and self.profile.role == "child":
            self._modules = [
                ("Today", self.dashboard),
                ("Practice", self.arithmetic),
                ("Quizzes", self.quiz),
            ]
        elif self._summer_mode:
            self._modules = [
                ("Today", self.dashboard),
                ("Practice", self.arithmetic),
                ("Quizzes", self.quiz),
                ("Parent", self.parent),
                ("Bonus Explore", self.fractal),
            ]
        elif self.profile.role == "child":
            self._modules = [
                ("Today", self.dashboard),
                ("Practice", self.arithmetic),
                ("Quizzes", self.quiz),
                ("Skill Map", self.skill_map),
            ]
        else:
            self._modules = [
                ("Today", self.dashboard),
                ("Practice", self.arithmetic),
                ("Quizzes", self.quiz),
                ("Skill Map", self.skill_map),
                ("Parent", self.parent),
                ("Bonus Explore", self.fractal),
            ]

        for name, module in self._modules:
            self.notebook.add(module.controls_frame, text=name)
            module.view_frame.grid(row=0, column=0, sticky="nsew")
            if name == "Parent":
                self._parent_tab_index = self.notebook.index("end") - 1

        self.notebook.bind("<<NotebookTabChanged>>", self._on_tab_changed)
        self._show_module(0)

    def _bind_global_shortcuts(self) -> None:
        self.root.bind_all("<Control-Key-1>", lambda _e: self._select_tab(0))
        self.root.bind_all("<Control-Key-2>", lambda _e: self._select_tab(1))
        self.root.bind_all("<Control-Key-3>", lambda _e: self._select_tab(2))
        self.root.bind_all("<Control-Key-4>", lambda _e: self._select_tab(3))
        self.root.bind_all("<Control-Key-5>", lambda _e: self._select_tab(4))
        self.root.bind_all("<Control-Key-6>", lambda _e: self._select_tab(5))
        self.root.bind_all("<Control-Tab>", self._next_tab)
        self.root.bind_all("<Control-ISO_Left_Tab>", self._prev_tab)
        self.root.bind_all("<Control-Shift-Tab>", self._prev_tab)
        self.root.bind_all("<Control-r>", lambda _e: self._refresh_active_module())
        self.root.bind_all("<F5>", lambda _e: self._refresh_active_module())
        self.root.bind_all("<Control-l>", lambda _e: self._focus_active_controls())
        self.root.bind_all("<Control-n>", self._shortcut_parent_create)
        self.root.bind_all("<Control-Return>", self._shortcut_quiz_ctrl_enter)
        self.root.bind_all("<Alt-s>", self._shortcut_quiz_start)
        self.root.bind_all("<Alt-n>", self._shortcut_quiz_submit_next)
        self.root.bind_all("<Alt-i>", self._shortcut_quiz_intuition)
        self.root.bind_all("<Alt-e>", self._shortcut_quiz_example)
        self.root.bind_all("<Alt-d>", self._shortcut_dashboard_daily)
        self.root.bind_all("<Alt-a>", self._shortcut_dashboard_assignment)
        self.root.bind_all("<Alt-Key-1>", lambda _e: self._shortcut_parent_tab(0))
        self.root.bind_all("<Alt-Key-2>", lambda _e: self._shortcut_parent_tab(1))
        self.root.bind_all("<Alt-Key-3>", lambda _e: self._shortcut_parent_tab(2))
        self.root.bind_all("<Alt-Key-4>", lambda _e: self._shortcut_parent_tab(3))
        self.root.bind_all("<Alt-Key-5>", lambda _e: self._shortcut_parent_tab(4))
        self.root.bind_all("<Alt-Key-6>", lambda _e: self._shortcut_parent_tab(5))
        self.root.bind_all("<Alt-Key-7>", lambda _e: self._shortcut_parent_tab(6))
        self.root.bind_all("<Alt-Key-8>", lambda _e: self._shortcut_parent_tab(7))

    def _select_tab(self, idx: int) -> None:
        if idx < 0 or idx >= len(self._modules):
            return
        self.notebook.select(idx)

    def _next_tab(self, _event=None) -> str:
        idx = self.notebook.index(self.notebook.select())
        self._select_tab((idx + 1) % len(self._modules))
        return "break"

    def _prev_tab(self, _event=None) -> str:
        idx = self.notebook.index(self.notebook.select())
        self._select_tab((idx - 1) % len(self._modules))
        return "break"

    def _refresh_active_module(self) -> None:
        idx = self.notebook.index(self.notebook.select())
        module = self._modules[idx][1]
        if hasattr(module, "_refresh_active_tab_shortcut"):
            try:
                module._refresh_active_tab_shortcut()
                return
            except Exception:
                pass
        self._show_module(idx)

    def _focus_active_controls(self) -> None:
        idx = self.notebook.index(self.notebook.select())
        module = self._modules[idx][1]
        if hasattr(module, "focus_primary_control"):
            try:
                module.focus_primary_control()
            except Exception:
                return

    def _active_module(self):
        idx = self.notebook.index(self.notebook.select())
        return self._modules[idx][1]

    def _shortcut_parent_create(self, _event=None) -> str:
        module = self._active_module()
        if module is self.parent:
            module._create_active_item_shortcut()
            return "break"
        return ""

    def _shortcut_quiz_ctrl_enter(self, _event=None) -> str:
        module = self._active_module()
        if module is self.quiz:
            module._submit_or_next_shortcut()
            return "break"
        return ""

    def _shortcut_quiz_start(self, _event=None) -> str:
        module = self._active_module()
        if module is self.quiz:
            module._start_quiz_shortcut()
            return "break"
        return ""

    def _shortcut_quiz_submit_next(self, _event=None) -> str:
        module = self._active_module()
        if module is self.quiz:
            module._submit_or_next_shortcut()
            return "break"
        return ""

    def _shortcut_quiz_intuition(self, _event=None) -> str:
        module = self._active_module()
        if module is self.quiz:
            module._show_intuition_shortcut()
            return "break"
        return ""

    def _shortcut_quiz_example(self, _event=None) -> str:
        module = self._active_module()
        if module is self.quiz:
            module._depth_controller.show_example(module)
            return "break"
        return ""

    def _shortcut_dashboard_daily(self, _event=None) -> str:
        module = self._active_module()
        if module is self.dashboard:
            module._daily_shortcut()
            return "break"
        return ""

    def _shortcut_dashboard_assignment(self, _event=None) -> str:
        module = self._active_module()
        if module is self.dashboard:
            module._assignment_shortcut()
            return "break"
        return ""

    def _shortcut_parent_tab(self, idx: int) -> str:
        module = self._active_module()
        if module is self.parent:
            module._select_parent_tab(idx)
            return "break"
        return ""

    def _on_tab_changed(self, _event) -> None:
        if self._handling_tab_change:
            return
        idx = self.notebook.index(self.notebook.select())
        if self._parent_tab_index is not None and idx == self._parent_tab_index and not self._ensure_parent_access():
            self._handling_tab_change = True
            self.notebook.select(self._last_tab_index)
            self._handling_tab_change = False
            return
        self._last_tab_index = idx
        self._show_module(idx)

    def _show_module(self, idx: int) -> None:
        module = self._modules[idx][1]
        module.view_frame.tkraise()
        if hasattr(module, "on_module_activated"):
            try:
                module.on_module_activated()
            except Exception:
                pass
        if hasattr(module, "render"):
            module.render()

    def get_profile(self):
        return self.profile

    def _refresh_offline_status(self) -> None:
        settings = load_ui_settings()
        self._settings = settings
        self._summer_mode = settings.summer_mode
        if settings.enforce_offline_mode:
            self.offline_var.set("Offline mode: enforced")
        else:
            self.offline_var.set("Offline mode: optional links")

    def _preset_track_for_skill(self, skill: str) -> str:
        return preferred_track_for_skill(
            skill,
            track_names(),
            skills_in_track,
            grade_band=self._settings.default_grade_band,
            summer_mode=self._summer_mode,
        )

    def _ensure_parent_access(self) -> bool:
        if self._parent_unlocked:
            return True
        configured = db.parent_pin_configured()
        if not configured:
            if self.profile.role == "parent":
                messagebox.showinfo(
                    "Set parent PIN",
                    "No parent PIN is set yet. You can set one in Parent -> Profiles.",
                )
                self._parent_unlocked = True
                return True
            messagebox.showerror(
                "Parent access locked",
                "A parent must sign in with a parent profile and set a parent PIN first.",
            )
            return False

        locked, locked_until = db.parent_pin_locked(now_iso())
        if locked:
            messagebox.showerror(
                "Parent access locked",
                f"Too many failed attempts. Try again after {locked_until}.",
            )
            return False

        pin = simpledialog.askstring("Parent PIN", "Enter parent PIN:", show="*", parent=self.root)
        if pin is None:
            return False
        if db.verify_parent_pin(pin, now_iso()):
            db.clear_parent_lock(now_iso())
            self._parent_unlocked = True
            return True

        locked_until = db.record_parent_auth_failure(now_iso())
        if locked_until:
            messagebox.showerror(
                "Parent access locked",
                f"PIN failed too many times. Locked until {locked_until}.",
            )
        else:
            messagebox.showerror("Incorrect PIN", "Parent PIN was incorrect.")
        return False

    def launch_daily_review(self, skill: str, subskill: str | None, level: int = 1) -> None:
        self.notebook.select(self.quiz.controls_frame)
        self.quiz.apply_preset(
            track=self._preset_track_for_skill(skill),
            skill=skill,
            subskill=subskill,
            num_questions=5,
            level=level,
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
            track=self._preset_track_for_skill(skill),
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

    def launch_summer_program_task(self, task_id: int, profile_override=None) -> None:
        task = db.get_summer_program_task(task_id)
        if task is None:
            messagebox.showerror("Summer Program", "That program task no longer exists.")
            return
        program = db.get_summer_program(task.program_id)
        if program is None:
            messagebox.showerror("Summer Program", "The selected program could not be loaded.")
            return
        target_profile = profile_override or self.profile
        summary = summer_program.summer_program_status_summary(target_profile.id, program.id)
        if summary is None:
            messagebox.showerror("Summer Program", "The selected program could not be loaded.")
            return
        if summary.current_blocker == "awaiting_parent_review":
            messagebox.showinfo("Summer Program", "Parent review is required before the next task can launch.")
            return
        launch_task = summer_program.launchable_summer_program_task(program.id)
        if launch_task is None or launch_task.id != task.id:
            messagebox.showinfo("Summer Program", "That task is no longer the current launchable Summer Program step.")
            return
        self.notebook.select(self.quiz.controls_frame)
        self.quiz.apply_preset(
            track=self._preset_track_for_skill(task.skill),
            skill=task.skill,
            subskill=task.subskill or "Any",
            num_questions=5,
            level=1 if program.lane == "foundation_bridge" else 2,
            question_type="typed",
            strategy="focused",
            launch_context="summer_program",
            profile_override=target_profile,
            summer_program_launch=SummerProgramLaunch(
                profile_id=target_profile.id,
                program_id=program.id,
                task_id=task.id,
            ),
        )
        self.quiz.start_quiz()

    def launch_bonus_explore(self) -> None:
        if self.profile.role == "child":
            today_count, _streak = db.daily_goal_status(self.profile.id)
            if today_count <= 0:
                messagebox.showinfo("Bonus Explore", "Finish today's math practice first.")
                return
            if not self._bonus_explore_unlocked:
                self._modules.append(("Bonus Explore", self.fractal))
                self.notebook.add(self.fractal.controls_frame, text="Bonus Explore")
                self.fractal.view_frame.grid(row=0, column=0, sticky="nsew")
                self._bonus_explore_unlocked = True
            self.notebook.select(self.fractal.controls_frame)
            return
        for idx, (_name, module) in enumerate(self._modules):
            if module is self.fractal:
                self.notebook.select(idx)
                return

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
            track=self._preset_track_for_skill(skill),
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
            track=self._preset_track_for_skill(skill),
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
        if hasattr(self.arithmetic, "shutdown"):
            self.arithmetic.shutdown()
        if hasattr(self.quiz, "shutdown"):
            self.quiz.shutdown()
