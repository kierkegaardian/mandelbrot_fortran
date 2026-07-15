from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from .models import Profile
from .theme import FONTS, apply_theme
from .ui_arithmetic import ArithmeticPanel
from .ui_dashboard import DashboardPanel
from .ui_fractals import FractalPanel
from .ui_parent import ParentPanel
from .ui_parent_access import ParentAccessMixin
from .ui_quiz import QuizPanel
from .ui_settings import UiSettings, load_ui_settings
from .ui_shell_launchers import ShellQuizLaunchersMixin
from .ui_shell_shortcuts import ShellShortcutsMixin
from .ui_skill_map import SkillMapPanel


class AppShell(ParentAccessMixin, ShellShortcutsMixin, ShellQuizLaunchersMixin):
    """Role-aware application shell with stable panel constructors."""

    def __init__(self, root: tk.Tk, profile: Profile) -> None:
        self.root = root
        self.profile = profile
        self._settings: UiSettings = load_ui_settings()
        self._parent_unlocked = False
        self._last_tab_index = 0
        self._handling_tab_change = False
        self._parent_tab_index: int | None = None

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
        ttk.Label(
            bar,
            textvariable=self.profile_var,
            font=FONTS["subheading"],
        ).pack(side=tk.LEFT, padx=10, pady=6)
        self.offline_var = tk.StringVar()
        ttk.Label(
            bar,
            textvariable=self.offline_var,
            foreground="#5b6f84",
        ).pack(side=tk.RIGHT, padx=10, pady=6)
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
        )
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

        common = [
            ("Today", self.dashboard),
            ("Practice", self.arithmetic),
            ("Quizzes", self.quiz),
            ("Skill Map", self.skill_map),
        ]
        if self.profile.role == "parent":
            self._modules = common + [
                ("Parent", self.parent),
                ("Bonus Explore", self.fractal),
            ]
        else:
            self._modules = common

        for name, module in self._modules:
            self.notebook.add(module.controls_frame, text=name)
            module.view_frame.grid(row=0, column=0, sticky="nsew")
            if name == "Parent":
                self._parent_tab_index = self.notebook.index("end") - 1
        self.notebook.bind("<<NotebookTabChanged>>", self._on_tab_changed)
        self._show_module(0)

    def _on_tab_changed(self, _event: tk.Event) -> None:  # type: ignore[type-arg]
        if self._handling_tab_change:
            return
        index = self.notebook.index(self.notebook.select())
        if (
            self._parent_tab_index is not None
            and index == self._parent_tab_index
            and not self._ensure_parent_access()
        ):
            self._handling_tab_change = True
            self.notebook.select(self._last_tab_index)
            self._handling_tab_change = False
            return
        self._last_tab_index = index
        self._show_module(index)

    def _show_module(self, index: int) -> None:
        self._refresh_offline_status()
        module = self._modules[index][1]
        module.view_frame.tkraise()
        activated = getattr(module, "on_module_activated", None)
        if callable(activated):
            activated()
        render = getattr(module, "render", None)
        if callable(render):
            render()

    def get_profile(self) -> Profile:
        return self.profile

    def _refresh_offline_status(self) -> None:
        self._settings = load_ui_settings()
        if self._settings.enforce_offline_mode:
            self.offline_var.set("Offline mode: enforced")
        else:
            self.offline_var.set("Offline mode: optional links")

    def shutdown(self) -> None:
        for module in (
            self.fractal,
            self.arithmetic,
            self.quiz,
            self.parent,
            self.dashboard,
            self.skill_map,
        ):
            shutdown = getattr(module, "shutdown", None)
            if callable(shutdown):
                shutdown()
