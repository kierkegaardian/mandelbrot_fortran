from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from . import db
from .learning_engine import build_skill_stats, frontier_skills, recommend_next_skill_paths
from .skill_graph import (
    SKILL_LABELS,
    SKILL_ORDER,
    SKILL_PREREQUISITE_EDGES,
    SKILL_PREREQUISITE_WEIGHTS,
    SKILL_TRACK_ORDER,
    skills_in_track,
    subskills_for,
)


class SkillMapPanel:
    def __init__(self, controls_parent: tk.Widget, view_parent: tk.Widget, profile_getter, quiz_launcher=None) -> None:
        self.controls_frame = ttk.Frame(controls_parent)
        self.view_frame = ttk.Frame(view_parent)
        self._profile_getter = profile_getter
        self._quiz_launcher = quiz_launcher
        self._selected_skill = "counting"
        self._node_items: dict[int, str] = {}

        self._build_controls()
        self._build_view()

    def _build_controls(self) -> None:
        frame = ttk.Frame(self.controls_frame, padding=10)
        frame.pack(fill=tk.BOTH, expand=True)
        ttk.Label(frame, text="Skill Map", font=("Helvetica", 12, "bold")).pack(anchor=tk.W, pady=(0, 6))
        ttk.Label(
            frame,
            text="Node-based progression with branching paths. Select a node to view why it is recommended.",
            wraplength=280,
        ).pack(anchor=tk.W, pady=(0, 8))
        ttk.Button(frame, text="Refresh Map", command=self.render).pack(anchor=tk.W)
        self.start_btn = ttk.Button(frame, text="Start Node Quiz", command=self._start_selected_skill_quiz)
        self.start_btn.pack(anchor=tk.W, pady=(8, 0))

        ttk.Separator(frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)
        self.selected_var = tk.StringVar(value="Selected node: —")
        ttk.Label(frame, textvariable=self.selected_var, foreground="#2d5d7c", wraplength=280).pack(anchor=tk.W)
        self.reason_var = tk.StringVar(value="")
        ttk.Label(frame, textvariable=self.reason_var, foreground="#4f6b7a", wraplength=280).pack(anchor=tk.W, pady=(4, 0))

        ttk.Separator(frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)
        self.legend_var = tk.StringVar(
            value="Legend: Green=Mastered | Blue=Frontier | Yellow=In progress | Gray=Locked"
        )
        ttk.Label(frame, textvariable=self.legend_var, foreground="#4f6b7a", wraplength=280).pack(anchor=tk.W)

    def _build_view(self) -> None:
        container = ttk.Frame(self.view_frame)
        container.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        self.canvas = tk.Canvas(container, bg="#f8fbfd", highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.canvas.bind("<Button-1>", self._on_canvas_click)

    def render(self) -> None:
        profile = self._profile_getter()
        if profile is None:
            self.canvas.delete("all")
            self.canvas.create_text(20, 20, text="No profile selected.", anchor=tk.NW, fill="#6b6b6b", font=("Helvetica", 11))
            self.start_btn.state(["disabled"])
            self.selected_var.set("Selected node: —")
            self.reason_var.set("")
            return

        attempts = db.list_attempts(profile.id)
        stats = build_skill_stats(attempts, tuple(SKILL_ORDER))
        coverage = _subskill_coverage_by_skill(profile.id)
        frontier = set(frontier_skills(tuple(SKILL_ORDER), SKILL_PREREQUISITE_WEIGHTS, stats, coverage))
        recommendations = recommend_next_skill_paths(
            tuple(SKILL_ORDER),
            SKILL_PREREQUISITE_WEIGHTS,
            stats,
            subskill_coverage=coverage,
            limit=3,
        )
        reason_by_skill = {item.skill: item.reasons[0] if item.reasons else "Strong next step." for item in recommendations}

        self._draw_map(stats, frontier)

        if self._selected_skill not in SKILL_ORDER:
            self._selected_skill = SKILL_ORDER[0]
        self._update_selected_text(stats, reason_by_skill)
        if self._quiz_launcher is None:
            self.start_btn.state(["disabled"])
        else:
            self.start_btn.state(["!disabled"])

    def _draw_map(self, stats, frontier: set[str]) -> None:
        self.canvas.delete("all")
        self._node_items.clear()
        self.canvas.update_idletasks()
        width = max(640, self.canvas.winfo_width())
        y_gap = 76
        track_gap = 84
        left = 20
        right = width - 20
        row_width = max(120, right - left)

        positions: dict[str, tuple[int, int]] = {}
        max_rows = 0
        for track in SKILL_TRACK_ORDER:
            skills = skills_in_track(track)
            if not skills:
                continue
            max_rows = max(max_rows, len(skills))
        for col_idx, track in enumerate(SKILL_TRACK_ORDER):
            skills = skills_in_track(track)
            if not skills:
                continue
            x = int(left + ((col_idx + 0.5) * (row_width / float(max(1, len(SKILL_TRACK_ORDER))))))
            self.canvas.create_text(x, 18, text=track, fill="#3a4f63", font=("Helvetica", 9, "bold"))
            for row_idx, skill in enumerate(skills):
                y = 42 + (row_idx * y_gap)
                positions[skill] = (x, y)

        for target, edges in SKILL_PREREQUISITE_EDGES.items():
            if target not in positions:
                continue
            tx, ty = positions[target]
            for source, _kind, _weight in edges:
                if source not in positions:
                    continue
                sx, sy = positions[source]
                self.canvas.create_line(sx, sy + 12, tx, ty - 12, fill="#d2d9de", width=1)

        for skill in SKILL_ORDER:
            if skill not in positions:
                continue
            x, y = positions[skill]
            state = _node_state(skill, stats, frontier)
            fill = _node_fill(state)
            outline = "#1d4f73" if skill == self._selected_skill else "#a7b6c2"
            rect_id = self.canvas.create_rectangle(x - 52, y - 18, x + 52, y + 18, fill=fill, outline=outline, width=2)
            label = SKILL_LABELS.get(skill, skill)
            text_id = self.canvas.create_text(x, y, text=label, fill="#22313f", font=("Helvetica", 8, "bold"), width=96)
            self._node_items[rect_id] = skill
            self._node_items[text_id] = skill

        height = 70 + (max_rows * y_gap)
        self.canvas.config(scrollregion=(0, 0, width, height))

    def _on_canvas_click(self, event) -> None:
        item_id = self.canvas.find_closest(event.x, event.y)
        if not item_id:
            return
        skill = self._node_items.get(int(item_id[0]))
        if skill is None:
            return
        self._selected_skill = skill
        self.render()

    def _update_selected_text(self, stats, reason_by_skill: dict[str, str]) -> None:
        label = SKILL_LABELS.get(self._selected_skill, self._selected_skill)
        item = stats.get(self._selected_skill)
        mastery = item.mastery if item is not None else "Not started"
        self.selected_var.set(f"Selected node: {label} ({mastery})")
        self.reason_var.set(reason_by_skill.get(self._selected_skill, "Tip: complete this node to unlock new branches."))

    def _start_selected_skill_quiz(self) -> None:
        if self._quiz_launcher is None:
            return
        self._quiz_launcher(self._selected_skill)


def _node_state(skill: str, stats, frontier: set[str]) -> str:
    item = stats.get(skill)
    mastery = item.mastery if item is not None else "Not started"
    if mastery == "Mastered":
        return "mastered"
    if skill in frontier:
        return "frontier"
    if item is not None and item.attempts > 0:
        return "in_progress"
    return "locked"


def _node_fill(state: str) -> str:
    if state == "mastered":
        return "#cfe9d6"
    if state == "frontier":
        return "#c9def2"
    if state == "in_progress":
        return "#f4e7bc"
    return "#e3e8ee"


def _subskill_coverage_by_skill(profile_id: int) -> dict[str, float]:
    coverage: dict[str, float] = {}
    for skill in SKILL_ORDER:
        subskills = _safe_subskills(skill)
        if not subskills:
            coverage[skill] = 1.0
            continue
        progress = {item.subskill: item for item in db.list_subskill_progress(profile_id, skill)}
        mastered = 0
        for subskill in subskills:
            item = progress.get(subskill)
            if item is not None and item.mastered:
                mastered += 1
        coverage[skill] = float(mastered) / float(len(subskills))
    return coverage


def _safe_subskills(skill: str) -> tuple[str, ...]:
    return subskills_for(skill)
