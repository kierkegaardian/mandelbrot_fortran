from __future__ import annotations

from dataclasses import dataclass, replace
import random

from ..quiz_engine import Question, generate_question
from ..texas_grade_goals import TexasGoal, texas_grade_plan
from .generation import generate_depth_question
from .models import ContentStatus, QuestionRequest, ReasoningKind
from .registry import depth_spec_for
from .units import ALGEBRA_1_UNITS, CumulativeMix, cumulative_mix, texas_question_count


@dataclass(frozen=True)
class CumulativeQuiz:
    code: str
    label: str
    questions: tuple[Question, ...]
    mix: CumulativeMix
    pass_score_pct: float = 80.0


@dataclass(frozen=True)
class CumulativeResult:
    score_pct: float
    passed: bool
    recommended_review: tuple[tuple[str, str], ...]


def build_texas_cumulative_quiz(grade: int, check_number: int, *, seed: int = 0) -> CumulativeQuiz:
    goals = tuple(goal for goal in texas_grade_plan(grade).goals if not goal.stretch and goal.quiz_ready)
    end = min(len(goals), max(2, int(check_number) * 2))
    current = goals[max(0, end - 1):end]
    earlier = goals[:max(0, end - 1)]
    count = texas_question_count(grade)
    questions = _compose_questions(current, earlier, count, random.Random(seed))
    return CumulativeQuiz(
        f"texas_g{grade}_cumulative_{check_number}",
        f"Grade {grade} Cumulative Check {check_number}",
        questions,
        cumulative_mix(count),
    )


def build_algebra1_cumulative_quiz(unit_number: int, *, seed: int = 0, question_count: int = 12) -> CumulativeQuiz:
    index = max(1, min(int(unit_number), len(ALGEBRA_1_UNITS))) - 1
    unit = ALGEBRA_1_UNITS[index]
    current = (_algebra_goal(unit.code, unit.label, unit.subskills),)
    earlier = tuple(_algebra_goal(item.code, item.label, item.subskills) for item in ALGEBRA_1_UNITS[:index])
    questions = _compose_questions(current, earlier, question_count, random.Random(seed))
    return CumulativeQuiz(
        f"algebra1_cumulative_{index + 1}",
        f"Algebra 1 Unit {index + 1} Cumulative Check",
        questions,
        cumulative_mix(question_count),
    )


def evaluate_cumulative_quiz(quiz: CumulativeQuiz, results: tuple[bool, ...]) -> CumulativeResult:
    total = len(quiz.questions)
    correct = sum(1 for value in results[:total] if value)
    score = (correct / total * 100.0) if total else 0.0
    review: list[tuple[str, str]] = []
    if score < quiz.pass_score_pct:
        for question, is_correct in zip(quiz.questions, results):
            if is_correct or question.subskill is None:
                continue
            target = (question.skill, question.subskill)
            if target not in review:
                review.append(target)
    return CumulativeResult(score, score >= quiz.pass_score_pct, tuple(review))


def _compose_questions(
    current_goals: tuple[TexasGoal, ...],
    earlier_goals: tuple[TexasGoal, ...],
    count: int,
    rng: random.Random,
) -> tuple[Question, ...]:
    mix = cumulative_mix(count)
    current_count = mix.current + (mix.earlier if not earlier_goals else 0)
    earlier_count = mix.earlier if earlier_goals else 0
    questions: list[Question] = []
    questions.extend(_sample_goal_questions(current_goals, current_count, rng, application=False))
    questions.extend(_sample_goal_questions(earlier_goals, earlier_count, rng, application=False))
    all_goals = (*current_goals, *earlier_goals)
    questions.extend(_sample_goal_questions(all_goals, mix.application, rng, application=True))
    rng.shuffle(questions)
    return tuple(questions)


def _sample_goal_questions(
    goals: tuple[TexasGoal, ...], count: int, rng: random.Random, *, application: bool
) -> list[Question]:
    targets = [(goal, subskill) for goal in goals for subskill in goal.subskills if goal.skill is not None]
    if not targets or count <= 0:
        return []
    questions: list[Question] = []
    first_cycle = list(targets)
    rng.shuffle(first_cycle)
    for index in range(count):
        goal, subskill = first_cycle[index] if index < len(first_cycle) else rng.choice(targets)
        assert goal.skill is not None
        spec = depth_spec_for(goal.skill, subskill)
        archetype_id = None
        if spec is not None and spec.content_status is ContentStatus.READY:
            kind = ReasoningKind.APPLICATION if application else ReasoningKind.PROCEDURAL
            archetype_id = next(
                (item.archetype_id for item in spec.archetypes if item.reasoning_kind is kind), None
            )
        if spec is not None and spec.content_status is ContentStatus.READY and archetype_id is not None:
            question = generate_depth_question(
                QuestionRequest(
                    goal.skill,
                    goal.quiz_level,
                    "typed",
                    subskill,
                    preferred_archetype_id=archetype_id,
                )
            )
        else:
            question = generate_question(goal.skill, goal.quiz_level, "typed", subskill=subskill)
        questions.append(replace(question, scaffold_steps=None, question_label="Cumulative Check"))
    return questions


def _algebra_goal(code: str, label: str, subskills: tuple[str, ...]) -> TexasGoal:
    return TexasGoal(code, label, (), "algebra_1", subskills, "Connect each representation to prior units.", 2)
