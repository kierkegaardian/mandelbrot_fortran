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
