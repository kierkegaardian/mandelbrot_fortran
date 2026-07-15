"""Dashboard data refresh and progress rendering."""

from __future__ import annotations

from datetime import datetime, timezone

from . import db
from .learning_engine import build_skill_stats, recommend_next_skill_paths
from .skill_graph import (
    SKILL_LABELS,
    SKILL_ORDER,
    SKILL_PREREQUISITE_WEIGHTS,
    SUBSKILL_STREAK_TO_MASTER,
    subskills_for,
)
from .theme import progress_style_for_mastery


class DashboardRenderMixin:
    def render(self) -> None:
        profile = self._profile_getter()
        if profile is None:
            self.summary_var.set("No profile selected.")
            self.reco_var.set("Recommended next: —")
            self.reco_detail_var.set("")
            self.daily_var.set("Daily review: —")
            self.assignment_var.set("Assignment: —")
            for skill, row in self.progress_rows.items():
                row["progress_var"].set(0)
                row["percent_var"].set("0%")
                row["mastery_var"].set("Not started")
                row["progress_bar"].configure(
                    style=progress_style_for_mastery("Not started")
                )
            for label, var in self.tile_vars.items():
                var.set(f"{label}: 0")
            self.daily_btn.state(["disabled"])
            self.assignment_btn.state(["disabled"])
            return
        attempts = db.list_attempts(profile.id)
        skill_stats = build_skill_stats(attempts, tuple(SKILL_ORDER))
        activity = db.skill_progress_pipeline(profile.id)
        stats = {
            skill: {"score": item.correct_questions, "total": item.total_questions, "attempts": item.attempts}
            for skill, item in skill_stats.items()
        }
        subskill_coverage = _subskill_coverage_by_skill(profile.id)

        mastery_map: dict[str, str] = {}
        counts = {label: 0 for label in self.tile_vars}
        for skill in SKILL_ORDER:
            item = skill_stats.get(skill)
            if item is None:
                avg = 0.0
                mastery = "Not started"
            else:
                avg = item.weighted_accuracy
                mastery = item.mastery
            mastery_map[skill] = mastery
            if mastery in counts:
                counts[mastery] += 1
            row = self.progress_rows.get(skill)
            if row:
                row["progress_var"].set(avg)
                row["percent_var"].set(f"{avg:.0f}%")
                row["mastery_var"].set(mastery)
                row["progress_bar"].configure(
                    style=progress_style_for_mastery(mastery)
                )

        for label, var in self.tile_vars.items():
            var.set(f"{label}: {counts.get(label, 0)}")

        completed = sum(1 for s in SKILL_ORDER if mastery_map.get(s) == "Mastered")
        total_questions = sum(item.get("questions", 0) for item in activity.values())
        total_worksheets = sum(item.get("worksheets", 0) for item in activity.values())
        self.summary_var.set(
            f"{profile.name}: {completed}/{len(SKILL_ORDER)} mastered • {total_questions} quiz Qs • {total_worksheets} worksheets"
        )
        branch_recommendations = recommend_next_skill_paths(
            tuple(SKILL_ORDER),
            SKILL_PREREQUISITE_WEIGHTS,
            skill_stats,
            subskill_coverage=subskill_coverage,
        )
        recommendations = [item.skill for item in branch_recommendations]
        if recommendations:
            labels = [SKILL_LABELS.get(skill, skill) for skill in recommendations]
            self.reco_var.set(f"Recommended next: {', '.join(labels)}")
            reason_lines: list[str] = []
            for item in branch_recommendations[:3]:
                label = SKILL_LABELS.get(item.skill, item.skill)
                reason = item.reasons[0] if item.reasons else "Strong next step."
                reason_lines.append(f"{label}: {reason}")
            self.reco_detail_var.set("Branch paths: " + " | ".join(reason_lines))
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
            self.reco_detail_var.set("")
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
                except (ValueError, TypeError):
                    continue
                if updated.tzinfo is None:
                    updated = updated.replace(tzinfo=timezone.utc)
                age_days = int((now - updated).total_seconds() // 86400)
                if item.mastered and age_days >= 21:
                    due.append((3, age_days, skill, subskill, f"maintenance {age_days}d"))
                elif (not item.mastered) and item.current_streak <= 0 and age_days >= 3:
                    due.append((1, age_days, skill, subskill, f"rebuild {age_days}d"))
                elif (not item.mastered) and item.current_streak < SUBSKILL_STREAK_TO_MASTER and age_days >= 5:
                    due.append((2, age_days, skill, subskill, f"streak {age_days}d"))
                elif (not item.mastered) and age_days >= 10:
                    due.append((3, age_days, skill, subskill, f"stale {age_days}d"))

        today_count, streak = db.daily_goal_status(profile_id)
        goal_text = f"Goal streak: {streak} day(s), today: {today_count} review(s)"

        if not due:
            self._daily_target = None
            self.daily_var.set(f"Daily review: all caught up • {goal_text}")
            self.daily_btn.state(["disabled"])
            return

        due.sort(key=lambda t: (t[0], -t[1], SKILL_ORDER.index(t[2])))
        _priority, _age, skill, subskill, status = due[0]
        self._daily_target = (skill, subskill)
        self.daily_var.set(f"Daily review: {SKILL_LABELS.get(skill, skill)} – {subskill} ({status}) • {goal_text}")
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
            target_text = "score = 100%"
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


def _subskill_coverage_by_skill(profile_id: int) -> dict[str, float]:
    progress = db.list_subskill_progress(profile_id)
    by_skill: dict[str, dict[str, int]] = {}
    for item in progress:
        if item.skill not in by_skill:
            by_skill[item.skill] = {"mastered": 0, "total": 0}
        by_skill[item.skill]["total"] += 1
        if item.mastered:
            by_skill[item.skill]["mastered"] += 1
    coverage: dict[str, float] = {}
    for skill, counts in by_skill.items():
        total = max(1, counts["total"])
        coverage[skill] = float(counts["mastered"]) / float(total)
    return coverage
