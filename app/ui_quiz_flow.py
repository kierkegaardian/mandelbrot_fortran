"""Question display and answer flow for a quiz session."""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk

from .quiz_answers import is_correct_answer
from .quiz_engine import Question
from .quiz_visuals import render_quiz_visual


class QuizFlowMixin:
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
        self.recovery_var.set("")
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
        if self._recovery_active():
            self._submit_mistake_recovery()
            return
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
        self._persist_quiz_progress()

        self.submit_btn.state(["disabled"])
        self.stuck_btn.state(["disabled"])
        if not correct and self._should_offer_mistake_recovery(question):
            self._start_mistake_recovery(question, answer)
        else:
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
        if self._advance_after_mistake_recovery():
            return
        if self._index + 1 < len(self._questions):
            self._index += 1
            self._show_question()
            self._persist_quiz_progress()
        else:
            self._finish_quiz()

    def _render_visual(self, question: Question) -> None:
        self.visual_canvas.delete("all")
        visual = question.visual
        if not visual:
            return
        render_quiz_visual(self.visual_canvas, visual)
