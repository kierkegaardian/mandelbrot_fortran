from __future__ import annotations

import tkinter as tk
import hashlib
from tkinter import messagebox, ttk
import webbrowser
import random
import time
from pathlib import Path
import subprocess

from . import db
from .explanations import QUIZ_EXPLANATION
from .learning_engine import (
    ModeMix,
    apply_word_gap_boost,
    build_blended_plan,
    build_free_mode_plan,
    build_skill_stats,
    default_mode_mix_for_stage,
    normalize_mode_mix,
    recommend_next_skill_paths,
    recommend_next_skills_soft,
)
from .quiz_answers import is_correct_answer
from .quiz_engine import QUESTION_TYPES, Question, generate_question
from .story_wrapper import apply_story_wrapper, can_wrap_skill
from .curriculum import curriculum_pdf_path, get_curriculum_for_skill
from .paths import data_dir, worksheets_dir
from .quiz_visuals import render_quiz_visual
from .skill_graph import (
    SKILLS,
    SKILL_LABELS,
    SKILL_ORDER,
    SKILL_PREREQUISITE_WEIGHTS,
    SUBSKILL_STREAK_TO_MASTER,
    skills_in_track,
    subskills_for,
    track_names,
)
from .time_utils import now_iso
from .ui_explain import ExplanationPanel
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

        self._build_controls()
        self._build_view()

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
            frame,
            textvariable=self.subskill_var,
            values=["Any"],
            state="readonly",
            width=24,
        )
        self.subskill_combo.pack(fill=tk.X, pady=(0, 8))
        ttk.Label(frame, text="Curriculum source:").pack(anchor=tk.W)
        self.curriculum_label = ttk.Label(frame, text="No source mapped", foreground="#4f6b7a")
        self.curriculum_label.pack(anchor=tk.W, pady=(0, 4))
        ttk.Button(frame, text="Open Source PDF", command=self._open_curriculum_pdf).pack(anchor=tk.W)
        ttk.Label(frame, text="(Choose a skill to refresh)").pack(anchor=tk.W, padx=2, pady=(0, 8))
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
        ttk.Button(test_btns, text="Open Full Test", command=self._open_historical_test).pack(side=tk.LEFT)
        ttk.Button(test_btns, text="Print Test Mode", command=self._print_historical_test).pack(side=tk.LEFT, padx=(6, 0))
        ttk.Button(test_btns, text="Ingest PDFs", command=self._ingest_historical_pdfs).pack(side=tk.LEFT, padx=(6, 0))
        ttk.Button(test_btns, text="Ingest Answer Keys", command=self._ingest_historical_answer_keys).pack(
            side=tk.LEFT, padx=(6, 0)
        )
        ttk.Button(test_btns, text="Refresh", command=self._refresh_historical_tests).pack(side=tk.LEFT, padx=(6, 0))

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
        ttk.Combobox(frame, textvariable=self.type_var, values=QUESTION_TYPES, state="readonly").pack(
            fill=tk.X, pady=(0, 8)
        )

        ttk.Label(frame, text="Strategy").pack(anchor=tk.W)
        ttk.Combobox(
            frame,
            textvariable=self.strategy_var,
            values=["focused", "learning_blend", "free_mode", "sat_psat_unit", "historical_practice"],
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

        ttk.Button(frame, text="Start Quiz", command=self.start_quiz).pack(fill=tk.X, pady=(6, 12))

        self.explain = ExplanationPanel(frame)
        self.explain.set_explanation(QUIZ_EXPLANATION)
        self.explain.frame.pack(fill=tk.X, pady=(12, 0))
        self._update_curriculum_label()
        self._refresh_subskills()
        self._refresh_historical_tests()
        self._apply_track_filter()

    def _build_view(self) -> None:
        self.prompt_var = tk.StringVar(value="Choose settings on the left to start a quiz.")
        ttk.Label(self.view_frame, textvariable=self.prompt_var, font=("Helvetica", 14, "bold")).pack(pady=12)
        self.meta_var = tk.StringVar(value="")
        ttk.Label(self.view_frame, textvariable=self.meta_var, foreground="#2d5d7c").pack(pady=(0, 4))

        self.visual_canvas = tk.Canvas(self.view_frame, bg="#f7f7f7", height=260)
        self.visual_canvas.pack(fill=tk.X, padx=16)

        self.answer_frame = ttk.Frame(self.view_frame)
        self.answer_frame.pack(fill=tk.X, padx=16, pady=10)

        self.answer_var = tk.StringVar(value="")
        self.choice_var = tk.StringVar(value="")
        self.repeat_var = tk.BooleanVar(value=False)

        self.feedback_var = tk.StringVar(value="")
        ttk.Label(self.view_frame, textvariable=self.feedback_var, foreground="#2f6f3e").pack(pady=(6, 4))
        self.intuition_var = tk.StringVar(value="")
        ttk.Label(self.view_frame, textvariable=self.intuition_var, foreground="#2d5d7c", wraplength=780).pack(pady=(0, 4))

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

        self.summary_box = tk.Text(self.view_frame, height=8, wrap=tk.WORD, font=("Helvetica", 10))
        self.summary_box.pack(fill=tk.BOTH, expand=True, padx=16, pady=8)
        self.summary_box.config(state=tk.DISABLED)

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
        root = data_dir() / "reference_pdfs"
        candidates: list[Path] = []
        for folder in (root / "historical", root):
            if folder.exists():
                candidates.extend(sorted(folder.glob("*.pdf")))
        out: dict[str, Path] = {}
        for path in candidates:
            name = path.name.lower()
            if "answer" in name or "key" in name or "solution" in name:
                continue
            if any(token in name for token in ("sat", "psat", "gre")):
                label = path.stem.replace("_", " ").replace("-", " ").strip()
                out[label] = path
        self._historical_tests = dict(sorted(out.items(), key=lambda kv: kv[0].lower()))
        labels = list(self._historical_tests.keys())
        self.historical_combo.config(values=labels)
        if labels and self.historical_test_var.get() not in self._historical_tests:
            self.historical_test_var.set(labels[0])
        if not labels:
            self.historical_test_var.set("")

    def _open_historical_test(self) -> None:
        if not self._historical_tests:
            messagebox.showerror(
                "No SAT/PSAT/GRE PDFs found",
                "Drop PDF files with 'sat', 'psat', or 'gre' in filename under data/reference_pdfs/historical/ and refresh.",
            )
            return
        label = self.historical_test_var.get().strip()
        path = self._historical_tests.get(label)
        if path is None:
            messagebox.showerror("No test selected", "Pick a historical SAT/PSAT/GRE test first.")
            return
        webbrowser.open(f"file://{path}")

    def _ingest_historical_pdfs(self) -> None:
        script = Path("scripts/ingest_historical_tests.py")
        if not script.exists():
            messagebox.showerror("Missing ingest script", "scripts/ingest_historical_tests.py was not found.")
            return
        root = data_dir() / "reference_pdfs" / "historical"
        if not root.exists():
            messagebox.showerror("Missing folder", f"Create folder first: {root}")
            return
        proc = subprocess.run(
            ["python", str(script), "--path", str(root)],
            capture_output=True,
            text=True,
        )
        if proc.returncode != 0:
            messagebox.showerror("Ingest failed", proc.stderr.strip() or proc.stdout.strip() or "Unknown error")
            return
        messagebox.showinfo("Ingest complete", proc.stdout.strip() or "Historical PDFs ingested.")

    def _ingest_historical_answer_keys(self) -> None:
        script = Path("scripts/ingest_historical_answer_keys.py")
        if not script.exists():
            messagebox.showerror("Missing ingest script", "scripts/ingest_historical_answer_keys.py was not found.")
            return
        root = data_dir() / "reference_pdfs" / "historical_keys"
        if not root.exists():
            messagebox.showerror("Missing folder", f"Create folder first: {root}")
            return
        proc = subprocess.run(
            ["python", str(script), "--path", str(root)],
            capture_output=True,
            text=True,
        )
        if proc.returncode != 0:
            messagebox.showerror("Answer key ingest failed", proc.stderr.strip() or proc.stdout.strip() or "Unknown error")
            return
        messagebox.showinfo("Answer keys ingested", proc.stdout.strip() or "Historical answer keys ingested.")

    def _print_historical_test(self) -> None:
        label = self.historical_test_var.get().strip()
        if not label:
            messagebox.showerror("No test selected", "Pick a historical SAT/PSAT/GRE test first.")
            return
        tests = db.list_historical_tests(exam_type="all")
        test = next((t for t in tests if t.title.lower() == label.lower()), None)
        if test is None:
            messagebox.showerror("Not indexed", "Ingest this historical PDF first using 'Ingest PDFs'.")
            return
        questions = db.list_historical_questions_for_test(test.id)
        if not questions:
            messagebox.showerror("No questions", "No parsed questions found for this test.")
            return
        out_dir = worksheets_dir()
        safe = "".join(ch if ch.isalnum() or ch in {"_", "-"} else "_" for ch in test.exam_code)
        out = out_dir / f"historical_test_{safe}.html"
        parts = [
            "<html><head><meta charset='utf-8'><title>Historical Test</title></head><body>",
            f"<h1>{test.title}</h1>",
            "<p>Print Test Mode (answers hidden)</p>",
        ]
        for q in questions:
            parts.append(f"<h3>{q.question_number}. {q.prompt}</h3>")
            choices = [q.choice_a, q.choice_b, q.choice_c, q.choice_d, q.choice_e]
            letters = ["A", "B", "C", "D", "E"]
            for letter, choice in zip(letters, choices):
                if choice:
                    parts.append(f"<p>{letter}. {choice}</p>")
            parts.append("<hr/>")
        parts.append("</body></html>")
        out.write_text("\n".join(parts), encoding="utf-8")
        webbrowser.open(f"file://{out}")

    def _template_only_quiz_skills(self) -> list[str]:
        skills = {
            str(item.skill)
            for item in db.list_all_question_templates(active_only=True)
            if item.skill and item.skill not in SKILLS and item.skill != "mixed"
        }
        return sorted(skills)

    def _quiz_skill_values_for_track(self, track: str) -> list[str]:
        skills = list(skills_in_track(track))
        if track == "All":
            skills.extend(self._template_only_quiz_skills())
            # Preserve canonical skill order while including template-only skills.
            merged = list(dict.fromkeys(skills))
            merged.append("mixed")
            return merged
        return skills

    def _apply_track_filter(self) -> None:
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
        if launch_context is not None:
            self._launch_context = str(launch_context)

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
        self._quiz_started_monotonic = time.monotonic()
        self.summary_box.config(state=tk.NORMAL)
        self.summary_box.delete("1.0", tk.END)
        self.summary_box.config(state=tk.DISABLED)
        self._show_question()

    def _show_question(self) -> None:
        if not self._questions:
            return
        question = self._questions[self._index]
        self.prompt_var.set(f"Question {self._index + 1}: {question.prompt}")
        template_label = ""
        if question.template_external_id:
            template_label = f" | Template: {question.template_external_id}"
        elif question.template_id is not None:
            template_label = f" | Template #{question.template_id}"
        self.meta_var.set(f"[{question.question_label}] [{question.mode}] Skill: {question.skill}{template_label}")
        self.feedback_var.set("")
        self.intuition_var.set("")
        self._build_answer_widget(question)
        self._render_visual(question)
        self.next_btn.state(["disabled"])
        self.submit_btn.state(["!disabled"])
        if question.skill in {"sat_math", "psat_math"}:
            self.stuck_btn.state(["!disabled"])
        else:
            self.stuck_btn.state(["disabled"])

    def _build_answer_widget(self, question: Question) -> None:
        for child in self.answer_frame.winfo_children():
            child.destroy()
        self.answer_var.set("")
        self.choice_var.set("")
        self.repeat_var.set(False)

        if question.choices:
            ttk.Label(self.answer_frame, text="Choose one:").pack(anchor=tk.W)
            for choice in question.choices:
                ttk.Radiobutton(
                    self.answer_frame, text=choice, variable=self.choice_var, value=choice
                ).pack(anchor=tk.W)
        else:
            ttk.Label(self.answer_frame, text="Type your answer:").pack(anchor=tk.W)
            ttk.Entry(self.answer_frame, textvariable=self.answer_var).pack(fill=tk.X)
            if question.skill == "fractions" or (question.visual and question.visual.get("kind") == "fraction"):
                hint = ttk.Frame(self.answer_frame)
                hint.pack(anchor=tk.W, pady=(6, 0))
                repeat_toggle = ttk.Checkbutton(hint, text="Repeating", variable=self.repeat_var)
                repeat_toggle.pack(side=tk.LEFT)
                ttk.Label(
                    hint,
                    text="(parentheses wrap repeating digits: 0.1(6); checkbox repeats entire decimal part)",
                ).pack(
                    side=tk.LEFT, padx=(6, 0)
                )
                repeat_help = ttk.Label(hint, text="Example: 0.12 + repeating = 0.121212…", foreground="#4f6b7a")

                def _toggle_repeat_help() -> None:
                    if self.repeat_var.get():
                        repeat_help.pack(side=tk.LEFT, padx=(8, 0))
                    else:
                        repeat_help.pack_forget()

                repeat_toggle.configure(command=_toggle_repeat_help)
                _toggle_repeat_help()

    def submit_answer(self) -> None:
        if not self._questions:
            return
        question = self._questions[self._index]
        answer = self.choice_var.get().strip() if question.choices else self.answer_var.get().strip()
        if not answer:
            messagebox.showerror("Missing answer", "Please enter or choose an answer.")
            return

        if not question.correct_answer:
            correct = False
            self.feedback_var.set("Answer recorded. This historical item has no answer key loaded.")
        else:
            correct = is_correct_answer(question.correct_answer, answer, self.repeat_var.get())
            if correct:
                self._score += 1
                self.feedback_var.set("Correct!")
            else:
                self.feedback_var.set(f"Not quite. Correct answer: {question.correct_answer}")
        self._answers.append((question, answer, correct))

        self.submit_btn.state(["disabled"])
        self.stuck_btn.state(["disabled"])
        self.next_btn.state(["!disabled"])

    def _show_intuition(self) -> None:
        if not self._questions:
            return
        question = self._questions[self._index]
        if question.skill not in {"sat_math", "psat_math"}:
            return
        prefix = "SAT intuition" if question.skill == "sat_math" else "PSAT intuition"
        self.intuition_var.set(f"{prefix}: {question.explanation}")

    def next_question(self) -> None:
        if self._index + 1 < len(self._questions):
            self._index += 1
            self._show_question()
        else:
            self._finish_quiz()

    def _finish_quiz(self) -> None:
        profile = self._profile_getter()
        if profile is None:
            return
        if not self._record_attempt:
            self.prompt_var.set("Practice complete.")
            self.feedback_var.set("")
            self.next_btn.state(["disabled"])
            return
        completed_at = now_iso()
        elapsed_seconds = None
        if self._quiz_started_monotonic is not None:
            elapsed_seconds = max(0.0, time.monotonic() - self._quiz_started_monotonic)
        attempt_id = db.create_attempt(
            profile_id=profile.id,
            quiz_set_id=None,
            skill=self._attempt_skill or self.skill_var.get(),
            question_type=self.type_var.get(),
            num_questions=len(self._questions),
            level=self.level_var.get(),
            score=self._score,
            created_at=completed_at,
            elapsed_seconds=elapsed_seconds,
        )
        for question, answer, correct in self._answers:
            if self._record_progress:
                subskill = _subskill_for_question(question)
                db.upsert_subskill_progress(
                    profile.id,
                    question.skill,
                    subskill,
                    correct,
                    completed_at,
                    SUBSKILL_STREAK_TO_MASTER,
                )
            db.add_question_result(
                attempt_id,
                question.skill,
                question.question_label,
                question.mode,
                question.prompt,
                question.correct_answer,
                answer,
                correct,
                question.explanation,
            )
        completed_assignments = db.evaluate_assignments_for_attempt(profile.id, attempt_id, completed_at)
        if self._launch_context == "daily_review":
            db.record_daily_review_completion(profile.id, completed_at)

        summary = f"Score: {self._score} / {len(self._questions)}\n\n"
        keyed_total = sum(1 for q, _a, _c in self._answers if q.correct_answer)
        if keyed_total < len(self._questions):
            summary += (
                f"Items with answer keys: {keyed_total} / {len(self._questions)} "
                "(others were recorded as practice only)\n\n"
            )
        if self._attempt_skill != "historical_practice" and self._score < len(self._questions):
            summary += "Retake required: mastery completion needs 100% on a quiz attempt.\n\n"
        if completed_assignments > 0:
            summary += f"Assignments completed: {completed_assignments}\n\n"
        branch_recommendations = recommend_next_skill_paths(
            tuple(SKILL_ORDER),
            SKILL_PREREQUISITE_WEIGHTS,
            build_skill_stats(db.list_attempts(profile.id), tuple(SKILL_ORDER)),
            subskill_coverage=_subskill_coverage_by_skill(profile.id),
            limit=3,
        )
        if branch_recommendations:
            summary += "Suggested next paths:\n"
            for item in branch_recommendations:
                reason = item.reasons[0] if item.reasons else "Strong next step."
                summary += f"- {SKILL_LABELS.get(item.skill, item.skill)}: {reason}\n"
            summary += "\n"
        summary += "Mistake explanations:\n"
        for question, answer, correct in self._answers:
            if correct:
                continue
            summary += f"- {question.prompt}\n  Your answer: {answer}\n  {question.explanation}\n\n"

        self.summary_box.config(state=tk.NORMAL)
        self.summary_box.delete("1.0", tk.END)
        self.summary_box.insert(tk.END, summary)
        self.summary_box.config(state=tk.DISABLED)
        if self._attempt_skill == "historical_practice":
            self.prompt_var.set("Historical practice complete.")
        elif self._score == len(self._questions):
            self.prompt_var.set("Quiz complete (100%)!")
        else:
            self.prompt_var.set("Quiz complete (retake needed for mastery).")
        self.feedback_var.set("")
        self.next_btn.state(["disabled"])
        self._launch_context = "manual"
        self._quiz_started_monotonic = None
        self._attempt_skill = None

    def _render_visual(self, question: Question) -> None:
        visual = question.visual
        if not visual:
            return
        render_quiz_visual(self.visual_canvas, visual)

    def _mode_mix_for_skill(
        self,
        profile_id: int,
        skill: str,
        skill_stats,
        mode_acc_cache: dict[str, dict[str, float]],
        override: tuple[int, int, int] | None,
    ) -> ModeMix:
        if override is not None:
            return normalize_mode_mix(override[0], override[1], override[2])
        base = default_mode_mix_for_stage(skill_stats.get(skill))
        if skill not in mode_acc_cache:
            mode_acc_cache[skill] = db.mode_accuracy_by_skill(profile_id, skill)
        mode_acc = mode_acc_cache[skill]
        boosted = apply_word_gap_boost(base, mode_acc.get("expression"), mode_acc.get("word"))
        if not can_wrap_skill(skill):
            return normalize_mode_mix(boosted.intuition, boosted.expression + boosted.word, 0)
        return boosted

    def _apply_mode_preference(self, question: Question, preferred_mode: str | None) -> Question:
        if preferred_mode == "intuition":
            if question.visual is not None:
                question.mode = "intuition"
            return question
        if preferred_mode == "word":
            if question.mode == "word":
                return question
            if can_wrap_skill(question.skill):
                return apply_story_wrapper(question, rng=random)
            return question
        if preferred_mode == "expression" and question.mode != "word":
            question.mode = "expression"
        return question

    def _pick_mode(self, mix: ModeMix, skill: str) -> str:
        labels = ["intuition", "expression", "word"]
        weights = [mix.intuition, mix.expression, mix.word]
        if not can_wrap_skill(skill):
            weights[1] += weights[2]
            weights[2] = 0
        if sum(weights) <= 0:
            return "expression"
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


def _subskill_for_question(question: Question) -> str:
    if getattr(question, "subskill", None):
        return str(question.subskill)
    subskills = subskills_for(question.skill)
    if not subskills:
        return "core"
    seed = _question_identity_seed(question)
    digest = hashlib.sha1(seed.encode("utf-8")).hexdigest()
    index = int(digest[:10], 16) % len(subskills)
    return subskills[index]


def _question_identity_seed(question: Question) -> str:
    # Keep fallback subskill mapping stable across quiz contexts (Core/Prereq/Review)
    # and wrapper styles (word vs expression) when the underlying math item is the same.
    if question.template_external_id:
        return f"{question.skill}|template_external:{question.template_external_id}"
    if question.template_id is not None:
        return f"{question.skill}|template:{int(question.template_id)}"
    prompt = question.prompt
    marker = "\nQuestion: "
    if marker in prompt:
        prompt = prompt.split(marker, 1)[1]
    prompt = " ".join(prompt.split())
    return f"{question.skill}|prompt:{prompt}|answer:{question.correct_answer}"


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
