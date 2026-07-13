from __future__ import annotations

import random
import time
import tkinter as tk
from typing import TYPE_CHECKING
from tkinter import messagebox, ttk

from . import db, sync_service
from .explanations import ARITHMETIC_MODE_EXPLANATIONS, explanation_for
from .learning_engine import build_skill_stats, recommend_next_skill_paths
from .quiz_answers import is_correct_answer
from .quiz_visuals import render_quiz_visual
from .skill_graph import SKILL_LABELS, SKILL_ORDER, SKILL_PREREQUISITE_WEIGHTS, SUBSKILL_STREAK_TO_MASTER
from .summer_mode import filter_skills
from .theme import COLORS
from .time_utils import now_iso
from .ui_settings import load_ui_settings

if TYPE_CHECKING:
    from .quiz_engine import Question

_CORRECT_MESSAGES = [
    "Great job! \u2705",
    "Nailed it! \u2705",
    "Perfect! \u2705",
    "You got it! \u2705",
    "Correct! \u2705",
    "Nicely done! \u2705",
    "Spot on! \u2705",
]

_WRONG_MESSAGES = [
    "Almost! The answer is {correct}. Keep going!",
    "Not quite \u2014 the answer is {correct}. You\'ll get the next one!",
    "Close! Correct answer: {correct}. Let\'s keep practicing!",
    "The answer is {correct}. Don\'t worry, practice makes progress!",
]


def question_intuition_preview(panel, question: "Question") -> str:
    is_child_profile = getattr(panel, "_is_child_profile", None)
    if not callable(is_child_profile) or not is_child_profile():
        return ""
    subskill_for_question = getattr(panel, "_subskill_for_question", None)
    subskill = subskill_for_question(question) if callable(subskill_for_question) else question.subskill
    explanation = explanation_for(question.skill, subskill=subskill)
    if subskill:
        return f"Practice focus: {subskill}\nThink: {explanation.mental_model}"
    return f"Think: {explanation.mental_model}"


def show_question(panel) -> None:
    if not panel._questions:
        return
    question = panel._questions[panel._index]
    if hasattr(panel, "recovery_var"):
        panel.recovery_var.set("")
    panel.prompt_var.set(f"Question {panel._index + 1}: {question.prompt}")
    template_label = ""
    if question.template_external_id:
        template_label = f" | Template: {question.template_external_id}"
    elif question.template_id is not None:
        template_label = f" | Template #{question.template_id}"
    panel.meta_var.set(f"[{question.question_label}] [{question.mode}] Skill: {question.skill}{template_label}")
    panel.feedback_var.set("")
    panel.intuition_var.set(question_intuition_preview(panel, question))
    panel._set_feedback_state(correct=None)
    build_answer_widget(panel, question)
    render_visual(panel, question)
    panel.next_btn.state(["disabled"])
    panel.submit_btn.state(["!disabled"])
    if question.skill in ARITHMETIC_MODE_EXPLANATIONS:
        panel.stuck_btn.state(["!disabled"])
    else:
        panel.stuck_btn.state(["disabled"])
    panel._persist_quiz_progress()


def build_answer_widget(panel, question) -> None:
    for child in panel.answer_frame.winfo_children():
        child.destroy()
    panel.answer_var.set("")
    panel.choice_var.set("")
    panel.repeat_var.set(False)
    if not question.scaffold_steps:
        getattr(panel, "_clear_scaffold_state", lambda: None)()

    if question.scaffold_steps:
        step = getattr(panel, "_current_scaffold_step", lambda _q: None)(question)
        if step is not None:
            ttk.Label(
                panel.answer_frame,
                text=f"Step {panel._scaffold_step_index + 1} of {len(question.scaffold_steps)}",
                foreground=COLORS["text_muted"],
            ).pack(anchor=tk.W)
            ttk.Label(panel.answer_frame, text=step.prompt, wraplength=760).pack(anchor=tk.W, pady=(4, 2))
            ttk.Label(
                panel.answer_frame,
                text=f"Hint: {step.hint}",
                foreground=COLORS["text_secondary"],
                wraplength=760,
            ).pack(anchor=tk.W, pady=(0, 6))
            entry = ttk.Entry(panel.answer_frame, textvariable=panel.answer_var)
            entry.pack(fill=tk.X)
            entry.focus_set()
            entry.bind("<Return>", lambda _e: panel._submit_or_next_shortcut())
            return

    if question.choices:
        hint_text = "Press 1\u20134 to choose, Enter to submit" if len(question.choices) <= 4 else "Choose one:"
        ttk.Label(panel.answer_frame, text=hint_text, foreground=COLORS["text_muted"]).pack(anchor=tk.W)
        first_radio = None
        for idx, choice in enumerate(question.choices):
            key_label = f"({idx + 1}) " if idx < 9 else ""
            radio = ttk.Radiobutton(
                panel.answer_frame, text=f"{key_label}{choice}",
                variable=panel.choice_var, value=choice,
            )
            radio.pack(anchor=tk.W)
            if first_radio is None:
                first_radio = radio
            # UX15: bind number keys to select choices
            if idx < 9:
                _bind_choice_key(panel, idx + 1, choice)
        if first_radio is not None:
            first_radio.focus_set()
        return

    ttk.Label(panel.answer_frame, text="Type your answer:").pack(anchor=tk.W)
    entry = ttk.Entry(panel.answer_frame, textvariable=panel.answer_var)
    entry.pack(fill=tk.X)
    entry.focus_set()
    entry.bind("<Return>", lambda _e: panel._submit_or_next_shortcut())
    if question.skill == "fractions" or (question.visual and question.visual.get("kind") == "fraction"):
        hint = ttk.Frame(panel.answer_frame)
        hint.pack(anchor=tk.W, pady=(6, 0))
        repeat_toggle = ttk.Checkbutton(hint, text="Repeating", variable=panel.repeat_var)
        repeat_toggle.pack(side=tk.LEFT)
        ttk.Label(
            hint,
            text="(parentheses wrap repeating digits: 0.1(6); checkbox repeats entire decimal part)",
        ).pack(side=tk.LEFT, padx=(6, 0))
        repeat_help = ttk.Label(hint, text="Example: 0.12 + repeating = 0.121212…", foreground=COLORS["text_secondary"])

        def _toggle_repeat_help() -> None:
            if panel.repeat_var.get():
                repeat_help.pack(side=tk.LEFT, padx=(8, 0))
            else:
                repeat_help.pack_forget()

        repeat_toggle.configure(command=_toggle_repeat_help)
        _toggle_repeat_help()


def submit_answer(panel) -> None:
    if getattr(panel, "_recovery_active", lambda: False)():
        panel._submit_mistake_recovery()
        return
    if not panel._questions:
        return
    question = panel._questions[panel._index]
    if question.scaffold_steps:
        step = panel._current_scaffold_step(question)
        answer = panel.answer_var.get().strip()
        if step is None:
            panel._clear_scaffold_state()
        else:
            if not answer:
                messagebox.showerror("Missing answer", "Please enter an answer for this step.")
                return
            if not is_correct_answer(step.expected_answer, answer, panel.repeat_var.get()):
                panel.feedback_var.set(step.hint)
                panel._set_feedback_state(correct=False)
                panel._persist_quiz_progress()
                return
            panel._scaffold_step_answers.append(answer)
            if panel._scaffold_step_index + 1 < len(question.scaffold_steps):
                panel._scaffold_step_index += 1
                panel.feedback_var.set("Nice. Keep going.")
                panel._set_feedback_state(correct=True)
                build_answer_widget(panel, question)
                panel._persist_quiz_progress()
                return
            recorded_answer = " | ".join(panel._scaffold_step_answers)
            panel._clear_scaffold_state()
            panel._score += 1
            panel.feedback_var.set("Nice work. You finished the steps.")
            panel._set_feedback_state(correct=True)
            panel._play_correct_animation()
            panel._record_streak(correct=True)
            panel._answers.append((question, recorded_answer, True))
            panel._persist_quiz_progress()
            panel.submit_btn.state(["disabled"])
            panel.stuck_btn.state(["disabled"])
            panel.next_btn.state(["!disabled"])
            return
    answer = panel.choice_var.get().strip() if question.choices else panel.answer_var.get().strip()
    if not answer:
        messagebox.showerror("Missing answer", "Please enter or choose an answer.")
        return

    if not question.correct_answer:
        correct = False
        panel.feedback_var.set("Answer recorded. This historical item has no answer key loaded.")
    else:
        correct = is_correct_answer(question.correct_answer, answer, panel.repeat_var.get())
        if correct:
            panel._score += 1
            panel.feedback_var.set(random.choice(_CORRECT_MESSAGES))
            panel._set_feedback_state(correct=True)
            panel._play_correct_animation()
        else:
            if panel._should_offer_mistake_recovery(question):
                panel.feedback_var.set("Let's fix this one together.")
            else:
                msg = random.choice(_WRONG_MESSAGES).format(correct=question.correct_answer)
                panel.feedback_var.set(msg)
            panel._set_feedback_state(correct=False)
    panel._record_streak(correct=correct)
    panel._answers.append((question, answer, correct))
    panel._persist_quiz_progress()

    # UX15: unbind number keys after submission
    _unbind_choice_keys(panel)
    if not correct and panel._should_offer_mistake_recovery(question):
        panel._start_mistake_recovery(question, answer)
        return

    panel.submit_btn.state(["disabled"])
    panel.stuck_btn.state(["disabled"])
    panel.next_btn.state(["!disabled"])


def show_intuition(panel) -> None:
    if getattr(panel, "_recovery_active", lambda: False)():
        question = panel._current_recovery_question()
        if question is None:
            return
    elif not panel._questions:
        return
    else:
        question = panel._questions[panel._index]
    subskill = panel._subskill_for_question(question)
    explanation = explanation_for(question.skill, subskill=subskill)
    lines: list[str] = []
    if subskill:
        lines.append(f"Subskill: {subskill}")
    lines.append(f"Mental model: {explanation.mental_model}")
    lines.append(f"Common mistake: {explanation.common_mistake}")
    lines.append(f"Try this: {explanation.try_this}")
    panel.intuition_var.set("\n".join(lines))


def next_question(panel) -> None:
    if getattr(panel, "_advance_after_mistake_recovery", lambda: False)():
        return
    if panel._index + 1 < len(panel._questions):
        panel._index += 1
        show_question(panel)
    else:
        finish_quiz(panel)


def finish_quiz(panel) -> None:
    profile_getter = getattr(panel, "_active_profile", panel._profile_getter)
    profile = profile_getter()
    if profile is None:
        return
    if hasattr(panel, "recovery_var"):
        panel.recovery_var.set("")
    settings = load_ui_settings()
    summer_mode = settings.summer_mode
    if not panel._record_attempt:
        panel.prompt_var.set("Practice complete.")
        panel.feedback_var.set("")
        panel.next_btn.state(["disabled"])
        getattr(panel, "_clear_scaffold_state", lambda: None)()
        panel._clear_quiz_progress()
        if hasattr(panel, "_profile_override"):
            panel._profile_override = None
        if hasattr(panel, "_summer_program_launch"):
            panel._summer_program_launch = None
        return

    completed_at = now_iso()
    elapsed_seconds = None
    if panel._quiz_started_monotonic is not None:
        elapsed_seconds = max(0.0, time.monotonic() - panel._quiz_started_monotonic)
    write_result = sync_service.record_completed_quiz(
        profile_id=profile.id,
        quiz_set_id=None,
        skill=panel._attempt_skill or panel.skill_var.get(),
        question_type=panel.type_var.get(),
        num_questions=len(panel._questions),
        level=panel.level_var.get(),
        score=panel._score,
        created_at=completed_at,
        elapsed_seconds=elapsed_seconds,
        question_results=[
            sync_service.QuestionResultInput(
                skill=question.skill,
                subskill=panel._subskill_for_question(question),
                question_label=question.question_label,
                mode=question.mode,
                prompt=question.prompt,
                correct_answer=question.correct_answer,
                user_answer=answer,
                is_correct=correct,
                explanation=question.explanation,
            )
            for question, answer, correct in panel._answers
        ],
        record_progress=panel._record_progress,
        streak_to_master=SUBSKILL_STREAK_TO_MASTER,
        record_daily_review=panel._launch_context == "daily_review",
        summer_program_task_id=(
            getattr(getattr(panel, "_summer_program_launch", None), "task_id", None)
        ),
    )
    completed_assignments = write_result.completed_assignments

    keyed_total = sum(1 for q, _a, _c in panel._answers if q.correct_answer)
    retake_required = (
        (not summer_mode)
        and panel._attempt_skill != "historical_practice"
        and panel._score < len(panel._questions)
    )
    visible_skills = tuple(
        filter_skills(
            tuple(SKILL_ORDER),
            grade_band=settings.default_grade_band,
            summer_mode=summer_mode,
        )
    ) or tuple(SKILL_ORDER)

    branch_recommendations = recommend_next_skill_paths(
        visible_skills,
        SKILL_PREREQUISITE_WEIGHTS,
        build_skill_stats(sync_service.list_attempts(profile.id), visible_skills),
        subskill_coverage=panel._subskill_coverage_by_skill(profile.id),
        limit=3,
    )

    mistakes = []
    for question, answer, correct in panel._answers:
        if not correct:
            mistakes.append((question.prompt, answer, question.explanation))

    panel._show_quiz_summary(
        score=panel._score,
        total=len(panel._questions),
        keyed_total=keyed_total,
        retake_required=retake_required,
        assignments=completed_assignments,
        recommendations=branch_recommendations,
        mistakes=mistakes,
        elapsed_seconds=elapsed_seconds,
        summer_program_note=write_result.summer_program_note,
    )

    if panel._attempt_skill == "historical_practice":
        panel.prompt_var.set("Historical practice complete.")
    elif summer_mode:
        if panel._score == len(panel._questions):
            panel.prompt_var.set("Quiz complete. Nice work.")
        else:
            panel.prompt_var.set("Quiz complete. Keep practicing to get stronger.")
    elif panel._score == len(panel._questions):
        panel.prompt_var.set("Quiz complete (100%)!")
    else:
        panel.prompt_var.set("Quiz complete (retake needed for mastery).")

    panel.feedback_var.set("")
    panel.next_btn.state(["disabled"])
    panel._launch_context = "manual"
    panel._quiz_started_monotonic = None
    panel._attempt_skill = None
    getattr(panel, "_clear_scaffold_state", lambda: None)()
    if hasattr(panel, "_profile_override"):
        panel._profile_override = None
    if hasattr(panel, "_summer_program_launch"):
        panel._summer_program_launch = None
    panel._clear_quiz_progress()


def render_visual(panel, question) -> None:
    visual = question.visual
    if not visual:
        return
    render_quiz_visual(panel.visual_canvas, visual)


def _bind_choice_key(panel, number: int, value: str) -> None:
    """Bind a number key (1-9) to select a multiple-choice answer."""
    def _handler(_event, v=value):
        panel.choice_var.set(v)
        return "break"
    panel.view_frame.bind_all(f"<Key-{number}>", _handler)


def _unbind_choice_keys(panel) -> None:
    """Remove number key bindings after answer submission."""
    for i in range(1, 10):
        try:
            panel.view_frame.unbind_all(f"<Key-{i}>")
        except Exception:
            pass
