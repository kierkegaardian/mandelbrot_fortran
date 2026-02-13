from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class Profile:
    id: int
    name: str
    role: str  # "child" or "parent"


@dataclass(frozen=True)
class QuizSet:
    id: int
    name: str
    skill: str
    question_type: str  # "mc", "typed", or "both"
    num_questions: int
    level: int


@dataclass(frozen=True)
class QuizAttempt:
    id: int
    profile_id: int
    quiz_set_id: Optional[int]
    skill: str
    question_type: str
    num_questions: int
    level: int
    score: int
    created_at: str


@dataclass(frozen=True)
class Worksheet:
    id: int
    profile_id: int
    quiz_set_id: Optional[int]
    skill: str
    question_type: str
    num_questions: int
    level: int
    file_path: str
    created_at: str


@dataclass(frozen=True)
class SubskillProgress:
    profile_id: int
    skill: str
    subskill: str
    current_streak: int
    best_streak: int
    mastered: bool


@dataclass(frozen=True)
class Book:
    id: int
    title: str
    source: str
    pdf_filename: str


@dataclass(frozen=True)
class ExerciseCandidate:
    id: int
    book_id: int
    location: str
    text: str
    status: str  # "new", "ignored", "templated"


@dataclass(frozen=True)
class QuestionTemplate:
    id: int
    book_id: Optional[int]
    external_id: Optional[str]
    skill: str
    subskill: str
    label: str
    prompt_template: str
    answer_expr: str
    constraint_expr: str
    explanation_template: str
    min_level: int
    max_level: int
    choice_spread: float
    active: bool


@dataclass(frozen=True)
class TemplateVar:
    template_id: int
    name: str
    kind: str  # "int" or "float"
    min_value: float
    max_value: float
    step: float
