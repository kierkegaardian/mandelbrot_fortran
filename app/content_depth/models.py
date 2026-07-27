from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ReasoningKind(str, Enum):
    CONCEPTUAL = "conceptual"
    PROCEDURAL = "procedural"
    TRANSFER = "transfer"
    APPLICATION = "application"
    PROOF = "proof"
    LEGACY = "legacy"


class ResponseKind(str, Enum):
    CHOICE = "choice"
    TYPED = "typed"
    PROOF_BUILDER = "proof_builder"


class ContentStatus(str, Enum):
    SCAFFOLD = "scaffold"
    READY = "ready"


@dataclass(frozen=True)
class MisconceptionSpec:
    code: str
    feedback: str
    hint: str
    recovery_archetype_id: str


@dataclass(frozen=True)
class MisconceptionCandidate:
    code: str
    expected_answer: str
    feedback: str
    hint: str
    recovery_archetype_id: str


@dataclass(frozen=True)
class WorkedExampleStep:
    stage: str
    prompt: str
    explanation: str
    expected_answer: str | None = None


@dataclass(frozen=True)
class WorkedExample:
    title: str
    steps: tuple[WorkedExampleStep, ...]


@dataclass(frozen=True)
class ProofStep:
    step_id: str
    statement: str
    reason: str
    depends_on: tuple[str, ...] = ()


@dataclass(frozen=True)
class ProofSpec:
    prompt: str
    required_steps: tuple[ProofStep, ...]
    distractor_steps: tuple[ProofStep, ...]

    @property
    def step_bank(self) -> tuple[ProofStep, ...]:
        return self.required_steps + self.distractor_steps


@dataclass(frozen=True)
class ArchetypeSpec:
    archetype_id: str
    reasoning_kind: ReasoningKind
    prompt_prefix: str = ""


@dataclass(frozen=True)
class DepthSpec:
    skill: str
    subskill: str
    content_status: ContentStatus
    archetypes: tuple[ArchetypeSpec, ...]
    worked_example: WorkedExample
    misconceptions: tuple[MisconceptionSpec, ...]
    proof: ProofSpec | None = None

    def archetype(self, archetype_id: str) -> ArchetypeSpec | None:
        return next((item for item in self.archetypes if item.archetype_id == archetype_id), None)


@dataclass(frozen=True)
class QuestionRequest:
    skill: str
    level: int
    question_type: str
    subskill: str | None = None
    preferred_mode: str | None = None
    preferred_archetype_id: str | None = None
    excluded_archetype_ids: frozenset[str] = frozenset()
