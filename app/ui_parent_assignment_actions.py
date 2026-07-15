"""Parent grades and assignments actions."""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox

from . import sync_service
from .skill_graph import SKILL_LABELS, subskills_for
from .time_utils import now_iso


class ParentAssignmentActionsMixin:
    def _refresh_profiles_for_grades(self) -> None:
        if not hasattr(self, "profile_combo"):
            return
        profiles = sync_service.list_profiles()
        labels = [p.name for p in profiles]
        self._profile_map = {p.name: p for p in profiles}
        self.profile_combo.configure(values=labels)

    def _refresh_profiles_for_assignments(self) -> None:
        if not hasattr(self, "assignment_profile_combo"):
            return
        profiles = [p for p in sync_service.list_profiles() if p.role == "child"]
        labels = [p.name for p in profiles]
        self._assignment_profile_map = {p.name: p for p in profiles}
        self.assignment_profile_combo.configure(values=labels)
        if labels and self.assignment_profile.get() not in self._assignment_profile_map:
            self.assignment_profile.set(labels[0])
        self._refresh_assignments()

    def _refresh_assignment_subskills(self) -> None:
        skill = self.assignment_skill.get()
        options = ["Any", *subskills_for(skill)]
        if self.assignment_subskill.get() not in options:
            self.assignment_subskill.set("Any")
        self.assignment_subskill_combo.configure(values=options)

    def _create_assignment(self) -> None:
        profile = self._assignment_profile_map.get(self.assignment_profile.get())
        if profile is None:
            messagebox.showerror("Missing student", "Choose a student profile first.")
            return
        target_type = self.assignment_target_type.get().strip()
        target_value = float(self.assignment_target_value.get())
        subskill = None if self.assignment_subskill.get() == "Any" else self.assignment_subskill.get()
        if target_type == "subskill_mastered" and not subskill:
            messagebox.showerror("Missing subskill", "Subskill-mastered assignments require a subskill.")
            return
        mode_mix = _mode_mix_or_none(
            self.assignment_mode_override.get(),
            self.assignment_mode_intuition.get(),
            self.assignment_mode_expression.get(),
            self.assignment_mode_word.get(),
        )
        sync_service.create_assignment(
            profile_id=profile.id,
            skill=self.assignment_skill.get().strip(),
            subskill=subskill,
            target_type=target_type,
            target_value=target_value,
            level=int(self.assignment_level.get()),
            num_questions=int(self.assignment_questions.get()),
            question_type=self.assignment_question_type.get().strip(),
            mode_intuition_pct=mode_mix[0],
            mode_expression_pct=mode_mix[1],
            mode_word_pct=mode_mix[2],
            notes=self.assignment_notes.get().strip(),
            created_at=now_iso(),
        )
        self.assignment_notes.delete(0, tk.END)
        self._refresh_assignments()

    def _refresh_assignments(self) -> None:
        if not hasattr(self, "assignments_active_list"):
            return
        self.assignments_active_list.delete(0, tk.END)
        self.assignments_done_list.delete(0, tk.END)
        profile = self._assignment_profile_map.get(self.assignment_profile.get())
        if profile is None:
            self.assignment_analytics_var.set("Assignments analytics: —")
            return
        skill_filter = None if self.assignment_filter_skill.get() == "All" else self.assignment_filter_skill.get()
        target_filter = None if self.assignment_filter_target.get() == "All" else self.assignment_filter_target.get()
        done_limit = int(self.assignment_done_limit.get())
        self._active_assignments = sync_service.list_assignments(
            profile.id,
            active_only=True,
            skill=skill_filter,
            target_type=target_filter,
        )
        self._done_assignments = sync_service.list_assignments(
            profile.id,
            active_only=False,
            skill=skill_filter,
            target_type=target_filter,
            limit=done_limit,
        )
        for a in self._active_assignments:
            self.assignments_active_list.insert(tk.END, _assignment_label(a))
        for a in self._done_assignments:
            self.assignments_done_list.insert(tk.END, _assignment_label(a))
        analytics = sync_service.assignment_completion_analytics(
            profile.id, recent_days=int(self.assignment_recent_days.get())
        )
        avg_hours = analytics.get("avg_completion_hours")
        avg_text = "n/a" if avg_hours is None else f"{(float(avg_hours) / 24.0):.1f}d avg complete"
        top = analytics.get("top_completed_skills", [])
        if top:
            top_text = ", ".join(f"{SKILL_LABELS.get(skill, skill)} ({count})" for skill, count in top)
        else:
            top_text = "none yet"
        self.assignment_analytics_var.set(
            "Assignments analytics: "
            f"active {analytics.get('active_count', 0)} | "
            f"completed {analytics.get('completed_count', 0)} | "
            f"completed {analytics.get('completed_recent_count', 0)} in {int(self.assignment_recent_days.get())}d | "
            f"{avg_text} | top: {top_text}"
        )

    def _complete_assignment(self) -> None:
        profile = self._assignment_profile_map.get(self.assignment_profile.get())
        if profile is None:
            return
        sel = self.assignments_active_list.curselection()
        if not sel:
            messagebox.showerror("Select assignment", "Choose an active assignment to complete.")
            return
        assignment = self._active_assignments[sel[0]]
        sync_service.complete_assignment(assignment.id, now_iso())
        self._refresh_assignments()

    def _refresh_grades(self) -> None:
        name = self.grades_profile.get()
        profile = self._profile_map.get(name)
        if profile is None:
            return
        attempts = sync_service.list_attempts(profile.id)
        self.grades_list.delete(0, tk.END)
        for attempt in attempts:
            self.grades_list.insert(
                tk.END, f"{attempt.created_at[:10]} | {attempt.skill} | {attempt.score}/{attempt.num_questions}"
            )


def _assignment_label(assignment) -> str:
    skill = SKILL_LABELS.get(assignment.skill, assignment.skill)
    target = assignment.target_type
    if target == "quiz_score_pct":
        target_text = "score = 100%"
    elif target == "subskill_mastered":
        target_text = "master subskill"
    else:
        target_text = target
    sub = f" [{assignment.subskill}]" if assignment.subskill else ""
    mix = ""
    if (
        assignment.mode_intuition_pct is not None
        and assignment.mode_expression_pct is not None
        and assignment.mode_word_pct is not None
    ):
        mix = f" | I/E/W {assignment.mode_intuition_pct}/{assignment.mode_expression_pct}/{assignment.mode_word_pct}"
    done = f" (done {assignment.completed_at[:10]})" if assignment.completed_at else ""
    return f"#{assignment.id} {skill}{sub} | {target_text}{mix}{done}"
