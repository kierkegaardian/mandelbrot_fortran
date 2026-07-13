from __future__ import annotations

import json
import tkinter as tk
from tkinter import messagebox, ttk
import webbrowser
import random
import time
from pathlib import Path

from . import db
from . import quiz_flow
from . import quiz_history
from . import quiz_strategies
from .explanations import ARITHMETIC_MODE_EXPLANATIONS, QUIZ_EXPLANATION, explanation_for
from .learning_engine import (
    ModeMix,
    apply_word_gap_boost,
    build_skill_stats,
    default_mode_mix_for_stage,
    normalize_mode_mix,
)
from .models import ScaffoldStep
from .quiz_answers import is_correct_answer
from .quiz_engine import QUESTION_TYPES, Question, generate_question
from .quiz_recovery import (
    MistakeRecoveryState,
    build_mistake_recovery_text,
    should_offer_mistake_recovery,
)
from .story_wrapper import apply_story_wrapper, can_wrap_skill
from .summer_program_quiz import ProgramQuizPlan, SummerProgramLaunch, build_task_quiz_plan
from .curriculum import curriculum_pdf_path, get_curriculum_for_skill
from .quiz_content import ContentUnavailableError, is_native_intuition_skill, is_template_only_skill
from .skill_graph import (
    SKILLS,
    SKILL_LABELS,
    SKILL_ORDER,
    SKILL_PREREQUISITE_WEIGHTS,
    skills_in_track,
    subskills_for,
    track_names,
)
from .summer_mode import filter_skills, filter_tracks
from .theme import COLORS
from .time_utils import now_iso
from .ui_explain import ExplanationPanel
from .ui_settings import load_ui_settings
from .ui_widgets import int_spinbox


class QuizPanel:
    def __init__(self, controls_parent: tk.Widget, view_parent: tk.Widget, profile_getter) -> None:
        self.controls_frame = ttk.Frame(controls_parent)
        self.view_frame = ttk.Frame(view_parent)
        self._profile_getter = profile_getter

        self.skill_var = tk.StringVar(value="counting")
        self.track_var = tk.StringVar(value="All")
        self.subskill_var = tk.StringVar(value="Any")
        self.type_var = tk.StringVar(value="both")
        self.strategy_var = tk.StringVar(value="focused")
        self.num_var = tk.IntVar(value=5)
        self.level_var = tk.IntVar(value=1)
        self.vary_numbers_var = tk.BooleanVar(value=True)
        self.historical_test_var = tk.StringVar(value="")
        self.historical_exam_filter_var = tk.StringVar(value="all")
        self.historical_category_var = tk.StringVar(value="all")
        self._historical_tests: dict[str, Path] = {}
        self._history_group_visible = True
        self._settings_group_visible = True

        self._questions: list[Question] = []
        self._index = 0
        self._score = 0
        self._answers: list[tuple[Question, str, bool]] = []
        self._mode_mix_override: tuple[int, int, int] | None = None
        self._launch_context = "manual"
        self._quiz_started_monotonic: float | None = None
        self._attempt_skill: str | None = None
        self._record_attempt: bool = True
        self._record_progress: bool = True
        self._correct_streak = 0
        self._progress_attempt_id: int | None = None
        self._animation_after_id: str | None = None
        self._profile_override = None
        self._summer_program_launch: SummerProgramLaunch | None = None
        self._scaffold_question_index: int | None = None
        self._scaffold_step_index = 0
        self._scaffold_step_answers: list[str] = []

        self._build_controls()
        self._build_view()

    def _build_controls(self) -> None:
        frame = ttk.Frame(self.controls_frame, padding=10)
        frame.pack(fill=tk.BOTH, expand=True)

        skill_group = ttk.LabelFrame(frame, text="Skill Selection", padding=8)
        skill_group.pack(fill=tk.X, pady=(0, 8))
        ttk.Label(skill_group, text="Skill").pack(anchor=tk.W)
        track_combo = ttk.Combobox(
            skill_group,
            textvariable=self.track_var,
            values=["All", *track_names()],
            state="readonly",
            width=20,
        )
        track_combo.pack(fill=tk.X, pady=(0, 8))
        track_combo.bind("<<ComboboxSelected>>", lambda _e: self._on_track_change())
        self.track_combo = track_combo

        self.skill_combo = ttk.Combobox(
            skill_group,
            textvariable=self.skill_var,
            values=self._quiz_skill_values_for_track("All"),
            state="readonly",
            width=20,
        )
        self.skill_combo.pack(fill=tk.X, pady=(0, 8))
        self.skill_combo.bind("<<ComboboxSelected>>", lambda _e: self._on_skill_change())

        ttk.Label(skill_group, text="Subskill (optional)").pack(anchor=tk.W)
        self.subskill_combo = ttk.Combobox(
            skill_group,
            textvariable=self.subskill_var,
            values=["Any"],
            state="readonly",
            width=24,
        )
        self.subskill_combo.pack(fill=tk.X, pady=(0, 8))
        self.subskill_combo.bind("<<ComboboxSelected>>", lambda _e: self._on_skill_change())
        ttk.Label(skill_group, text="Curriculum source:").pack(anchor=tk.W)
        self.curriculum_label = ttk.Label(skill_group, text="No source mapped", foreground=COLORS["text_secondary"])
        self.curriculum_label.pack(anchor=tk.W, pady=(0, 4))
        ttk.Button(skill_group, text="Open Source PDF", command=self._open_curriculum_pdf).pack(anchor=tk.W)
        ttk.Label(skill_group, text="(Choose a skill to refresh)").pack(anchor=tk.W, padx=2, pady=(0, 2))

        history_group = ttk.LabelFrame(frame, text="Historical Tests", padding=8)
        history_group.pack(fill=tk.X, pady=(0, 8))
        self.history_group = history_group
        ttk.Label(history_group, text="Historical full tests (offline PDFs)").pack(anchor=tk.W)
        self.historical_combo = ttk.Combobox(
            history_group,
            textvariable=self.historical_test_var,
            values=[],
            state="readonly",
            width=24,
        )
        self.historical_combo.pack(fill=tk.X, pady=(4, 4))
        test_btns = ttk.Frame(history_group)
        test_btns.pack(fill=tk.X, pady=(0, 8))
        ttk.Button(test_btns, text="Open Full Test", command=self._open_historical_test).pack(side=tk.LEFT)
        ttk.Button(test_btns, text="Print Test Mode", command=self._print_historical_test).pack(side=tk.LEFT, padx=(6, 0))
        ttk.Button(test_btns, text="Ingest PDFs", command=self._ingest_historical_pdfs).pack(side=tk.LEFT, padx=(6, 0))
        ttk.Button(test_btns, text="Ingest Answer Keys", command=self._ingest_historical_answer_keys).pack(
            side=tk.LEFT, padx=(6, 0)
        )
        ttk.Button(test_btns, text="Refresh", command=self._refresh_historical_tests).pack(side=tk.LEFT, padx=(6, 0))

        filters = ttk.Frame(history_group)
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

        settings_group = ttk.LabelFrame(frame, text="Quiz Settings", padding=8)
        settings_group.pack(fill=tk.X, pady=(0, 8))
        self.settings_group = settings_group
        ttk.Label(settings_group, text="Question Type").pack(anchor=tk.W)
        ttk.Combobox(settings_group, textvariable=self.type_var, values=QUESTION_TYPES, state="readonly").pack(
            fill=tk.X, pady=(0, 8)
        )

        ttk.Label(settings_group, text="Strategy").pack(anchor=tk.W)
        strategy_combo = ttk.Combobox(
            settings_group,
            textvariable=self.strategy_var,
            values=["focused", "learning_blend", "free_mode", "sat_psat_unit", "historical_practice"],
            state="readonly",
        )
        strategy_combo.pack(fill=tk.X, pady=(0, 8))
        self.strategy_combo = strategy_combo

        ttk.Label(settings_group, text="Number of Questions").pack(anchor=tk.W)
        int_spinbox(settings_group, self.num_var, 3, 20).pack(anchor=tk.W, pady=(0, 8))

        ttk.Label(settings_group, text="Level").pack(anchor=tk.W)
        int_spinbox(settings_group, self.level_var, 1, 3).pack(anchor=tk.W, pady=(0, 8))
        ttk.Checkbutton(
            settings_group,
            text="Vary numbers / avoid repeats in this session",
            variable=self.vary_numbers_var,
        ).pack(anchor=tk.W, pady=(0, 8))

        self.launch_note_var = tk.StringVar(value="")
        self.launch_note_label = ttk.Label(
            frame,
            textvariable=self.launch_note_var,
            foreground=COLORS["text_secondary"],
            wraplength=260,
        )
        self.launch_note_label.pack(fill=tk.X, pady=(0, 6))
        self.start_quiz_btn = ttk.Button(frame, text="Start Quiz", command=self.start_quiz, style="Accent.TButton")
        self.start_quiz_btn.pack(fill=tk.X, pady=(6, 12))

        self.explain = ExplanationPanel(frame)
        self.explain.set_explanation(QUIZ_EXPLANATION)
        self.explain.frame.pack(fill=tk.X, pady=(12, 0))
        self._update_curriculum_label()
        self._refresh_subskills()
        self._refresh_historical_tests()
        self._apply_track_filter()

    def _build_view(self) -> None:
        # UX6: Quiz progress bar
        progress_row = ttk.Frame(self.view_frame)
        progress_row.pack(fill=tk.X, padx=16, pady=(8, 0))
        self.quiz_progress_var = tk.DoubleVar(value=0)
        self.quiz_progress_bar = ttk.Progressbar(
            progress_row, variable=self.quiz_progress_var, maximum=100,
            style="Accent.Horizontal.TProgressbar",
        )
        self.quiz_progress_bar.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8))
        self.quiz_progress_label = tk.StringVar(value="")
        ttk.Label(progress_row, textvariable=self.quiz_progress_label, foreground=COLORS["text_secondary"]).pack(
            side=tk.LEFT,
        )
        self.quiz_score_label = tk.StringVar(value="")
        ttk.Label(progress_row, textvariable=self.quiz_score_label, foreground=COLORS["accent"]).pack(
            side=tk.LEFT, padx=(8, 0),
        )

        self.prompt_var = tk.StringVar(value="Choose settings on the left to start a quiz.")
        ttk.Label(self.view_frame, textvariable=self.prompt_var, font=("Segoe UI", 14, "bold")).pack(pady=12)
        self.meta_var = tk.StringVar(value="")
        ttk.Label(self.view_frame, textvariable=self.meta_var, foreground=COLORS["accent_strong"]).pack(pady=(0, 4))

        self.visual_canvas = tk.Canvas(self.view_frame, bg=COLORS["canvas_bg"], height=260)
        self.visual_canvas.pack(fill=tk.X, padx=16)

        self.answer_frame = tk.Frame(
            self.view_frame,
            bg=COLORS["panel_bg"],
            highlightthickness=0,
            bd=0,
        )
        self.answer_frame.pack(fill=tk.X, padx=16, pady=10)

        self.answer_var = tk.StringVar(value="")
        self.choice_var = tk.StringVar(value="")
        self.repeat_var = tk.BooleanVar(value=False)
        self.recovery_var = tk.StringVar(value="")
        self._mistake_recovery: MistakeRecoveryState | None = None

        self.feedback_var = tk.StringVar(value="")
        ttk.Label(self.view_frame, textvariable=self.feedback_var, foreground=COLORS["success"],
                  font=("Segoe UI", 12, "bold")).pack(pady=(6, 4))
        self.streak_var = tk.StringVar(value="")
        ttk.Label(self.view_frame, textvariable=self.streak_var, foreground=COLORS["accent"],
                  font=("Segoe UI", 10, "bold")).pack(pady=(0, 4))
        self.intuition_var = tk.StringVar(value="")
        ttk.Label(self.view_frame, textvariable=self.intuition_var, foreground=COLORS["accent_strong"], wraplength=780).pack(pady=(0, 4))
        ttk.Label(
            self.view_frame,
            textvariable=self.recovery_var,
            foreground=COLORS["text_secondary"],
            wraplength=780,
            justify=tk.LEFT,
        ).pack(pady=(0, 4))

        btns = ttk.Frame(self.view_frame)
        btns.pack(pady=6)
        self.submit_btn = ttk.Button(btns, text="Submit", command=self.submit_answer)
        self.stuck_btn = ttk.Button(btns, text="Show intuition (I'm stuck)", command=self._show_intuition)
        self.next_btn = ttk.Button(btns, text="Next", command=self.next_question)
        self.submit_btn.pack(side=tk.LEFT, padx=4)
        self.stuck_btn.pack(side=tk.LEFT, padx=4)
        self.next_btn.pack(side=tk.LEFT, padx=4)
        self.next_btn.state(["disabled"])
        self.stuck_btn.state(["disabled"])

        self.summary_frame = ttk.Frame(self.view_frame)
        self.summary_frame.pack(fill=tk.BOTH, expand=True, padx=16, pady=8)

    def _start_quiz_shortcut(self) -> str:
        self.start_quiz()
        return "break"

    def _submit_or_next_shortcut(self) -> str:
        if not self._questions:
            self.start_quiz()
            return "break"
        if self.next_btn.instate(["!disabled"]):
            self.next_question()
        elif self.submit_btn.instate(["!disabled"]):
            self.submit_answer()
        return "break"

    def _show_intuition_shortcut(self) -> str:
        if self.stuck_btn.instate(["!disabled"]):
            self._show_intuition()
        return "break"

    def focus_primary_control(self) -> None:
        if self._is_child_profile():
            self.skill_combo.focus_set()
            return
        self.track_combo.focus_set()

    def on_module_activated(self) -> None:
        self._apply_track_filter()
        self.focus_primary_control()

    def _active_profile(self):
        return self._profile_override or self._profile_getter()

    def _ensure_scaffold_state(self, question_index: int) -> None:
        if self._scaffold_question_index == question_index:
            return
        self._scaffold_question_index = question_index
        self._scaffold_step_index = 0
        self._scaffold_step_answers = []

    def _clear_scaffold_state(self) -> None:
        self._scaffold_question_index = None
        self._scaffold_step_index = 0
        self._scaffold_step_answers = []

    def _current_scaffold_step(self, question: Question):
        if not question.scaffold_steps:
            return None
        self._ensure_scaffold_state(self._index)
        if self._scaffold_step_index >= len(question.scaffold_steps):
            return None
        return question.scaffold_steps[self._scaffold_step_index]

    def _update_curriculum_label(self) -> None:
        skill = self.skill_var.get()
        entry = get_curriculum_for_skill(skill)
        if entry is None:
            self.curriculum_label.config(text="No source mapped for this skill.")
            return
        topics = ", ".join(entry.topics)
        self.curriculum_label.config(text=f"{entry.label}: {topics} ({entry.source})")

    def _open_curriculum_pdf(self) -> None:
        path = curriculum_pdf_path(self.skill_var.get())
        if path is None:
            messagebox.showerror("No curriculum file", "No local PDF found for this skill.")
            return
        webbrowser.open(f"file://{path}")

    def _refresh_historical_tests(self) -> None:
        quiz_history.refresh_historical_tests(self)

    def _open_historical_test(self) -> None:
        quiz_history.open_historical_test(self)

    def _ingest_historical_pdfs(self) -> None:
        quiz_history.ingest_historical_pdfs(self)

    def _ingest_historical_answer_keys(self) -> None:
        quiz_history.ingest_historical_answer_keys(self)

    def _print_historical_test(self) -> None:
        quiz_history.print_historical_test(self)

    def _template_only_quiz_skills(self) -> list[str]:
        skills = {
            str(item.skill)
            for item in db.list_all_question_templates(active_only=True)
            if item.skill and item.skill not in SKILLS and item.skill != "mixed"
        }
        return sorted(skills)

    def _quiz_skill_values_for_track(self, track: str) -> list[str]:
        settings = load_ui_settings()
        if track == "All":
            skills = list(SKILLS)
            if not settings.summer_mode:
                skills.extend(self._template_only_quiz_skills())
            merged = list(
                dict.fromkeys(
                    filter_skills(skills, grade_band=settings.default_grade_band, summer_mode=settings.summer_mode)
                )
            )
            merged.append("mixed")
            return merged
        skills = list(
            filter_skills(
                skills_in_track(track),
                grade_band=settings.default_grade_band,
                summer_mode=settings.summer_mode,
            )
        )
        return skills

    def _apply_track_filter(self) -> None:
        settings = load_ui_settings()
        visible_tracks = list(
            filter_tracks(track_names(), skills_in_track, grade_band=settings.default_grade_band, summer_mode=settings.summer_mode)
        )
        track_values = visible_tracks if settings.summer_mode else ["All", *visible_tracks]
        if not track_values:
            track_values = ["All"]
        if self.track_var.get() not in track_values:
            self.track_var.set(track_values[0])
        self.track_combo.config(values=track_values)
        track = self.track_var.get()
        values = self._quiz_skill_values_for_track(track)
        if not values:
            values = ["counting"]
        if self.skill_var.get() not in values and "mixed" in values:
            self.skill_var.set("mixed")
        elif self.skill_var.get() not in values:
            self.skill_var.set(values[0] if values else "counting")
        self.skill_combo.config(values=values if values else ["counting"])
        self._refresh_subskills()
        self._apply_experience_mode(settings.summer_mode)

    def _is_child_profile(self) -> bool:
        profile = self._profile_getter()
        return bool(profile is not None and getattr(profile, "role", "") == "child")

    def _set_history_group_visible(self, visible: bool) -> None:
        if visible and not self._history_group_visible:
            self.history_group.pack(fill=tk.X, pady=(0, 8), before=self.settings_group)
            self._history_group_visible = True
        elif not visible and self._history_group_visible:
            self.history_group.pack_forget()
            self._history_group_visible = False

    def _set_settings_group_visible(self, visible: bool) -> None:
        if visible and not self._settings_group_visible:
            self.settings_group.pack(fill=tk.X, pady=(0, 8), before=self.launch_note_label)
            self._settings_group_visible = True
        elif not visible and self._settings_group_visible:
            self.settings_group.pack_forget()
            self._settings_group_visible = False

    def _apply_experience_mode(self, summer_mode: bool) -> None:
        child_profile = self._is_child_profile()
        if child_profile:
            self._set_history_group_visible(False)
            self._set_settings_group_visible(False)
            strategy_values = ["focused", "learning_blend"]
            if self._launch_context == "manual":
                self.strategy_var.set("learning_blend")
            elif self.strategy_var.get() not in strategy_values:
                self.strategy_var.set("learning_blend")
            self.type_var.set("both")
            if self.num_var.get() < 3 or self.num_var.get() > 10:
                self.num_var.set(5)
            self.start_quiz_btn.config(text="Start Practice")
            self.launch_note_var.set("Pick a skill, then start a short practice. Tests stay in Parent tools.")
        elif summer_mode:
            self._set_history_group_visible(False)
            self._set_settings_group_visible(True)
            strategy_values = ["focused", "learning_blend"]
            if self.strategy_var.get() not in strategy_values:
                self.strategy_var.set("learning_blend")
            self.start_quiz_btn.config(text="Start Quiz")
            self.launch_note_var.set("")
        else:
            self._set_history_group_visible(True)
            self._set_settings_group_visible(True)
            strategy_values = ["focused", "learning_blend", "free_mode", "sat_psat_unit", "historical_practice"]
            if self.strategy_var.get() not in strategy_values:
                self.strategy_var.set("focused")
            self.start_quiz_btn.config(text="Start Quiz")
            self.launch_note_var.set("")
        self.strategy_combo.config(values=strategy_values)

    def _on_track_change(self) -> None:
        self._apply_track_filter()
        self._on_skill_change()

    def _on_skill_change(self) -> None:
        self._update_curriculum_label()
        self._refresh_subskills()

    def _refresh_subskills(self) -> None:
        skill = self.skill_var.get()
        options = ["Any", *subskills_for(skill)]
        if self.subskill_var.get() not in options:
            self.subskill_var.set("Any")
        self.subskill_combo.config(values=options)

    def apply_preset(
        self,
        *,
        track: str | None = None,
        skill: str | None = None,
        subskill: str | None = None,
        num_questions: int | None = None,
        level: int | None = None,
        question_type: str | None = None,
        strategy: str | None = None,
        mode_mix_override: tuple[int, int, int] | None = None,
        launch_context: str | None = None,
        profile_override=None,
        summer_program_launch: SummerProgramLaunch | None = None,
    ) -> None:
        if track is not None:
            self.track_var.set(track)
        self._apply_track_filter()
        if skill is not None:
            self.skill_var.set(skill)
        self._on_skill_change()
        if subskill is not None:
            self.subskill_var.set(subskill)
        if num_questions is not None:
            self.num_var.set(int(num_questions))
        if level is not None:
            self.level_var.set(int(level))
        if question_type is not None:
            self.type_var.set(str(question_type))
        if strategy is not None:
            self.strategy_var.set(str(strategy))
        else:
            self.strategy_var.set("focused")
        self._mode_mix_override = mode_mix_override
        self._profile_override = profile_override
        self._summer_program_launch = summer_program_launch
        if launch_context is not None:
            self._launch_context = str(launch_context)

    def _build_historical_questions(self):
        return quiz_strategies.build_historical_questions(self)

    def _build_sat_psat_questions(
        self,
        *,
        profile_id: int,
        skill_stats,
        mode_acc_cache: dict[str, dict[str, float]],
        active_override: tuple[int, int, int] | None,
        seen_signatures: set[str],
    ):
        return quiz_strategies.build_sat_psat_questions(
            self,
            profile_id=profile_id,
            skill_stats=skill_stats,
            mode_acc_cache=mode_acc_cache,
            active_override=active_override,
            seen_signatures=seen_signatures,
        )

    def _build_free_mode_questions(
        self,
        *,
        profile_id: int,
        selected_skill: str,
        chosen_subskill: str | None,
        skill_stats,
        mode_acc_cache: dict[str, dict[str, float]],
        active_override: tuple[int, int, int] | None,
        seen_signatures: set[str],
    ):
        return quiz_strategies.build_free_mode_questions(
            self,
            profile_id=profile_id,
            selected_skill=selected_skill,
            chosen_subskill=chosen_subskill,
            skill_stats=skill_stats,
            mode_acc_cache=mode_acc_cache,
            active_override=active_override,
            seen_signatures=seen_signatures,
        )

    def _build_learning_blend_questions(
        self,
        *,
        profile_id: int,
        selected_skill: str,
        chosen_subskill: str | None,
        skill_stats,
        mode_acc_cache: dict[str, dict[str, float]],
        active_override: tuple[int, int, int] | None,
        seen_signatures: set[str],
    ):
        return quiz_strategies.build_learning_blend_questions(
            self,
            profile_id=profile_id,
            selected_skill=selected_skill,
            chosen_subskill=chosen_subskill,
            skill_stats=skill_stats,
            mode_acc_cache=mode_acc_cache,
            active_override=active_override,
            seen_signatures=seen_signatures,
        )

    def _build_focused_questions(
        self,
        *,
        profile_id: int,
        selected_skill: str,
        chosen_subskill: str | None,
        skill_stats,
        mode_acc_cache: dict[str, dict[str, float]],
        active_override: tuple[int, int, int] | None,
        seen_signatures: set[str],
    ):
        return quiz_strategies.build_focused_questions(
            self,
            profile_id=profile_id,
            selected_skill=selected_skill,
            chosen_subskill=chosen_subskill,
            skill_stats=skill_stats,
            mode_acc_cache=mode_acc_cache,
            active_override=active_override,
            seen_signatures=seen_signatures,
        )

    def start_quiz(self) -> None:
        profile = self._active_profile()
        if profile is None:
            messagebox.showerror("No profile", "Please select a profile first.")
            return
        if self._try_resume_saved_quiz(profile.id):
            return
        attempts = db.list_attempts(profile.id)
        skill_stats = build_skill_stats(attempts, tuple(SKILL_ORDER))
        mode_acc_cache: dict[str, dict[str, float]] = {}
        self._questions = []
        seen_signatures: set[str] = set()
        self._record_attempt = True
        self._record_progress = True
        active_override = self._mode_mix_override
        # Preset overrides apply to one quiz launch; avoid leaking into later manual runs.
        self._mode_mix_override = None
        chosen_subskill = None if self.subskill_var.get() == "Any" else self.subskill_var.get()
        strategy = self.strategy_var.get()
        selected_skill = self.skill_var.get()
        if self._summer_program_launch is not None:
            try:
                plan = build_task_quiz_plan(self._summer_program_launch)
            except ValueError as exc:
                messagebox.showerror("Summer Program", str(exc))
                self._summer_program_launch = None
                return
            self._load_program_plan(plan)
            return
        if (
            strategy in {"learning_blend", "free_mode"}
            and selected_skill not in SKILL_ORDER
            and selected_skill != "mixed"
        ):
            strategy = "focused"
        result = None
        if strategy == "historical_practice":
            result = self._build_historical_questions()
            if result is None:
                messagebox.showerror(
                    "No historical questions",
                    "No parsed historical questions found. Add PDFs to data/reference_pdfs/historical and click 'Ingest PDFs'.",
                )
                return
        else:
            try:
                if strategy == "sat_psat_unit":
                    result = self._build_sat_psat_questions(
                        profile_id=profile.id,
                        skill_stats=skill_stats,
                        mode_acc_cache=mode_acc_cache,
                        active_override=active_override,
                        seen_signatures=seen_signatures,
                    )
                elif strategy == "free_mode":
                    result = self._build_free_mode_questions(
                        profile_id=profile.id,
                        selected_skill=selected_skill,
                        chosen_subskill=chosen_subskill,
                        skill_stats=skill_stats,
                        mode_acc_cache=mode_acc_cache,
                        active_override=active_override,
                        seen_signatures=seen_signatures,
                    )
                elif strategy == "learning_blend" and selected_skill != "mixed":
                    result = self._build_learning_blend_questions(
                        profile_id=profile.id,
                        selected_skill=selected_skill,
                        chosen_subskill=chosen_subskill,
                        skill_stats=skill_stats,
                        mode_acc_cache=mode_acc_cache,
                        active_override=active_override,
                        seen_signatures=seen_signatures,
                    )
                else:
                    result = self._build_focused_questions(
                        profile_id=profile.id,
                        selected_skill=selected_skill,
                        chosen_subskill=chosen_subskill,
                        skill_stats=skill_stats,
                        mode_acc_cache=mode_acc_cache,
                        active_override=active_override,
                        seen_signatures=seen_signatures,
                    )
            except ContentUnavailableError as exc:
                messagebox.showerror("No quiz content", str(exc))
                return

        self._questions = result.questions
        self._attempt_skill = result.attempt_skill
        self._record_progress = result.record_progress
        self.meta_var.set(result.meta)
        self._index = 0
        self._score = 0
        self._answers = []
        self._clear_mistake_recovery()
        self._correct_streak = 0
        self.streak_var.set("")
        self._quiz_started_monotonic = time.monotonic()
        self._persist_quiz_progress()
        for child in self.summary_frame.winfo_children():
            child.destroy()
        self.visual_canvas.pack(fill=tk.X, padx=16)
        self.answer_frame.pack(fill=tk.X, padx=16, pady=10)
        self.submit_btn.master.pack(pady=6)
        self._update_quiz_progress()
        self._show_question()

    def _load_program_plan(self, plan: ProgramQuizPlan) -> None:
        self.type_var.set(plan.question_type)
        self.level_var.set(int(plan.level))
        self._questions = plan.questions
        self._attempt_skill = plan.attempt_skill
        self._record_attempt = True
        self._record_progress = True
        self.meta_var.set(plan.meta)
        self._launch_context = plan.launch_context
        self._index = 0
        self._score = 0
        self._answers = []
        self._clear_mistake_recovery()
        self._clear_scaffold_state()
        self._correct_streak = 0
        self.streak_var.set("")
        self._quiz_started_monotonic = time.monotonic()
        self._persist_quiz_progress()
        for child in self.summary_frame.winfo_children():
            child.destroy()
        self.visual_canvas.pack(fill=tk.X, padx=16)
        self.answer_frame.pack(fill=tk.X, padx=16, pady=10)
        self.submit_btn.master.pack(pady=6)
        self._update_quiz_progress()
        self._show_question()

    def _show_question(self) -> None:
        quiz_flow.show_question(self)
        self._update_quiz_progress()

    def _build_answer_widget(self, question: Question) -> None:
        quiz_flow.build_answer_widget(self, question)

    def submit_answer(self) -> None:
        quiz_flow.submit_answer(self)

    def _show_intuition(self) -> None:
        quiz_flow.show_intuition(self)

    def next_question(self) -> None:
        quiz_flow.next_question(self)

    def _finish_quiz(self) -> None:
        quiz_flow.finish_quiz(self)

    def _render_visual(self, question: Question) -> None:
        quiz_flow.render_visual(self, question)

    def _mode_mix_for_skill(
        self,
        profile_id: int,
        skill: str,
        skill_stats,
        mode_acc_cache: dict[str, dict[str, float]],
        override: tuple[int, int, int] | None,
        *,
        subskill: str | None = None,
    ) -> ModeMix:
        if override is not None:
            return normalize_mode_mix(override[0], override[1], override[2])
        base = default_mode_mix_for_stage(skill_stats.get(skill))
        if skill not in mode_acc_cache:
            mode_acc_cache[skill] = db.mode_accuracy_by_skill(profile_id, skill)
        mode_acc = mode_acc_cache[skill]
        boosted = apply_word_gap_boost(base, mode_acc.get("expression"), mode_acc.get("word"))
        supported = self._supported_modes_for(skill, subskill=subskill)
        intuition = boosted.intuition if "intuition" in supported else 0
        expression = boosted.expression if "expression" in supported else 0
        word = boosted.word if "word" in supported else 0
        if intuition + expression + word <= 0:
            fallback = supported[0] if supported else "expression"
            intuition = 100 if fallback == "intuition" else 0
            expression = 100 if fallback == "expression" else 0
            word = 100 if fallback == "word" else 0
        return normalize_mode_mix(intuition, expression, word)

    def _supported_modes_for(self, skill: str, *, subskill: str | None = None) -> tuple[str, ...]:
        supported: set[str] = set(db.template_modes_for_skill(skill, subskill=subskill))
        if not is_template_only_skill(skill):
            supported.add("expression")
        if can_wrap_skill(skill):
            supported.add("word")
        if is_native_intuition_skill(skill):
            supported.add("intuition")
        if not supported:
            supported.add("expression")
        return tuple(mode for mode in ("intuition", "expression", "word") if mode in supported)

    def _apply_mode_preference(self, question: Question, preferred_mode: str | None) -> Question:
        if preferred_mode == "intuition":
            return question
        if preferred_mode == "word":
            if question.mode == "word":
                return question
            if can_wrap_skill(question.skill):
                return apply_story_wrapper(question, rng=random)
            return question
        return question

    def _pick_mode(self, mix: ModeMix, skill: str, *, subskill: str | None = None) -> str:
        supported = self._supported_modes_for(skill, subskill=subskill)
        labels = ["intuition", "expression", "word"]
        weights = [
            mix.intuition if "intuition" in supported else 0,
            mix.expression if "expression" in supported else 0,
            mix.word if "word" in supported else 0,
        ]
        if sum(weights) <= 0:
            return supported[0] if supported else "expression"
        return random.choices(labels, weights=weights, k=1)[0]

    def _mode_mix_label(self, mix: ModeMix) -> str:
        return f"{mix.intuition}/{mix.expression}/{mix.word}"

    def _generate_question_with_variation(
        self,
        seen_signatures: set[str],
        skill: str,
        level: int,
        question_type: str,
        *,
        subskill: str | None,
        preferred_mode: str | None,
    ) -> Question:
        if not self.vary_numbers_var.get():
            q = generate_question(skill, level, question_type, subskill=subskill, preferred_mode=preferred_mode)
            seen_signatures.add(_question_session_signature(q))
            return q
        last_q: Question | None = None
        for _ in range(10):
            q = generate_question(skill, level, question_type, subskill=subskill, preferred_mode=preferred_mode)
            sig = _question_session_signature(q)
            last_q = q
            if sig not in seen_signatures:
                seen_signatures.add(sig)
                return q
        assert last_q is not None
        seen_signatures.add(_question_session_signature(last_q))
        return last_q

    def _subskill_for_question(self, question: Question) -> str | None:
        return _subskill_for_question(question)

    def _subskill_coverage_by_skill(self, profile_id: int) -> dict[str, float]:
        return _subskill_coverage_by_skill(profile_id)

    def _template_family(self, question: Question) -> str:
        return _template_family(question)

    def _recovery_active(self) -> bool:
        return self._mistake_recovery is not None

    def _current_recovery_question(self) -> Question | None:
        state = self._mistake_recovery
        if state is None:
            return None
        if state.phase in {"followup", "complete"} and state.followup_question is not None:
            return state.followup_question
        return state.source_question

    def _should_offer_mistake_recovery(self, question: Question) -> bool:
        settings = load_ui_settings()
        return should_offer_mistake_recovery(
            summer_mode=settings.summer_mode,
            strategy=self.strategy_var.get(),
            question=question,
        )

    def _question_type_for(self, question: Question) -> str:
        return "mc" if question.choices else "typed"

    def _recovery_meta_for(self, question: Question) -> str:
        template_label = ""
        if question.template_external_id:
            template_label = f" | Template: {question.template_external_id}"
        elif question.template_id is not None:
            template_label = f" | Template #{question.template_id}"
        return f"[{question.question_label}] [{question.mode}] Skill: {question.skill}{template_label}"

    def _recovery_explanation_text(self, question: Question, *, phase: str) -> str:
        explanation = explanation_for(question.skill, subskill=question.subskill)
        return build_mistake_recovery_text(explanation, phase=phase)

    def _render_recovery_question(self, question: Question, *, prompt_prefix: str) -> None:
        self.prompt_var.set(f"{prompt_prefix}: {question.prompt}")
        self.meta_var.set(self._recovery_meta_for(question))
        self.intuition_var.set("")
        self._set_feedback_state(correct=None)
        self._build_answer_widget(question)
        self._render_visual(question)

    def _build_mistake_recovery_followup(self, question: Question) -> Question | None:
        preferred_mode = question.mode if question.mode in {"intuition", "expression", "word"} else None
        try:
            followup = self._generate_question_with_variation(
                {_question_session_signature(question)},
                question.skill,
                self.level_var.get(),
                self._question_type_for(question),
                subskill=question.subskill,
                preferred_mode=preferred_mode,
            )
        except ContentUnavailableError:
            return None
        followup = self._apply_mode_preference(followup, preferred_mode)
        followup.question_label = "Recovery"
        return followup

    def _start_mistake_recovery(self, question: Question, incorrect_answer: str) -> None:
        self._mistake_recovery = MistakeRecoveryState(
            phase="redo",
            source_question=question,
            incorrect_answer=incorrect_answer,
        )
        self.submit_btn.config(text="Try Again")
        self.stuck_btn.state(["disabled"])
        self.next_btn.state(["disabled"])
        self.feedback_var.set("Let's fix this one first.")
        self.recovery_var.set(self._recovery_explanation_text(question, phase="redo"))
        self._render_recovery_question(question, prompt_prefix="Try it again")
        self.submit_btn.state(["!disabled"])
        self._persist_quiz_progress()

    def _show_mistake_recovery_followup(self, followup: Question) -> None:
        self.submit_btn.config(text="Submit Follow-up")
        self.feedback_var.set("Nice correction. Now try one like it on your own.")
        self.recovery_var.set(self._recovery_explanation_text(followup, phase="followup"))
        self._render_recovery_question(followup, prompt_prefix="Recovery Practice")
        self.submit_btn.state(["!disabled"])
        if followup.skill in ARITHMETIC_MODE_EXPLANATIONS:
            self.stuck_btn.state(["!disabled"])
        else:
            self.stuck_btn.state(["disabled"])
        self.next_btn.state(["disabled"])
        self._persist_quiz_progress()

    def _complete_mistake_recovery(self, *, correct: bool) -> None:
        state = self._mistake_recovery
        if state is None:
            return
        question = state.followup_question or state.source_question
        if correct:
            self.feedback_var.set("Nice recovery. You fixed it and used it again.")
            self._set_feedback_state(correct=True)
            self._play_correct_animation()
        else:
            self.feedback_var.set(f"Close. For this follow-up, the answer is {question.correct_answer}.")
            self._set_feedback_state(correct=False)
        state.phase = "complete"
        self.submit_btn.config(text="Submit")
        self.submit_btn.state(["disabled"])
        self.stuck_btn.state(["disabled"])
        self.next_btn.state(["!disabled"])
        self.recovery_var.set(self._recovery_explanation_text(state.source_question, phase="complete"))
        self._persist_quiz_progress()

    def _submit_mistake_recovery(self) -> None:
        state = self._mistake_recovery
        if state is None:
            return
        question = self._current_recovery_question()
        if question is None:
            return
        answer = self.choice_var.get().strip() if question.choices else self.answer_var.get().strip()
        if not answer:
            messagebox.showerror("Missing answer", "Please enter or choose an answer.")
            return
        correct = is_correct_answer(question.correct_answer, answer, self.repeat_var.get())
        if state.phase == "redo":
            if not correct:
                self.feedback_var.set("Use the hint and try again. Focus on the mental model.")
                self._set_feedback_state(correct=False)
                return
            followup = self._build_mistake_recovery_followup(state.source_question)
            if followup is None:
                self._complete_mistake_recovery(correct=True)
                return
            state.phase = "followup"
            state.followup_question = followup
            self._show_mistake_recovery_followup(followup)
            return
        self._complete_mistake_recovery(correct=correct)

    def _advance_after_mistake_recovery(self) -> bool:
        if self._mistake_recovery is None:
            return False
        if self._mistake_recovery.phase != "complete":
            return True
        self._clear_mistake_recovery()
        return False

    def _clear_mistake_recovery(self) -> None:
        self._mistake_recovery = None
        self.recovery_var.set("")
        self.submit_btn.config(text="Submit")

    def _set_feedback_state(self, *, correct: bool | None) -> None:
        if correct is None:
            self.answer_frame.configure(highlightthickness=0)
            return
        color = COLORS["success"] if correct else COLORS["danger"]
        self.answer_frame.configure(highlightthickness=2, highlightbackground=color)

    def _record_streak(self, *, correct: bool) -> None:
        if correct:
            self._correct_streak += 1
        else:
            self._correct_streak = 0
        # UX5: streak with emoji milestones
        streak = self._correct_streak
        if streak == 0:
            self.streak_var.set("")
        elif streak >= 10:
            self.streak_var.set(f"🌟 {streak} in a row!")
        elif streak >= 5:
            self.streak_var.set(f"🔥 Streak: {streak}")
        else:
            self.streak_var.set(f"✨ Streak: {streak}")
        # UX6: update progress bar and score label
        self._update_quiz_progress()

    def _update_quiz_progress(self) -> None:
        """UX6: keep progress bar, counter, and score in sync with quiz state."""
        total = len(self._questions) if self._questions else 0
        answered = len(self._answers) if hasattr(self, "_answers") else 0
        if total > 0:
            pct = (answered / total) * 100.0
            self.quiz_progress_var.set(pct)
            self.quiz_progress_label.set(f"{answered} of {total}")
            self.quiz_score_label.set(f"Score: {self._score}/{answered}" if answered > 0 else "")
        else:
            self.quiz_progress_var.set(0)
            self.quiz_progress_label.set("")
            self.quiz_score_label.set("")

    def _play_correct_animation(self) -> None:
        self._cancel_correct_animation()
        cx = max(24, int(self.visual_canvas.winfo_width() - 28))
        cy = 20
        check_id = self.visual_canvas.create_text(
            cx,
            cy,
            text="✓",
            fill=COLORS["success"],
            font=("Helvetica", 18, "bold"),
            anchor=tk.NE,
        )
        dots: list[int] = []
        for offset in (-16, -8, 0, 8, 16):
            dot = self.visual_canvas.create_oval(
                cx + offset - 2,
                cy + 18 - 2,
                cx + offset + 2,
                cy + 18 + 2,
                fill=COLORS["accent"],
                outline="",
            )
            dots.append(dot)

        def _fade(step: int) -> None:
            if not self.visual_canvas.winfo_exists():
                self._animation_after_id = None
                return
            if step >= 8:
                self.visual_canvas.delete(check_id)
                for dot_id in dots:
                    self.visual_canvas.delete(dot_id)
                self._animation_after_id = None
                return
            self.visual_canvas.move(check_id, 0, -1)
            for idx, dot_id in enumerate(dots):
                self.visual_canvas.move(dot_id, 0, -1 - (idx % 2))
            self._animation_after_id = self.visual_canvas.after(35, lambda: _fade(step + 1))

        _fade(0)

    def _cancel_correct_animation(self) -> None:
        if self._animation_after_id is None:
            return
        try:
            self.visual_canvas.after_cancel(self._animation_after_id)
        except tk.TclError:
            pass
        self._animation_after_id = None

    def shutdown(self) -> None:
        self._cancel_correct_animation()

    def _question_to_payload(self, question: Question) -> dict[str, object]:
        return {
            "skill": question.skill,
            "prompt": question.prompt,
            "correct_answer": question.correct_answer,
            "explanation": question.explanation,
            "choices": question.choices,
            "visual": question.visual,
            "template_id": question.template_id,
            "template_external_id": question.template_external_id,
            "subskill": question.subskill,
            "question_label": question.question_label,
            "mode": question.mode,
            "scaffold_steps": [
                {
                    "prompt": step.prompt,
                    "expected_answer": step.expected_answer,
                    "hint": step.hint,
                }
                for step in (question.scaffold_steps or [])
            ],
        }

    def _question_from_payload(self, payload: dict[str, object]) -> Question:
        raw_choices = payload.get("choices")
        choices = [str(choice) for choice in raw_choices] if isinstance(raw_choices, list) else None
        raw_visual = payload.get("visual")
        visual = raw_visual if isinstance(raw_visual, dict) else None
        raw_scaffold = payload.get("scaffold_steps")
        scaffold_steps = None
        if isinstance(raw_scaffold, list) and raw_scaffold:
            scaffold_steps = []
            for item in raw_scaffold:
                if not isinstance(item, dict):
                    continue
                scaffold_steps.append(
                    ScaffoldStep(
                        prompt=str(item.get("prompt", "")),
                        expected_answer=str(item.get("expected_answer", "")),
                        hint=str(item.get("hint", "")),
                    )
                )
        template_id = payload.get("template_id")
        if template_id is not None:
            template_id = int(template_id)
        return Question(
            skill=str(payload.get("skill", "")),
            prompt=str(payload.get("prompt", "")),
            correct_answer=str(payload.get("correct_answer", "")),
            explanation=str(payload.get("explanation", "")),
            choices=choices,
            visual=visual,
            template_id=template_id,
            template_external_id=str(payload.get("template_external_id")) if payload.get("template_external_id") else None,
            subskill=str(payload.get("subskill")) if payload.get("subskill") else None,
            question_label=str(payload.get("question_label", "Core")),
            mode=str(payload.get("mode", "expression")),
            scaffold_steps=scaffold_steps,
        )

    def _build_progress_state(self) -> str:
        answer_payload: list[dict[str, object]] = []
        for idx, (_question, answer, correct) in enumerate(self._answers):
            answer_payload.append(
                {
                    "question_index": idx,
                    "answer": answer,
                    "correct": bool(correct),
                }
            )
        recovery_payload: dict[str, object] | None = None
        if self._mistake_recovery is not None:
            recovery_payload = {
                "phase": self._mistake_recovery.phase,
                "incorrect_answer": self._mistake_recovery.incorrect_answer,
                "source_question": self._question_to_payload(self._mistake_recovery.source_question),
                "followup_question": (
                    self._question_to_payload(self._mistake_recovery.followup_question)
                    if self._mistake_recovery.followup_question is not None
                    else None
                ),
            }
        profile_override_id = getattr(self._profile_override, "id", None)
        summer_launch_payload = None
        if self._summer_program_launch is not None:
            summer_launch_payload = {
                "profile_id": self._summer_program_launch.profile_id,
                "program_id": self._summer_program_launch.program_id,
                "task_id": self._summer_program_launch.task_id,
            }
        payload = {
            "version": 1,
            "track": self.track_var.get(),
            "skill": self.skill_var.get(),
            "subskill": self.subskill_var.get(),
            "question_type": self.type_var.get(),
            "strategy": self.strategy_var.get(),
            "num_questions": int(self.num_var.get()),
            "level": int(self.level_var.get()),
            "meta": self.meta_var.get(),
            "attempt_skill": self._attempt_skill,
            "record_attempt": bool(self._record_attempt),
            "record_progress": bool(self._record_progress),
            "launch_context": self._launch_context,
            "profile_override_id": profile_override_id,
            "summer_program_launch": summer_launch_payload,
            "index": int(self._index),
            "score": int(self._score),
            "correct_streak": int(self._correct_streak),
            "scaffold_state": {
                "question_index": self._scaffold_question_index,
                "step_index": self._scaffold_step_index,
                "answers": list(self._scaffold_step_answers),
            },
            "questions": [self._question_to_payload(question) for question in self._questions],
            "answers": answer_payload,
            "mistake_recovery": recovery_payload,
        }
        return json.dumps(payload, ensure_ascii=True)

    def _persist_quiz_progress(self) -> None:
        profile = self._active_profile()
        if profile is None or not self._questions:
            return
        state_json = self._build_progress_state()
        self._progress_attempt_id = db.save_quiz_progress(
            profile.id,
            self._progress_attempt_id,
            self._index,
            state_json,
            now_iso(),
        )

    def _clear_quiz_progress(self) -> None:
        if self._progress_attempt_id is None:
            return
        db.clear_quiz_progress(self._progress_attempt_id)
        self._progress_attempt_id = None

    def _try_resume_saved_quiz(self, profile_id: int) -> bool:
        saved = db.load_quiz_progress(profile_id)
        if saved is None:
            return False
        attempt_id, _saved_index, state_json = saved
        if not messagebox.askyesno("Resume quiz", "Resume your in-progress quiz from last session?"):
            db.clear_quiz_progress(attempt_id)
            self._progress_attempt_id = None
            return False
        try:
            payload = json.loads(state_json)
        except json.JSONDecodeError:
            db.clear_quiz_progress(attempt_id)
            self._progress_attempt_id = None
            return False
        if not isinstance(payload, dict):
            db.clear_quiz_progress(attempt_id)
            self._progress_attempt_id = None
            return False

        raw_questions = payload.get("questions", [])
        if not isinstance(raw_questions, list) or not raw_questions:
            db.clear_quiz_progress(attempt_id)
            self._progress_attempt_id = None
            return False

        questions: list[Question] = []
        for item in raw_questions:
            if not isinstance(item, dict):
                continue
            questions.append(self._question_from_payload(item))
        if not questions:
            db.clear_quiz_progress(attempt_id)
            self._progress_attempt_id = None
            return False

        self._progress_attempt_id = attempt_id
        self.track_var.set(str(payload.get("track", "All")))
        self._apply_track_filter()
        self.skill_var.set(str(payload.get("skill", self.skill_var.get())))
        self._on_skill_change()
        self.subskill_var.set(str(payload.get("subskill", "Any")))
        self.type_var.set(str(payload.get("question_type", "both")))
        self.strategy_var.set(str(payload.get("strategy", "focused")))
        self.num_var.set(int(payload.get("num_questions", len(questions))))
        self.level_var.set(int(payload.get("level", 1)))

        self._questions = questions
        self._index = max(0, min(int(payload.get("index", 0)), len(self._questions) - 1))
        self._score = int(payload.get("score", 0))
        self._correct_streak = int(payload.get("correct_streak", 0))
        self._attempt_skill = str(payload.get("attempt_skill")) if payload.get("attempt_skill") else self.skill_var.get()
        self._record_attempt = bool(payload.get("record_attempt", True))
        self._record_progress = bool(payload.get("record_progress", True))
        self._launch_context = str(payload.get("launch_context", "manual"))
        self.meta_var.set(str(payload.get("meta", "")))
        self._profile_override = None
        override_id = payload.get("profile_override_id")
        if override_id is not None:
            for candidate in db.list_profiles():
                if candidate.id == int(override_id):
                    self._profile_override = candidate
                    break
        self._summer_program_launch = None
        raw_launch = payload.get("summer_program_launch")
        if isinstance(raw_launch, dict):
            try:
                self._summer_program_launch = SummerProgramLaunch(
                    profile_id=int(raw_launch.get("profile_id")),
                    program_id=int(raw_launch.get("program_id")),
                    task_id=int(raw_launch.get("task_id")),
                )
            except (TypeError, ValueError):
                self._summer_program_launch = None

        self._answers = []
        raw_answers = payload.get("answers", [])
        if isinstance(raw_answers, list):
            for item in raw_answers:
                if not isinstance(item, dict):
                    continue
                q_idx = int(item.get("question_index", len(self._answers)))
                if q_idx < 0 or q_idx >= len(self._questions):
                    continue
                answer = str(item.get("answer", ""))
                correct = bool(item.get("correct", False))
                self._answers.append((self._questions[q_idx], answer, correct))
        raw_scaffold_state = payload.get("scaffold_state")
        self._clear_scaffold_state()
        if isinstance(raw_scaffold_state, dict):
            q_idx = raw_scaffold_state.get("question_index")
            if q_idx is not None:
                self._scaffold_question_index = int(q_idx)
                self._scaffold_step_index = int(raw_scaffold_state.get("step_index", 0))
                raw_answers = raw_scaffold_state.get("answers", [])
                if isinstance(raw_answers, list):
                    self._scaffold_step_answers = [str(item) for item in raw_answers]

        self._mistake_recovery = None
        raw_recovery = payload.get("mistake_recovery")
        if isinstance(raw_recovery, dict):
            source_payload = raw_recovery.get("source_question")
            phase = str(raw_recovery.get("phase", "redo"))
            if isinstance(source_payload, dict):
                source_question = self._question_from_payload(source_payload)
                followup_payload = raw_recovery.get("followup_question")
                followup_question = (
                    self._question_from_payload(followup_payload)
                    if isinstance(followup_payload, dict)
                    else None
                )
                self._mistake_recovery = MistakeRecoveryState(
                    phase=phase,
                    source_question=source_question,
                    incorrect_answer=str(raw_recovery.get("incorrect_answer", "")),
                    followup_question=followup_question,
                )

        self.streak_var.set(f"Streak: {self._correct_streak}")
        self._quiz_started_monotonic = None
        for child in self.summary_frame.winfo_children():
            child.destroy()
        self.visual_canvas.pack(fill=tk.X, padx=16)
        self.answer_frame.pack(fill=tk.X, padx=16, pady=10)
        self.submit_btn.master.pack(pady=6)
        self.feedback_var.set("Resumed in-progress quiz.")
        if self._mistake_recovery is not None:
            state = self._mistake_recovery
            if state.phase in {"followup", "complete"} and state.followup_question is not None:
                self._render_recovery_question(state.followup_question, prompt_prefix="Recovery Practice")
                if state.phase == "complete":
                    self.feedback_var.set("Resume the next step when you're ready.")
                    self.submit_btn.config(text="Submit")
                    self.submit_btn.state(["disabled"])
                    self.stuck_btn.state(["disabled"])
                    self.next_btn.state(["!disabled"])
                    self.recovery_var.set(self._recovery_explanation_text(state.source_question, phase="complete"))
                else:
                    self.feedback_var.set("Resumed recovery practice.")
                    self.submit_btn.config(text="Submit Follow-up")
                    self.submit_btn.state(["!disabled"])
                    if state.followup_question.skill in ARITHMETIC_MODE_EXPLANATIONS:
                        self.stuck_btn.state(["!disabled"])
                    else:
                        self.stuck_btn.state(["disabled"])
                    self.next_btn.state(["disabled"])
                    self.recovery_var.set(self._recovery_explanation_text(state.followup_question, phase="followup"))
            else:
                self._render_recovery_question(state.source_question, prompt_prefix="Try it again")
                self.feedback_var.set("Resumed recovery step.")
                self.submit_btn.config(text="Try Again")
                self.submit_btn.state(["!disabled"])
                self.stuck_btn.state(["disabled"])
                self.next_btn.state(["disabled"])
                self.recovery_var.set(self._recovery_explanation_text(state.source_question, phase="redo"))
            return True
        self._show_question()
        if self._index < len(self._answers):
            _, _saved_answer, saved_correct = self._answers[self._index]
            if saved_correct:
                self.feedback_var.set("Answer already recorded as correct. Click Next to continue.")
            else:
                self.feedback_var.set("Answer already recorded. Click Next to continue.")
            self.submit_btn.state(["disabled"])
            self.stuck_btn.state(["disabled"])
            self.next_btn.state(["!disabled"])
        return True

    def _show_quiz_summary(
        self, score: int, total: int, keyed_total: int, retake_required: bool,
        assignments: int, recommendations: list, mistakes: list, elapsed_seconds: float | None,
        summer_program_note: str | None = None,
    ) -> None:
        """Render a structured celebration screen for a completed quiz."""
        settings = load_ui_settings()
        summer_mode = settings.summer_mode
        child_profile = self._is_child_profile()
        for child in self.summary_frame.winfo_children():
            child.destroy()

        # Hide main quiz elements during summary
        self.visual_canvas.pack_forget()
        self.answer_frame.pack_forget()
        self.submit_btn.master.pack_forget()  # Hide the entire btns frame

        # Build celebration card
        pct = (score / max(1, total)) * 100
        bg_color = "#d4ead8" if pct >= 80 else "#f6e8bf" if pct >= 60 else "#fceceb"
        card = tk.Frame(self.summary_frame, bg=bg_color, bd=1, relief=tk.RIDGE)
        card.pack(fill=tk.X, pady=(0, 12))

        header = "Practice Complete!" if child_profile else "Quiz Complete!"
        if pct == 100:
            header = "Perfect Practice!" if child_profile else "🌟 Perfect Score! 🌟"
        elif pct >= 80:
            header = "Nice Practice!" if child_profile else "Great Job! 🎉"
        ttk.Label(card, text=header, font=("Segoe UI", 16, "bold"), background=bg_color).pack(pady=(12, 4))
        ttk.Label(card, text=f"{score} / {total}", font=("Segoe UI", 24, "bold"), background=bg_color).pack(pady=4)

        if elapsed_seconds is not None:
            mins, secs = int(elapsed_seconds // 60), int(elapsed_seconds % 60)
            time_str = f"Time: {mins}m {secs}s" if mins > 0 else f"Time: {secs}s"
            ttk.Label(card, text=time_str, font=("Segoe UI", 10), background=bg_color).pack(pady=(0, 12))
        if summer_program_note:
            ttk.Label(card, text=summer_program_note, font=("Segoe UI", 10), background=bg_color, wraplength=720).pack(
                pady=(0, 12)
            )
        if child_profile:
            next_label = "practice this skill again"
            if recommendations:
                top_skill = recommendations[0].skill
                next_label = f"try {SKILL_LABELS.get(top_skill, top_skill)} next"
            result_text = (
                "You got every question right."
                if score == total
                else f"You got {score} right and have {len(mistakes)} to review below."
            )
            ttk.Label(
                card,
                text=f"What happened: {result_text}",
                font=("Segoe UI", 11, "bold"),
                background=bg_color,
                wraplength=720,
            ).pack(pady=(0, 4))
            ttk.Label(
                card,
                text=f"Next step: {next_label}.",
                font=("Segoe UI", 11),
                background=bg_color,
                wraplength=720,
            ).pack(pady=(0, 12))

        # Action buttons
        actions = ttk.Frame(self.summary_frame)
        actions.pack(fill=tk.X, pady=(0, 12))

        if retake_required and not summer_mode and not child_profile:
            ttk.Label(actions, text="Mastery requires 100% — Try Again?").pack(side=tk.LEFT, padx=(0, 12))
            ttk.Button(actions, text="Retake Quiz", style="Accent.TButton", command=self.start_quiz).pack(side=tk.LEFT)
        else:
            if child_profile:
                primary_label = "Practice This Again"
            else:
                primary_label = "Practice More" if not summer_mode else "Keep Practicing"
            ttk.Button(actions, text=primary_label, command=self.start_quiz).pack(side=tk.LEFT, padx=(0, 8))
            if recommendations:
                top_nav = recommendations[0].skill
                label = SKILL_LABELS.get(top_nav, top_nav)

                def _nav(s=top_nav):
                    self.skill_var.set(s)
                    self.subskill_var.set("Any")
                    self.start_quiz()

                if child_profile:
                    next_label = f"Try Next: {label}"
                else:
                    next_label = f"Next: {label}" if not summer_mode else f"Next Practice: {label}"
                ttk.Button(actions, text=next_label, style="Accent.TButton", command=_nav).pack(side=tk.LEFT)

        # Scrolling details pane
        details_canvas = tk.Canvas(self.summary_frame, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.summary_frame, orient="vertical", command=details_canvas.yview)
        scrollable_frame = ttk.Frame(details_canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: details_canvas.configure(scrollregion=details_canvas.bbox("all"))
        )
        details_canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        details_canvas.configure(yscrollcommand=scrollbar.set)

        details_canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        if mistakes:
            review_title = "Let's review what you missed:"
            if summer_mode:
                review_title = "Let's look at the tricky ones:"
            ttk.Label(scrollable_frame, text=review_title, font=("Segoe UI", 12, "bold")).pack(anchor=tk.W, pady=(0, 8))
            for i, (prompt, answer, explanation) in enumerate(mistakes):
                row = ttk.Frame(scrollable_frame)
                row.pack(fill=tk.X, pady=4, anchor=tk.W)
                ttk.Label(row, text=f"Q: {prompt}", font=("Segoe UI", 10, "bold"), wraplength=700).pack(anchor=tk.W)
                ttk.Label(row, text=f"Your answer: {answer}", foreground=COLORS["accent_strong"]).pack(anchor=tk.W)
                ttk.Label(row, text=explanation, wraplength=700, foreground=COLORS["text_secondary"]).pack(anchor=tk.W)
        else:
            no_mistakes = "Nothing tricky to review today." if child_profile else "No mistakes to review!"
            ttk.Label(scrollable_frame, text=no_mistakes).pack(anchor=tk.W)


def _subskill_for_question(question: Question) -> str | None:
    if getattr(question, "subskill", None):
        return str(question.subskill)
    return None


def _template_family(question: Question) -> str:
    external_id = getattr(question, "template_external_id", None)
    if external_id:
        parts = str(external_id).split(".")
        if len(parts) >= 3:
            return ".".join(parts[:-1])
        return str(external_id)
    template_id = getattr(question, "template_id", None)
    if template_id is not None:
        return f"id:{int(template_id)}"
    return ""


def _question_session_signature(question: Question) -> str:
    prompt = " ".join(str(question.prompt).split())
    answer = str(question.correct_answer)
    return f"{question.skill}|{question.mode}|{prompt}|{answer}"


def _subskill_coverage_by_skill(profile_id: int) -> dict[str, float]:
    progress = db.list_subskill_progress(profile_id)
    by_skill: dict[str, dict[str, int]] = {}
    for item in progress:
        if item.skill not in by_skill:
            by_skill[item.skill] = {"mastered": 0, "total": 0}
        by_skill[item.skill]["total"] += 1
        if item.mastered:
            by_skill[item.skill]["mastered"] += 1
    out: dict[str, float] = {}
    for skill, counts in by_skill.items():
        out[skill] = float(counts["mastered"]) / float(max(1, counts["total"]))
    return out
