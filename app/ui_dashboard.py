from __future__ import annotations

from datetime import datetime, timezone
import tkinter as tk
from tkinter import ttk

from . import db
from .skill_graph import (
    SKILL_LABELS,
    SKILL_ORDER,
    SUBSKILL_STREAK_TO_MASTER,
    recommend_next_skills,
    subskills_for,
)


class DashboardPanel:
    def __init__(
        self,
        controls_parent: tk.Widget,
        view_parent: tk.Widget,
        profile_getter,
        quiz_launcher=None,
        assignment_launcher=None,
    ) -> None:
        self.controls_frame = ttk.Frame(controls_parent)
        self.view_frame = ttk.Frame(view_parent)
        self._profile_getter = profile_getter
        self._quiz_launcher = quiz_launcher
        self._assignment_launcher = assignment_launcher
        self._daily_target: tuple[str, str] | None = None
        self._assignment_target = None

        self._build_controls()
        self._build_view()

    def _build_controls(self) -> None:
        frame = ttk.Frame(self.controls_frame, padding=10)
        frame.pack(fill=tk.BOTH, expand=True)
        ttk.Label(frame, text="Student Dashboard", font=("Helvetica", 12, "bold")).pack(anchor=tk.W, pady=(0, 6))
        ttk.Label(
            frame,
            text="See progress, mastery level, and suggested next skills.",
            wraplength=260,
        ).pack(anchor=tk.W, pady=(0, 8))
        ttk.Button(frame, text="Refresh", command=self.render).pack(anchor=tk.W)
        self.daily_btn = ttk.Button(frame, text="Start Daily Review", command=self._start_daily_review)
        self.daily_btn.pack(anchor=tk.W, pady=(8, 0))
        self.assignment_btn = ttk.Button(frame, text="Start Assignment", command=self._start_assignment)
        self.assignment_btn.pack(anchor=tk.W, pady=(8, 0))

    def _build_view(self) -> None:
        header = ttk.Frame(self.view_frame)
        header.pack(fill=tk.X, pady=(10, 6))
        self.summary_var = tk.StringVar(value="No data yet.")
        ttk.Label(header, textvariable=self.summary_var, font=("Helvetica", 12, "bold")).pack(anchor=tk.W, padx=10)

        self.tiles_frame = ttk.Frame(self.view_frame)
        self.tiles_frame.pack(fill=tk.X, padx=10, pady=(0, 6))
        self.tile_vars: dict[str, tk.StringVar] = {}
        tile_specs = [
            ("Not started", "#dfe3e8"),
            ("Needs work", "#f3d4d4"),
            ("Developing", "#f2e3b6"),
            ("Proficient", "#c7e3f2"),
            ("Mastered", "#cbe8d1"),
        ]
        for label, color in tile_specs:
            tile = tk.Frame(self.tiles_frame, bg=color, bd=1, relief=tk.RIDGE)
            tile.pack(side=tk.LEFT, padx=4, pady=2, ipadx=6, ipady=4)
            var = tk.StringVar(value=f"{label}: 0")
            tk.Label(tile, textvariable=var, bg=color, fg="#2a2a2a", font=("Helvetica", 9, "bold")).pack()
            self.tile_vars[label] = var

        self.progress_frame = ttk.Frame(self.view_frame)
        self.progress_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=4)
        self.progress_rows: dict[str, dict[str, object]] = {}
        for skill in SKILL_ORDER:
            row = ttk.Frame(self.progress_frame)
            row.pack(fill=tk.X, pady=2)
            ttk.Label(row, text=SKILL_LABELS.get(skill, skill), width=18).pack(side=tk.LEFT)
            progress_var = tk.DoubleVar(value=0)
            bar = ttk.Progressbar(row, variable=progress_var, maximum=100)
            bar.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=6)
            percent_var = tk.StringVar(value="0%")
            ttk.Label(row, textvariable=percent_var, width=6).pack(side=tk.LEFT)
            mastery_var = tk.StringVar(value="Not started")
            ttk.Label(row, textvariable=mastery_var, width=12).pack(side=tk.LEFT, padx=(6, 0))
            self.progress_rows[skill] = {
                "progress_var": progress_var,
                "percent_var": percent_var,
                "mastery_var": mastery_var,
            }

        self.reco_var = tk.StringVar(value="Recommended next: —")
        ttk.Label(self.view_frame, textvariable=self.reco_var, foreground="#2d5d7c").pack(
            anchor=tk.W, padx=10, pady=(6, 10)
        )
        self.subskill_var = tk.StringVar(value="")
        ttk.Label(self.view_frame, textvariable=self.subskill_var, foreground="#4f6b7a", wraplength=520).pack(
            anchor=tk.W, padx=10, pady=(0, 10)
        )
        self.daily_var = tk.StringVar(value="Daily review: —")
        ttk.Label(self.view_frame, textvariable=self.daily_var, foreground="#2f6f3e", wraplength=520).pack(
            anchor=tk.W, padx=10, pady=(0, 10)
        )
        self.assignment_var = tk.StringVar(value="Assignment: —")
        ttk.Label(self.view_frame, textvariable=self.assignment_var, foreground="#7a4f2e", wraplength=520).pack(
            anchor=tk.W, padx=10, pady=(0, 10)
        )

    def _start_daily_review(self) -> None:
        if self._quiz_launcher is None or self._daily_target is None:
            return
        skill, subskill = self._daily_target
        self._quiz_launcher(skill, subskill)

    def _start_assignment(self) -> None:
        if self._assignment_launcher is None or self._assignment_target is None:
            return
        self._assignment_launcher(
            self._assignment_target.skill,
            self._assignment_target.subskill,
            self._assignment_target.level,
            self._assignment_target.num_questions,
            self._assignment_target.question_type,
        )

    def render(self) -> None:
        profile = self._profile_getter()
        if profile is None:
            self.summary_var.set("No profile selected.")
            self.reco_var.set("Recommended next: —")
            self.daily_var.set("Daily review: —")
            self.assignment_var.set("Assignment: —")
            for skill, row in self.progress_rows.items():
                row["progress_var"].set(0)
                row["percent_var"].set("0%")
                row["mastery_var"].set("Not started")
            for label, var in self.tile_vars.items():
                var.set(f"{label}: 0")
            self.daily_btn.state(["disabled"])
            self.assignment_btn.state(["disabled"])
            return
        attempts = db.list_attempts(profile.id)
        stats = {skill: {"score": 0, "total": 0, "attempts": 0} for skill in SKILL_ORDER}
        for attempt in attempts:
            skill = attempt.skill
            if skill not in stats:
                stats[skill] = {"score": 0, "total": 0, "attempts": 0}
            stats[skill]["score"] += attempt.score
            stats[skill]["total"] += attempt.num_questions
            stats[skill]["attempts"] += 1

        mastery_map: dict[str, str] = {}
        counts = {label: 0 for label in self.tile_vars}
        for skill in SKILL_ORDER:
            data = stats.get(skill, {"score": 0, "total": 0, "attempts": 0})
            attempts_count = data["attempts"]
            total = data["total"]
            avg = (data["score"] / total * 100) if total else 0
            mastery = _mastery_label(attempts_count, avg)
            mastery_map[skill] = mastery
            if mastery in counts:
                counts[mastery] += 1
            row = self.progress_rows.get(skill)
            if row:
                row["progress_var"].set(avg)
                row["percent_var"].set(f"{avg:.0f}%")
                row["mastery_var"].set(mastery)

        for label, var in self.tile_vars.items():
            var.set(f"{label}: {counts.get(label, 0)}")

        completed = sum(1 for s in SKILL_ORDER if mastery_map.get(s) == "Mastered")
        self.summary_var.set(f"{profile.name}: {completed}/{len(SKILL_ORDER)} skills mastered")
        recommendations = recommend_next_skills(mastery_map)
        if recommendations:
            labels = [SKILL_LABELS.get(skill, skill) for skill in recommendations]
            self.reco_var.set(f"Recommended next: {', '.join(labels)}")
            top_recommendation = recommendations[0]
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
                self.subskill_var.set("Subskills to build: " + " • ".join(subskill_status))
            else:
                self.subskill_var.set("")
        else:
            self.reco_var.set("Recommended next: Mixed review")
            self.subskill_var.set("")

        self._render_daily_review(profile.id, mastery_map, stats, recommendations)
        self._render_assignment(profile.id)

    def _render_daily_review(
        self, profile_id: int, mastery_map: dict[str, str], stats: dict[str, dict], recommendations: list[str]
    ) -> None:
        now = datetime.now(timezone.utc)
        started = {skill for skill in SKILL_ORDER if int(stats.get(skill, {}).get("attempts", 0)) > 0}
        solid = {skill for skill in SKILL_ORDER if mastery_map.get(skill) in {"Proficient", "Mastered"}}
        candidate_skills = started | solid | set(recommendations)
        if not candidate_skills:
            candidate_skills = {"counting"}

        progress = {
            (item.skill, item.subskill): item for item in db.list_subskill_progress(profile_id)
        }

        due: list[tuple[int, int, str, str, str]] = []
        # tuple: (priority, age_days, skill, subskill, status_text)
        for skill in SKILL_ORDER:
            if skill not in candidate_skills:
                continue
            for subskill in subskills_for(skill):
                item = progress.get((skill, subskill))
                if item is None:
                    due.append((0, 9999, skill, subskill, "new"))
                    continue
                try:
                    updated = datetime.fromisoformat(item.updated_at)
                except ValueError:
                    continue
                age_days = int((now - updated).total_seconds() // 86400)
                if item.mastered and age_days >= 30:
                    due.append((1, age_days, skill, subskill, f"{age_days}d ago"))
                elif (not item.mastered) and age_days >= 7:
                    due.append((2, age_days, skill, subskill, f"{age_days}d ago"))

        if not due:
            self._daily_target = None
            self.daily_var.set("Daily review: all caught up")
            self.daily_btn.state(["disabled"])
            return

        due.sort(key=lambda t: (t[0], -t[1], SKILL_ORDER.index(t[2])))
        _priority, _age, skill, subskill, status = due[0]
        self._daily_target = (skill, subskill)
        self.daily_var.set(f"Daily review: {SKILL_LABELS.get(skill, skill)} – {subskill} ({status})")
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
            target_text = f"score >= {assignment.target_value:.0f}%"
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


def _streak_graph(current: int, target: int) -> str:
    blocks = min(max(current, 0), target)
    return ("🔥" * blocks) + ("⬜" * (target - blocks))


def _mastery_label(attempts: int, avg: float) -> str:
    if attempts == 0:
        return "Not started"
    if avg >= 90:
        return "Mastered"
    if avg >= 75:
        return "Proficient"
    if avg >= 60:
        return "Developing"
    return "Needs work"
