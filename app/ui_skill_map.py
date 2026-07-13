from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from . import db
from .curriculum import BY_SKILL as CURRICULUM_BY_SKILL
from .learning_engine import SkillStats, build_skill_stats, frontier_skills, recommend_next_skill_paths
from .skill_graph import (
    PREREQ_HELPFUL,
    SKILL_LABELS,
    SKILL_ORDER,
    SKILL_PREREQUISITE_EDGES,
    SKILL_PREREQUISITE_WEIGHTS,
    SKILL_TRACK_ORDER,
    skills_in_track,
    subskills_for,
)
from .theme import COLORS, FONTS

EDGE_BASE = COLORS["border_soft"]
EDGE_PREREQ = "#7a4ea3"
EDGE_UNLOCK = "#2f8f7b"
EDGE_ANCESTOR = "#b089c9"
EDGE_DESCENDANT = "#6eb5a7"

ADVANCED_TRACKS: frozenset[str] = frozenset({
    "Algebra 2 / Trig",
    "Calculus",
    "Test Prep",
})

GRADE_OPTIONS: tuple[str, ...] = (
    "All", "K", "1", "2", "3", "4", "5", "6", "7", "8", "9",
)


def _grade_band_contains(grade_band: str, grade: str) -> bool:
    """Return True if *grade* falls inside a grade_band like 'K-2' or '6-9'."""
    if not grade_band:
        return False
    parts = [p.strip() for p in grade_band.split("-")]
    if len(parts) == 1:
        return parts[0] == grade
    lo, hi = parts[0], parts[1]
    order = list(GRADE_OPTIONS[1:])  # K,1,2,...,9
    try:
        lo_idx = order.index(lo)
        hi_idx = order.index(hi)
        gr_idx = order.index(grade)
    except ValueError:
        return False
    return lo_idx <= gr_idx <= hi_idx


class SkillMapPanel:
    def __init__(self, controls_parent: tk.Widget, view_parent: tk.Widget, profile_getter, quiz_launcher=None) -> None:
        self.controls_frame = ttk.Frame(controls_parent)
        self.view_frame = ttk.Frame(view_parent)
        self._profile_getter = profile_getter
        self._quiz_launcher = quiz_launcher
        self._selected_skill = "counting"
        self._node_items: dict[int, str] = {}
        self._profile_id: int | None = None
        self._stats_by_skill: dict[str, SkillStats] = {}
        self._reason_by_skill: dict[str, str] = {}
        self._frontier: set[str] = set()
        self._coverage: dict[str, float] = {}
        self._dependents: dict[str, tuple[str, ...]] = {}
        self._progress_by_skill: dict[str, dict[str, object]] = {}

        self._build_controls()
        self._build_view()

    def _build_controls(self) -> None:
        frame = ttk.Frame(self.controls_frame, padding=10)
        frame.pack(fill=tk.BOTH, expand=True)
        ttk.Label(frame, text="Skill Map", font=FONTS["heading"]).pack(anchor=tk.W, pady=(0, 6))
        ttk.Label(
            frame,
            text="Node-based progression with branching paths. Select a node to view why it is recommended.",
            wraplength=280,
        ).pack(anchor=tk.W, pady=(0, 8))
        ttk.Button(frame, text="Refresh Map", command=self.render).pack(anchor=tk.W)
        self.start_btn = ttk.Button(frame, text="Start Node Quiz", command=self._start_selected_skill_quiz)
        self.start_btn.pack(anchor=tk.W, pady=(8, 0))

        ttk.Separator(frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)
        ttk.Label(frame, text="Grade level").pack(anchor=tk.W)
        self.grade_var = tk.StringVar(value="All")
        grade_cb = ttk.Combobox(
            frame,
            textvariable=self.grade_var,
            values=list(GRADE_OPTIONS),
            state="readonly",
            width=8,
        )
        grade_cb.pack(fill=tk.X, pady=(0, 6))
        grade_cb.bind("<<ComboboxSelected>>", lambda _e: self.render())

        self.k9_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            frame,
            text="K\u20139 Focus (hide advanced)",
            variable=self.k9_var,
            command=self.render,
        ).pack(anchor=tk.W, pady=(0, 6))

        ttk.Separator(frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)
        self.selected_var = tk.StringVar(value="Selected node: —")
        ttk.Label(frame, textvariable=self.selected_var, foreground=COLORS["accent_strong"], wraplength=280, justify=tk.LEFT).pack(
            anchor=tk.W
        )
        self.reason_var = tk.StringVar(value="")
        ttk.Label(frame, textvariable=self.reason_var, foreground=COLORS["text_secondary"], wraplength=280, justify=tk.LEFT).pack(
            anchor=tk.W, pady=(4, 0)
        )
        self.stats_var = tk.StringVar(value="")
        ttk.Label(frame, textvariable=self.stats_var, foreground=COLORS["text_primary"], wraplength=280, justify=tk.LEFT).pack(
            anchor=tk.W, pady=(6, 0)
        )
        self.deps_var = tk.StringVar(value="")
        ttk.Label(frame, textvariable=self.deps_var, foreground=COLORS["text_secondary"], wraplength=280, justify=tk.LEFT).pack(
            anchor=tk.W, pady=(4, 0)
        )
        self.subskills_var = tk.StringVar(value="")
        ttk.Label(frame, textvariable=self.subskills_var, foreground=COLORS["text_secondary"], wraplength=280, justify=tk.LEFT).pack(
            anchor=tk.W, pady=(4, 0)
        )
        self.mode_var = tk.StringVar(value="")
        ttk.Label(frame, textvariable=self.mode_var, foreground=COLORS["text_secondary"], wraplength=280, justify=tk.LEFT).pack(
            anchor=tk.W, pady=(4, 0)
        )

        ttk.Separator(frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)
        self.legend_var = tk.StringVar(
            value=(
                "Legend:\n"
                "Nodes: Green=Mastered | Blue=Frontier | Yellow=In progress | Gray=Locked\n"
                "Edges: Solid=Required | Dashed=Helpful\n"
                "Highlights: Purple=Prerequisite path | Teal=Unlock path"
            )
        )
        ttk.Label(frame, textvariable=self.legend_var, foreground=COLORS["text_secondary"], wraplength=280, justify=tk.LEFT).pack(
            anchor=tk.W
        )

    def _build_view(self) -> None:
        container = ttk.Frame(self.view_frame)
        container.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        self.canvas = tk.Canvas(
            container,
            bg=COLORS["panel_alt_bg"],
            highlightthickness=0,
            xscrollincrement=20,
            yscrollincrement=20,
        )
        x_scroll = ttk.Scrollbar(container, orient=tk.HORIZONTAL, command=self.canvas.xview)
        y_scroll = ttk.Scrollbar(container, orient=tk.VERTICAL, command=self.canvas.yview)
        self.canvas.configure(xscrollcommand=x_scroll.set, yscrollcommand=y_scroll.set)
        self.canvas.grid(row=0, column=0, sticky="nsew")
        y_scroll.grid(row=0, column=1, sticky="ns")
        x_scroll.grid(row=1, column=0, sticky="ew")
        container.rowconfigure(0, weight=1)
        container.columnconfigure(0, weight=1)
        self.canvas.bind("<Button-1>", self._on_canvas_click)
        self.canvas.bind("<MouseWheel>", self._on_mousewheel)

    def render(self) -> None:
        profile = self._profile_getter()
        if profile is None:
            self.canvas.delete("all")
            self.canvas.create_text(
                20,
                20,
                text="No profile selected.",
                anchor=tk.NW,
                fill=COLORS["text_muted"],
                font=FONTS["subheading"],
            )
            self.start_btn.state(["disabled"])
            self.selected_var.set("Selected node: —")
            self.reason_var.set("")
            self.stats_var.set("")
            self.deps_var.set("")
            self.subskills_var.set("")
            self.mode_var.set("")
            return

        self._profile_id = int(profile.id)
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
        self._reason_by_skill = {
            item.skill: item.reasons[0] if item.reasons else "Strong next step."
            for item in recommendations
        }
        self._stats_by_skill = stats
        self._coverage = coverage
        self._frontier = frontier
        self._dependents = _dependents_by_skill()
        self._progress_by_skill = _progress_by_skill(profile.id)

        self._draw_map(stats, frontier)

        if self._selected_skill not in SKILL_ORDER:
            self._selected_skill = SKILL_ORDER[0]
        self._update_selected_text()
        if self._quiz_launcher is None:
            self.start_btn.state(["disabled"])
        else:
            self.start_btn.state(["!disabled"])

    def _visible_tracks(self) -> list[str]:
        """Return track names that pass both the K-9 toggle and the grade filter."""
        all_tracks = [track for track in SKILL_TRACK_ORDER if skills_in_track(track)]
        if self.k9_var.get():
            all_tracks = [t for t in all_tracks if t not in ADVANCED_TRACKS]
        grade = self.grade_var.get()
        if grade == "All":
            return all_tracks
        # Filter tracks that have at least one skill matching the grade
        result: list[str] = []
        for track in all_tracks:
            skills = skills_in_track(track)
            if any(self._skill_matches_grade(s, grade) for s in skills):
                result.append(track)
        return result

    @staticmethod
    def _skill_matches_grade(skill: str, grade: str) -> bool:
        entry = CURRICULUM_BY_SKILL.get(skill)
        if entry is None:
            return True  # include unlisted skills by default
        return _grade_band_contains(entry.grade_band, grade)

    def _draw_map(self, stats, frontier: set[str]) -> None:
        self.canvas.delete("all")
        self._node_items.clear()
        self.canvas.update_idletasks()
        viewport_w = max(640, self.canvas.winfo_width())
        viewport_h = max(420, self.canvas.winfo_height())
        tracks = self._visible_tracks()
        grade = self.grade_var.get()
        virtual_w = max(viewport_w, (len(tracks) * 180) + 100)
        y_gap = 76
        left = 30
        row_width = max(120, virtual_w - (2 * left))

        positions: dict[str, tuple[int, int]] = {}
        max_rows = 0
        for track in tracks:
            skills = skills_in_track(track)
            if grade != "All":
                skills = tuple(s for s in skills if self._skill_matches_grade(s, grade))
            if not skills:
                continue
            max_rows = max(max_rows, len(skills))
        for col_idx, track in enumerate(tracks):
            skills = skills_in_track(track)
            if grade != "All":
                skills = tuple(s for s in skills if self._skill_matches_grade(s, grade))
            if not skills:
                continue
            x = int(left + ((col_idx + 0.5) * (row_width / float(max(1, len(tracks))))))
            self.canvas.create_text(x, 18, text=track, fill=COLORS["accent_strong"], font=FONTS["small"], width=150)
            for row_idx, skill in enumerate(skills):
                y = 42 + (row_idx * y_gap)
                positions[skill] = (x, y)

        ancestors = _collect_ancestors(self._selected_skill)
        descendants = _collect_descendants(self._selected_skill, self._dependents)
        direct_prereqs = {edge[0] for edge in SKILL_PREREQUISITE_EDGES.get(self._selected_skill, ())}
        direct_dependents = set(self._dependents.get(self._selected_skill, ()))

        for target, edges in SKILL_PREREQUISITE_EDGES.items():
            if target not in positions:
                continue
            tx, ty = positions[target]
            for source, kind, _weight in edges:
                if source not in positions:
                    continue
                sx, sy = positions[source]
                color = EDGE_BASE
                width = 2 if kind != PREREQ_HELPFUL else 1
                dash: tuple[int, ...] | None = None if kind != PREREQ_HELPFUL else (4, 4)
                if source in direct_prereqs and target == self._selected_skill:
                    color = EDGE_PREREQ
                    width = 3
                    dash = None
                elif source == self._selected_skill and target in direct_dependents:
                    color = EDGE_UNLOCK
                    width = 3
                    dash = None
                elif source in ancestors and target in (ancestors | {self._selected_skill}):
                    color = EDGE_ANCESTOR
                elif source in ({self._selected_skill} | descendants) and target in descendants:
                    color = EDGE_DESCENDANT
                self.canvas.create_line(
                    sx,
                    sy + 18,
                    tx,
                    ty - 18,
                    fill=color,
                    width=width,
                    dash=dash,
                    arrow=tk.LAST,
                    arrowshape=(7, 8, 3),
                )

        for skill in SKILL_ORDER:
            if skill not in positions:
                continue
            x, y = positions[skill]
            state = _node_state(skill, stats, frontier)
            fill = _node_fill(state)
            outline = "#a7b6c2"
            if skill == self._selected_skill:
                outline = COLORS["accent_strong"]
            elif skill in ancestors:
                outline = EDGE_PREREQ
            elif skill in descendants:
                outline = EDGE_UNLOCK
            rect_id = self.canvas.create_rectangle(x - 52, y - 18, x + 52, y + 18, fill=fill, outline=outline, width=2)
            label = SKILL_LABELS.get(skill, skill)
            text_id = self.canvas.create_text(x, y, text=label, fill=COLORS["text_primary"], font=FONTS["small"], width=96)
            self._node_items[rect_id] = skill
            self._node_items[text_id] = skill
            item = stats.get(skill)
            if item is not None and item.attempts > 0:
                self.canvas.create_text(
                    x + 48,
                    y - 14,
                    text=str(item.attempts),
                    fill=COLORS["accent"],
                    font=FONTS["small"],
                    anchor=tk.E,
                )

        virtual_h = max(viewport_h, 90 + (max_rows * y_gap) + 30)
        self.canvas.config(scrollregion=(0, 0, virtual_w, virtual_h))

    def _on_canvas_click(self, event) -> None:
        items = self.canvas.find_overlapping(event.x - 2, event.y - 2, event.x + 2, event.y + 2)
        if not items:
            return
        for item_id in reversed(items):
            skill = self._node_items.get(int(item_id))
            if skill is None:
                continue
            self._selected_skill = skill
            self.render()
            return

    def _update_selected_text(self) -> None:
        label = SKILL_LABELS.get(self._selected_skill, self._selected_skill)
        item = self._stats_by_skill.get(self._selected_skill)
        mastery = item.mastery if item is not None else "Not started"
        self.selected_var.set(f"Selected node: {label} ({mastery})")
        self.reason_var.set(
            self._reason_by_skill.get(self._selected_skill, "Tip: complete this node to unlock new branches.")
        )
        if item is None:
            self.stats_var.set("No stats yet.")
        else:
            accuracy = f"{item.correct_questions}/{item.total_questions} ({item.weighted_accuracy:.0f}%)"
            recent = f"{item.recent_accuracy:.0f}%"
            trend = f"{item.recent_trend:+.1f}"
            speed = "—" if item.avg_seconds_per_question is None else f"{item.avg_seconds_per_question:.1f}s/q"
            self.stats_var.set(
                f"Attempts: {item.attempts}\n"
                f"Accuracy: {accuracy}\n"
                f"Recent: {recent} | Trend: {trend} | Speed: {speed}"
            )

        prereqs = [edge[0] for edge in SKILL_PREREQUISITE_EDGES.get(self._selected_skill, ())]
        dependents = list(self._dependents.get(self._selected_skill, ()))
        prereq_text = _format_skill_status_list(prereqs, self._stats_by_skill)
        dependent_text = _format_skill_status_list(dependents, self._stats_by_skill)
        self.deps_var.set(f"Prerequisites: {prereq_text}\nUnlocks: {dependent_text}")

        subskills = _safe_subskills(self._selected_skill)
        coverage = self._coverage.get(self._selected_skill, 1.0)
        progress = self._progress_by_skill.get(self._selected_skill, {})
        if subskills:
            pending = [name for name in subskills if not _is_subskill_mastered(progress.get(name))]
            pending_preview = ", ".join(pending[:3]) if pending else "none"
            self.subskills_var.set(
                f"Subskills: {int(round(coverage * 100.0))}% mastered ({len(subskills)} total)\n"
                f"Needs work: {pending_preview}"
            )
        else:
            self.subskills_var.set("Subskills: none listed for this node.")

        if self._profile_id is None:
            self.mode_var.set("")
        else:
            mode_acc = db.mode_accuracy_by_skill(self._profile_id, self._selected_skill)
            intuition = _fmt_pct(mode_acc.get("intuition"))
            expression = _fmt_pct(mode_acc.get("expression"))
            word = _fmt_pct(mode_acc.get("word"))
            self.mode_var.set(f"Mode accuracy I/E/W: {intuition} / {expression} / {word}")

    def _start_selected_skill_quiz(self) -> None:
        if self._quiz_launcher is None:
            return
        self._quiz_launcher(self._selected_skill)

    def _on_mousewheel(self, event) -> None:
        if event.delta == 0:
            return
        direction = -1 if event.delta > 0 else 1
        self.canvas.yview_scroll(direction, "units")


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
        return "#d4ead8"
    if state == "frontier":
        return "#c9dff6"
    if state == "in_progress":
        return "#f6e8bf"
    return "#e7ebf0"


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


def _dependents_by_skill() -> dict[str, tuple[str, ...]]:
    out: dict[str, list[str]] = {skill: [] for skill in SKILL_ORDER}
    for target, edges in SKILL_PREREQUISITE_EDGES.items():
        for source, _kind, _weight in edges:
            if source not in out:
                out[source] = []
            if target not in out[source]:
                out[source].append(target)
    return {skill: tuple(items) for skill, items in out.items()}


def _collect_ancestors(skill: str) -> set[str]:
    seen: set[str] = set()
    stack = [skill]
    while stack:
        node = stack.pop()
        for prereq, _kind, _weight in SKILL_PREREQUISITE_EDGES.get(node, ()):
            if prereq in seen:
                continue
            seen.add(prereq)
            stack.append(prereq)
    return seen


def _collect_descendants(skill: str, dependents: dict[str, tuple[str, ...]]) -> set[str]:
    seen: set[str] = set()
    stack = [skill]
    while stack:
        node = stack.pop()
        for child in dependents.get(node, ()):
            if child in seen:
                continue
            seen.add(child)
            stack.append(child)
    return seen


def _status_for(skill: str, stats: dict[str, SkillStats]) -> str:
    item = stats.get(skill)
    if item is None:
        return "Not started"
    return item.mastery


def _format_skill_status_list(skills: list[str], stats: dict[str, SkillStats]) -> str:
    if not skills:
        return "none"
    labels = []
    for skill in skills[:4]:
        status = _status_for(skill, stats)
        labels.append(f"{SKILL_LABELS.get(skill, skill)} ({status})")
    if len(skills) > 4:
        labels.append("...")
    return ", ".join(labels)


def _progress_by_skill(profile_id: int) -> dict[str, dict[str, object]]:
    rows = db.list_subskill_progress(profile_id)
    out: dict[str, dict[str, object]] = {}
    for item in rows:
        skill_map = out.setdefault(item.skill, {})
        skill_map[item.subskill] = item
    return out


def _is_subskill_mastered(item: object | None) -> bool:
    if item is None:
        return False
    return bool(getattr(item, "mastered", False))


def _fmt_pct(value: float | None) -> str:
    if value is None:
        return "—"
    return f"{value:.0f}%"
