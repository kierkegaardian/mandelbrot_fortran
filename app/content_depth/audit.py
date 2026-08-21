from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import hashlib
import random
from typing import TYPE_CHECKING

from ..explanations import explanation_for
from ..ui_arithmetic import khan_url_for_selection
from .generation import generate_depth_question
from .models import ContentStatus, QuestionRequest, ReasoningKind, ResponseKind
from .pilot_generators import has_pilot_generator
from .registry import PROOF_SUBSKILLS, depth_spec_for, in_scope_pairs

if TYPE_CHECKING:
    from ..quiz_engine import Question


Readiness = str
READY: Readiness = "ready"
THIN: Readiness = "thin"
MISSING: Readiness = "missing"


@dataclass(frozen=True)
class DepthAuditRow:
    skill: str
    subskill: str
    reasoning_counts: tuple[tuple[str, int], ...]
    worked_example_steps: int
    misconception_count: int
    has_application: bool
    has_proof: bool
    generation_failures: tuple[str, ...]
    readiness: Readiness
    notes: tuple[str, ...]
    sample_prompt: str


@dataclass(frozen=True)
class DepthAuditReport:
    rows: tuple[DepthAuditRow, ...]

    @property
    def ready_count(self) -> int:
        return sum(row.readiness == READY for row in self.rows)

    @property
    def thin_count(self) -> int:
        return sum(row.readiness == THIN for row in self.rows)

    @property
    def missing_count(self) -> int:
        return sum(row.readiness == MISSING for row in self.rows)

    @property
    def depth_ready(self) -> bool:
        return bool(self.rows) and self.ready_count == len(self.rows)

    @property
    def weakest_rows(self) -> tuple[DepthAuditRow, ...]:
        order = {MISSING: 0, THIN: 1, READY: 2}
        return tuple(sorted(self.rows, key=lambda row: (order[row.readiness], row.skill, row.subskill)))


def build_depth_audit(
    *, generation_types: tuple[str, ...] = ("typed", "mc"), seeds_per_archetype: int = 1
) -> DepthAuditReport:
    state = random.getstate()
    try:
        return DepthAuditReport(
            tuple(
                _audit_subskill(skill, subskill, generation_types, max(1, int(seeds_per_archetype)))
                for skill, subskill in in_scope_pairs()
            )
        )
    finally:
        random.setstate(state)


def _audit_subskill(
    skill: str, subskill: str, generation_types: tuple[str, ...], seeds_per_archetype: int
) -> DepthAuditRow:
    spec = depth_spec_for(skill, subskill)
    if spec is None:
        return DepthAuditRow(skill, subskill, (), 0, 0, False, False, (), MISSING, ("missing depth manifest",), "")
    counts = Counter(item.reasoning_kind.value for item in spec.archetypes)
    failures: list[str] = []
    semantic_notes: list[str] = []
    sample = ""
    authored = spec.content_status is ContentStatus.READY
    seeds_to_run = seeds_per_archetype if authored else 1
    for archetype in spec.archetypes:
        for question_type in generation_types:
            for seed_index in range(seeds_to_run):
                try:
                    seed_text = f"{archetype.archetype_id}:{question_type}:{seed_index}".encode("utf-8")
                    random.seed(int.from_bytes(hashlib.sha256(seed_text).digest()[:8], "big"))
                    question = generate_depth_question(
                        QuestionRequest(
                            skill, 2, question_type, subskill=subskill,
                            preferred_archetype_id=archetype.archetype_id,
                        )
                    )
                    if not question.correct_answer:
                        failures.append(f"{archetype.archetype_id}/{question_type}/{seed_index}: empty answer")
                    if question.archetype_id != archetype.archetype_id:
                        failures.append(f"{archetype.archetype_id}/{question_type}/{seed_index}: wrong archetype")
                    if question.reasoning_kind is not archetype.reasoning_kind:
                        failures.append(f"{archetype.archetype_id}/{question_type}/{seed_index}: wrong reasoning kind")
                    if authored:
                        _check_authored_question(question, archetype.reasoning_kind, question_type, semantic_notes)
                    if archetype.reasoning_kind is ReasoningKind.APPLICATION and ";" not in question.correct_answer:
                        failures.append(f"{archetype.archetype_id}/{question_type}/{seed_index}: no constructed model")
                    if not sample:
                        sample = question.prompt
                except Exception as exc:  # surfaced in audit evidence
                    failures.append(
                        f"{archetype.archetype_id}/{question_type}/{seed_index}: {type(exc).__name__}: {exc}"
                    )
    notes: list[str] = []
    if not authored:
        notes.append("scaffold manifest only; substantive archetype content is not authored")
    elif not has_pilot_generator(skill, subskill):
        notes.append("ready status has no authored generator")
    for kind in (ReasoningKind.CONCEPTUAL, ReasoningKind.PROCEDURAL, ReasoningKind.TRANSFER):
        if counts[kind.value] < 1:
            notes.append(f"missing {kind.value} archetype")
    has_application = counts[ReasoningKind.APPLICATION.value] >= 1
    if not has_application:
        notes.append("missing application archetype")
    stages = tuple(step.stage for step in spec.worked_example.steps)
    if stages != ("model", "guided", "transfer"):
        notes.append("worked example must contain model/guided/transfer stages")
    if authored and len({step.prompt.strip() for step in spec.worked_example.steps}) != 3:
        notes.append("worked-example stages do not use three distinct tasks")
    if authored and any(not (step.expected_answer or "").strip() for step in spec.worked_example.steps):
        notes.append("worked-example stage is missing an answer key")
    if len(spec.misconceptions) < 2:
        notes.append(f"misconceptions {len(spec.misconceptions)}/2")
    explanation = explanation_for(skill, subskill)
    if not (explanation.mental_model and explanation.common_mistake and explanation.try_this):
        notes.append("missing enriched intuition")
    if not khan_url_for_selection(skill, subskill):
        notes.append("missing Khan mapping")
    proof_required = subskill in PROOF_SUBSKILLS
    has_proof = spec.proof is not None and counts[ReasoningKind.PROOF.value] >= 1
    if proof_required:
        if not has_proof:
            notes.append("missing structured proof")
        elif len(spec.proof.required_steps) < 4 or len(spec.proof.distractor_steps) < 2:
            notes.append("proof needs four required steps and two distractors")
    notes.extend(dict.fromkeys(semantic_notes))
    notes.extend(failures)
    readiness = READY if not notes else THIN
    return DepthAuditRow(
        skill, subskill, tuple(sorted(counts.items())), len(spec.worked_example.steps),
        len(spec.misconceptions), has_application, has_proof, tuple(failures), readiness,
        tuple(notes), sample,
    )


def _check_authored_question(
    question: "Question", reasoning_kind: ReasoningKind, question_type: str, notes: list[str]
) -> None:
    if len(question.misconceptions) < 2:
        notes.append("generated question has fewer than two diagnostic misconception answers")
    candidate_answers = [item.expected_answer for item in question.misconceptions]
    if len(set(candidate_answers)) != len(candidate_answers) or question.correct_answer in candidate_answers:
        notes.append("generated misconception answers are not distinct from each other and the key")
    if question_type == "mc" and question.response_kind is not ResponseKind.PROOF_BUILDER:
        if question.choices is None or question.correct_answer not in question.choices:
            notes.append("multiple-choice form does not contain its answer key")
        else:
            if not set(candidate_answers) <= set(question.choices):
                notes.append("multiple-choice form omits diagnostic misconception distractors")
            if reasoning_kind is ReasoningKind.APPLICATION:
                model_choices = {
                    choice.partition(";")[0].strip().lower() for choice in question.choices if ";" in choice
                }
                if len(model_choices) < 2:
                    notes.append("application choices do not require selecting a model")
    if reasoning_kind is ReasoningKind.APPLICATION:
        if "model" not in question.prompt.lower() or ";" not in question.correct_answer:
            notes.append("application does not require a model and result")
    if reasoning_kind is ReasoningKind.TRANSFER:
        lowered = question.prompt.lower()
        if not any(token in lowered for token in ("learner", "diagnose", "correct")):
            notes.append("transfer task does not analyze or correct an error")
