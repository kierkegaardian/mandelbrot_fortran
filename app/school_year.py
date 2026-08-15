from __future__ import annotations

from dataclasses import dataclass

from . import db
from .models import SchoolYearTarget, SubskillProgress
from .skill_graph import SUBSKILL_STREAK_TO_MASTER
from .texas_grade_goals import TexasGoal, TexasGradePlan, texas_grade_plan


@dataclass(frozen=True)
class SchoolYearGoalStep:
    subskill: str
    current_streak: int
    best_streak: int
    target_streak: int
    mastered: bool


@dataclass(frozen=True)
class SchoolYearStatus:
    target: SchoolYearTarget
    plan: TexasGradePlan
    active_goals: tuple[TexasGoal, ...]
    completed_goals: tuple[TexasGoal, ...]
    next_goal: TexasGoal | None
    next_goal_steps: tuple[SchoolYearGoalStep, ...]
    content_gaps: tuple[TexasGoal, ...]

    @property
    def completed_count(self) -> int:
        return len(self.completed_goals)

    @property
    def total_count(self) -> int:
        return len(self.active_goals)


def school_year_status(profile_id: int) -> SchoolYearStatus | None:
    target = db.get_school_year_target(profile_id)
    if target is None:
        return None
    plan = texas_grade_plan(target.grade)
    active_goals = tuple(
        goal for goal in plan.goals if goal.quiz_ready and (target.stretch_enabled or not goal.stretch)
    )
    progress: dict[tuple[str, str], SubskillProgress] = {
        (item.skill, item.subskill): item
        for item in db.list_subskill_progress(profile_id)
    }
    completed = tuple(goal for goal in active_goals if _goal_mastered(goal, progress))
    completed_codes = {goal.code for goal in completed}
    next_goal = next((goal for goal in active_goals if goal.code not in completed_codes), None)
    next_goal_steps = _goal_steps(next_goal, progress)
    gaps = tuple(goal for goal in plan.goals if not goal.quiz_ready)
    return SchoolYearStatus(
        target=target,
        plan=plan,
        active_goals=active_goals,
        completed_goals=completed,
        next_goal=next_goal,
        next_goal_steps=next_goal_steps,
        content_gaps=gaps,
    )


def _goal_mastered(goal: TexasGoal, progress: dict[tuple[str, str], SubskillProgress]) -> bool:
    if goal.skill is None or not goal.subskills:
        return False
    for subskill in goal.subskills:
        item = progress.get((goal.skill, subskill))
        if item is None or not bool(getattr(item, "mastered", False)):
            return False
    return True


def _goal_steps(
    goal: TexasGoal | None,
    progress: dict[tuple[str, str], SubskillProgress],
) -> tuple[SchoolYearGoalStep, ...]:
    if goal is None or goal.skill is None:
        return ()
    steps: list[SchoolYearGoalStep] = []
    for subskill in goal.subskills:
        item = progress.get((goal.skill, subskill))
        current_streak = int(item.current_streak) if item is not None else 0
        best_streak = int(item.best_streak) if item is not None else 0
        mastered = bool(item.mastered) if item is not None else False
        steps.append(
            SchoolYearGoalStep(
                subskill=subskill,
                current_streak=current_streak,
                best_streak=best_streak,
                target_streak=SUBSKILL_STREAK_TO_MASTER,
                mastered=mastered,
            )
        )
    return tuple(steps)
