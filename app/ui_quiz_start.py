"""Question-plan construction for a new quiz session."""

from __future__ import annotations

import random
import time
import tkinter as tk
from tkinter import messagebox

from . import db
from .learning_engine import (
    build_blended_plan,
    build_free_mode_plan,
    build_skill_stats,
    recommend_next_skills_soft,
)
from .quiz_engine import Question
from .skill_graph import SKILL_ORDER, SKILL_PREREQUISITE_WEIGHTS
from .ui_quiz_generation import _subskill_coverage_by_skill, _template_family


class QuizStartMixin:
    def start_quiz(self) -> None:
        profile = self._profile_getter()
        if profile is None:
            messagebox.showerror("No profile", "Please select a profile first.")
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
        sat_psat_pool = ("sat_math", "psat_math")
        if (
            strategy in {"learning_blend", "free_mode"}
            and selected_skill not in SKILL_ORDER
            and selected_skill != "mixed"
        ):
            strategy = "focused"
        if strategy == "historical_practice":
            rows = db.list_historical_questions(
                exam_type=self.historical_exam_filter_var.get(),
                category=self.historical_category_var.get(),
                limit=self.num_var.get(),
            )
            if not rows:
                messagebox.showerror(
                    "No historical questions",
                    "No parsed historical questions found. Add PDFs to data/reference_pdfs/historical and click 'Ingest PDFs'.",
                )
                return
            self._record_progress = False
            self._attempt_skill = "historical_practice"
            for row in rows:
                choices = [c for c in [row.choice_a, row.choice_b, row.choice_c, row.choice_d, row.choice_e] if c]
                q = Question(
                    skill=f"historical_{self.historical_exam_filter_var.get()}_{row.category}",
                    prompt=row.prompt,
                    correct_answer=str(row.correct_answer or ""),
                    explanation=row.explanation or "Historical item.",
                    choices=choices if choices else None,
                    visual=None,
                    template_id=None,
                    template_external_id=f"historical.q{row.id}",
                    subskill=row.category,
                    question_label=f"Historical {row.section}",
                    mode="word",
                )
                self._questions.append(q)
            self.meta_var.set(
                f"Historical practice: exam={self.historical_exam_filter_var.get()} category={self.historical_category_var.get()}"
            )
        elif strategy == "sat_psat_unit":
            last_family = ""
            for idx in range(self.num_var.get()):
                q_type = self.type_var.get()
                if q_type == "both":
                    q_type = "mc" if idx % 2 == 0 else "typed"
                q_skill = sat_psat_pool[idx % len(sat_psat_pool)]
                mode_mix = self._mode_mix_for_skill(
                    profile.id,
                    q_skill,
                    skill_stats,
                    mode_acc_cache,
                    active_override,
                )
                preferred_mode = self._pick_mode(mode_mix, q_skill)
                q = self._generate_question_with_variation(
                    seen_signatures,
                    q_skill,
                    self.level_var.get(),
                    q_type,
                    subskill=None,
                    preferred_mode=preferred_mode,
                )
                # Avoid same template family in consecutive SAT/PSAT unit items.
                for _ in range(8):
                    family = _template_family(q)
                    if not family or family != last_family:
                        break
                    q = self._generate_question_with_variation(
                        seen_signatures,
                        q_skill,
                        self.level_var.get(),
                        q_type,
                        subskill=None,
                        preferred_mode=preferred_mode,
                    )
                q.question_label = "SAT Unit" if q_skill == "sat_math" else "PSAT Unit"
                q = self._apply_mode_preference(q, preferred_mode)
                self._questions.append(q)
                last_family = _template_family(q)
            self.meta_var.set("SAT/PSAT Unit: SAT+PSAT questions only")
            self._attempt_skill = "sat_math"
        elif strategy == "free_mode":
            target_skill = selected_skill
            if target_skill == "mixed":
                target_skill = (
                    recommend_next_skills_soft(
                        tuple(SKILL_ORDER),
                        SKILL_PREREQUISITE_WEIGHTS,
                        skill_stats,
                        subskill_coverage=_subskill_coverage_by_skill(profile.id),
                        limit=1,
                    )[0]
                    if SKILL_ORDER
                    else "counting"
                )
            plan_items, policy = build_free_mode_plan(
                target_skill=target_skill,
                num_questions=self.num_var.get(),
                skill_order=tuple(SKILL_ORDER),
                prerequisites=SKILL_PREREQUISITE_WEIGHTS,
                stats=skill_stats,
            )
            random.shuffle(plan_items)
            for idx, item in enumerate(plan_items):
                q_type = self.type_var.get()
                if q_type == "both":
                    q_type = "mc" if idx % 2 == 0 else "typed"
                q_level = self.level_var.get() + 1 if item.label == "Preview" else self.level_var.get()
                q_level = max(1, min(3, int(q_level)))
                subskill = chosen_subskill if (item.label == "Core" and item.skill == target_skill) else None
                mode_mix = self._mode_mix_for_skill(
                    profile.id,
                    item.skill,
                    skill_stats,
                    mode_acc_cache,
                    active_override,
                )
                preferred_mode = self._pick_mode(mode_mix, item.skill)
                q = self._generate_question_with_variation(
                    seen_signatures,
                    item.skill,
                    q_level,
                    q_type,
                    subskill=subskill,
                    preferred_mode=preferred_mode,
                )
                q.question_label = item.label
                q = self._apply_mode_preference(q, preferred_mode)
                self._questions.append(q)
            mix_text = self._mode_mix_label(
                self._mode_mix_for_skill(
                    profile.id,
                    target_skill,
                    skill_stats,
                    mode_acc_cache,
                    active_override,
                )
            )
            self.meta_var.set(
                "Free Mode "
                f"{target_skill}: C/Pv/Pr/R {policy.core_pct}/{policy.preview_pct}/{policy.prereq_pct}/{policy.review_pct} "
                f"| Modes I/E/W: {mix_text}"
            )
            self._attempt_skill = target_skill
        elif strategy == "learning_blend" and selected_skill != "mixed":
            plan_items, policy = build_blended_plan(
                target_skill=selected_skill,
                num_questions=self.num_var.get(),
                skill_order=tuple(SKILL_ORDER),
                prerequisites=SKILL_PREREQUISITE_WEIGHTS,
                stats=skill_stats,
            )
            random.shuffle(plan_items)
            for idx, item in enumerate(plan_items):
                q_type = self.type_var.get()
                if q_type == "both":
                    q_type = "mc" if idx % 2 == 0 else "typed"
                subskill = chosen_subskill if item.label == "Core" else None
                mode_mix = self._mode_mix_for_skill(
                    profile.id,
                    item.skill,
                    skill_stats,
                    mode_acc_cache,
                    active_override,
                )
                preferred_mode = self._pick_mode(mode_mix, item.skill)
                q = self._generate_question_with_variation(
                    seen_signatures,
                    item.skill,
                    self.level_var.get(),
                    q_type,
                    subskill=subskill,
                    preferred_mode=preferred_mode,
                )
                q.question_label = item.label
                q = self._apply_mode_preference(q, preferred_mode)
                self._questions.append(q)
            mix_text = self._mode_mix_label(
                self._mode_mix_for_skill(
                    profile.id,
                    selected_skill,
                    skill_stats,
                    mode_acc_cache,
                    active_override,
                )
            )
            self.meta_var.set(f"Blend: {policy.core_pct}/{policy.prereq_pct}/{policy.review_pct} | Modes I/E/W: {mix_text}")
            self._attempt_skill = selected_skill
        else:
            for idx in range(self.num_var.get()):
                q_type = self.type_var.get()
                if q_type == "both":
                    q_type = "mc" if idx % 2 == 0 else "typed"
                mode_mix = self._mode_mix_for_skill(
                    profile.id,
                    selected_skill,
                    skill_stats,
                    mode_acc_cache,
                    active_override,
                )
                preferred_mode = self._pick_mode(mode_mix, selected_skill)
                q = self._generate_question_with_variation(
                    seen_signatures,
                    selected_skill,
                    self.level_var.get(),
                    q_type,
                    subskill=chosen_subskill,
                    preferred_mode=preferred_mode,
                )
                q.question_label = "Core"
                q = self._apply_mode_preference(q, preferred_mode)
                self._questions.append(q)
            self.meta_var.set(f"Modes I/E/W: {self._mode_mix_label(mode_mix)}")
            self._attempt_skill = selected_skill
        self._index = 0
        self._score = 0
        self._answers = []
        self._clear_mistake_recovery()
        self._completion_created_at = None
        self._clear_quiz_progress()
        self._quiz_started_monotonic = time.monotonic()
        self.summary_box.config(state=tk.NORMAL)
        self.summary_box.delete("1.0", tk.END)
        self.summary_box.config(state=tk.DISABLED)
        self._show_question()
        self._persist_quiz_progress()
