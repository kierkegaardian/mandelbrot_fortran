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
    mode_intuition_pct: Optional[int]
    mode_expression_pct: Optional[int]
    mode_word_pct: Optional[int]


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
    elapsed_seconds: Optional[float]


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
    archived_at: Optional[str] = None


@dataclass(frozen=True)
class SubskillProgress:
    profile_id: int
    skill: str
    subskill: str
    current_streak: int
    best_streak: int
    mastered: bool
    updated_at: str


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
    mode: str
    active: bool
    archetype_id: Optional[str] = None
    reasoning_kind: str = "legacy"
    misconceptions_json: str = "[]"


@dataclass(frozen=True)
class TemplateVar:
    template_id: int
    name: str
    kind: str  # "int" or "float"
    min_value: float
    max_value: float
    step: float


@dataclass(frozen=True)
class Assignment:
    id: int
    profile_id: int
    skill: str
    subskill: Optional[str]
    target_type: str
    target_value: float
    level: int
    num_questions: int
    question_type: str
    mode_intuition_pct: Optional[int]
    mode_expression_pct: Optional[int]
    mode_word_pct: Optional[int]
    active: bool
    notes: str
    created_at: str
    completed_at: Optional[str]


@dataclass(frozen=True)
class DailyGoalHistory:
    profile_id: int
    day_utc: str
    completions: int
    last_completed_at: str


@dataclass(frozen=True)
class SchoolYearTarget:
    profile_id: int
    grade: int
    stretch_enabled: bool
    updated_at: str


@dataclass(frozen=True)
class HistoricalTest:
    id: int
    exam_code: str
    title: str
    exam_type: str
    year: Optional[int]
    pdf_path: str
    source: str


@dataclass(frozen=True)
class HistoricalQuestion:
    id: int
    test_id: int
    question_number: int
    section: str
    category: str
    prompt: str
    choice_a: Optional[str]
    choice_b: Optional[str]
    choice_c: Optional[str]
    choice_d: Optional[str]
    choice_e: Optional[str]
    correct_answer: Optional[str]
    explanation: str
    source_page: Optional[int]


@dataclass(frozen=True)
class ScaffoldStep:
    prompt: str
    expected_answer: str
    hint: str


@dataclass(frozen=True)
class SummerProgram:
    id: int
    profile_id: int
    lane: str
    start_date: str
    end_date: str
    days_per_week: int
    minutes_per_session: int
    status: str
    finish_definition: str
    placement_recommendation: Optional[str]
    placement_review_status: str
    placement_reviewed_at: Optional[str]
    student_age_years: Optional[int]
    created_at: str
    updated_at: str


@dataclass(frozen=True)
class SummerProgramTask:
    id: int
    program_id: int
    unit_code: str
    task_kind: str
    skill: str
    subskill: Optional[str]
    sequence_index: int
    status: str
    target_score_pct: Optional[float]
    scheduled_date: str
    notes_json: str


@dataclass(frozen=True)
class SummerAssessmentRun:
    id: int
    program_id: int
    assessment_type: str
    score_pct: float
    passed: bool
    strand_results_json: str
    completed_at: str


@dataclass(frozen=True)
class SummerProgramReviewState:
    current_lane: str
    recommended_lane: Optional[str]
    review_status: str
    weak_strands: tuple[str, ...]
    age_gate_note: Optional[str]
    latest_placement_score_pct: Optional[float]


@dataclass(frozen=True)
class SummerProgramBlockSummary:
    reason: Optional[str]
    task_id: Optional[int]
    unit_code: Optional[str]
    task_kind: Optional[str]
    score_pct: Optional[float]
    required_score_pct: Optional[float]
    weak_strands: tuple[str, ...]
    next_action: Optional[str]


@dataclass(frozen=True)
class SummerProgramStatusSummary:
    program_id: int
    current_lane: str
    recommended_lane: Optional[str]
    review_status: str
    weak_strands: tuple[str, ...]
    current_blocker: Optional[str]
    next_action: Optional[str]
    pace_label: str
    finish_state: str
    launchable: bool
    catch_up_note: Optional[str]
    projected_finish_date: Optional[str]
    projected_finish_note: Optional[str]
    remediation_note: Optional[str]
    remediation_focus: tuple[str, ...]
    current_task: Optional[SummerProgramTask]
    review_state: SummerProgramReviewState
    block_summary: SummerProgramBlockSummary
