from __future__ import annotations

import tkinter as tk
import hashlib
from tkinter import messagebox, ttk
import webbrowser

from . import db
from .explanations import QUIZ_EXPLANATION
from .quiz_answers import is_correct_answer
from .quiz_engine import QUESTION_TYPES, Question, generate_question
from .curriculum import curriculum_pdf_path, get_curriculum_for_skill
from .quiz_visuals import render_quiz_visual
from .skill_graph import SKILLS, SUBSKILL_STREAK_TO_MASTER, skills_in_track, subskills_for, track_names
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
        self.num_var = tk.IntVar(value=5)
        self.level_var = tk.IntVar(value=1)

        self._questions: list[Question] = []
        self._index = 0
        self._score = 0
        self._answers: list[tuple[Question, str, bool]] = []

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
            values=[*SKILLS, "mixed"],
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

        ttk.Label(frame, text="Question Type").pack(anchor=tk.W)
        ttk.Combobox(frame, textvariable=self.type_var, values=QUESTION_TYPES, state="readonly").pack(
            fill=tk.X, pady=(0, 8)
        )

        ttk.Label(frame, text="Number of Questions").pack(anchor=tk.W)
        int_spinbox(frame, self.num_var, 3, 20).pack(anchor=tk.W, pady=(0, 8))

        ttk.Label(frame, text="Level").pack(anchor=tk.W)
        int_spinbox(frame, self.level_var, 1, 3).pack(anchor=tk.W, pady=(0, 8))

        ttk.Button(frame, text="Start Quiz", command=self.start_quiz).pack(fill=tk.X, pady=(6, 12))

        self.explain = ExplanationPanel(frame)
        self.explain.set_explanation(QUIZ_EXPLANATION)
        self.explain.frame.pack(fill=tk.X, pady=(12, 0))
        self._update_curriculum_label()
        self._refresh_subskills()
        self._apply_track_filter()

    def _build_view(self) -> None:
        self.prompt_var = tk.StringVar(value="Choose settings on the left to start a quiz.")
        ttk.Label(self.view_frame, textvariable=self.prompt_var, font=("Helvetica", 14, "bold")).pack(pady=12)

        self.visual_canvas = tk.Canvas(self.view_frame, bg="#f7f7f7", height=260)
        self.visual_canvas.pack(fill=tk.X, padx=16)

        self.answer_frame = ttk.Frame(self.view_frame)
        self.answer_frame.pack(fill=tk.X, padx=16, pady=10)

        self.answer_var = tk.StringVar(value="")
        self.choice_var = tk.StringVar(value="")
        self.repeat_var = tk.BooleanVar(value=False)

        self.feedback_var = tk.StringVar(value="")
        ttk.Label(self.view_frame, textvariable=self.feedback_var, foreground="#2f6f3e").pack(pady=(6, 4))

        btns = ttk.Frame(self.view_frame)
        btns.pack(pady=6)
        self.submit_btn = ttk.Button(btns, text="Submit", command=self.submit_answer)
        self.next_btn = ttk.Button(btns, text="Next", command=self.next_question)
        self.submit_btn.pack(side=tk.LEFT, padx=4)
        self.next_btn.pack(side=tk.LEFT, padx=4)
        self.next_btn.state(["disabled"])

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

    def _apply_track_filter(self) -> None:
        track = self.track_var.get()
        skills = list(skills_in_track(track))
        values = list(skills)
        if track == "All":
            values.append("mixed")
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

    def start_quiz(self) -> None:
        profile = self._profile_getter()
        if profile is None:
            messagebox.showerror("No profile", "Please select a profile first.")
            return
        self._questions = []
        chosen_subskill = None if self.subskill_var.get() == "Any" else self.subskill_var.get()
        for _ in range(self.num_var.get()):
            q_type = self.type_var.get()
            if q_type == "both":
                q_type = "mc" if _ % 2 == 0 else "typed"
            q = generate_question(self.skill_var.get(), self.level_var.get(), q_type, subskill=chosen_subskill)
            self._questions.append(q)
        self._index = 0
        self._score = 0
        self._answers = []
        self.summary_box.config(state=tk.NORMAL)
        self.summary_box.delete("1.0", tk.END)
        self.summary_box.config(state=tk.DISABLED)
        self._show_question()

    def _show_question(self) -> None:
        if not self._questions:
            return
        question = self._questions[self._index]
        self.prompt_var.set(f"Question {self._index + 1}: {question.prompt}")
        self.feedback_var.set("")
        self._build_answer_widget(question)
        self._render_visual(question)
        self.next_btn.state(["disabled"])
        self.submit_btn.state(["!disabled"])

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

        correct = is_correct_answer(question.correct_answer, answer, self.repeat_var.get())
        if correct:
            self._score += 1
            self.feedback_var.set("Correct!")
        else:
            self.feedback_var.set(f"Not quite. Correct answer: {question.correct_answer}")
        self._answers.append((question, answer, correct))

        self.submit_btn.state(["disabled"])
        self.next_btn.state(["!disabled"])

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
        attempt_id = db.create_attempt(
            profile_id=profile.id,
            quiz_set_id=None,
            skill=self.skill_var.get(),
            question_type=self.type_var.get(),
            num_questions=len(self._questions),
            level=self.level_var.get(),
            score=self._score,
            created_at=now_iso(),
        )
        for question, answer, correct in self._answers:
            subskill = _subskill_for_question(question)
            db.upsert_subskill_progress(
                profile.id,
                question.skill,
                subskill,
                correct,
                now_iso(),
                SUBSKILL_STREAK_TO_MASTER,
            )
            db.add_question_result(
                attempt_id,
                question.skill,
                question.prompt,
                question.correct_answer,
                answer,
                correct,
                question.explanation,
            )

        summary = f"Score: {self._score} / {len(self._questions)}\n\n"
        summary += "Mistake explanations:\n"
        for question, answer, correct in self._answers:
            if correct:
                continue
            summary += f"- {question.prompt}\n  Your answer: {answer}\n  {question.explanation}\n\n"

        self.summary_box.config(state=tk.NORMAL)
        self.summary_box.delete("1.0", tk.END)
        self.summary_box.insert(tk.END, summary)
        self.summary_box.config(state=tk.DISABLED)
        self.prompt_var.set("Quiz complete!")
        self.feedback_var.set("")
        self.next_btn.state(["disabled"])

    def _render_visual(self, question: Question) -> None:
        visual = question.visual
        if not visual:
            return
        render_quiz_visual(self.visual_canvas, visual)


def _subskill_for_question(question: Question) -> str:
    if getattr(question, "subskill", None):
        return str(question.subskill)
    subskills = subskills_for(question.skill)
    if not subskills:
        return "core"
    seed = f"{question.skill}|{question.prompt}|{question.correct_answer}"
    digest = hashlib.sha1(seed.encode("utf-8")).hexdigest()
    index = int(digest[:10], 16) % len(subskills)
    return subskills[index]
