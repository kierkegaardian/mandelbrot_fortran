from __future__ import annotations

import json
import math
import random
from dataclasses import replace
from typing import TYPE_CHECKING

from ..explanations import explanation_for
from .models import (
    ArchetypeSpec,
    ContentStatus,
    DepthSpec,
    MisconceptionCandidate,
    QuestionRequest,
    ReasoningKind,
    ResponseKind,
)
from .pilot_generators import generate_pilot_question, has_pilot_generator
from .proof import encode_proof_answer
from .registry import depth_spec_for

if TYPE_CHECKING:
    from ..quiz_engine import Question


def generate_depth_question(request: QuestionRequest) -> "Question":
    """Generate a depth-aware question without changing the legacy public API."""
    from ..quiz_engine import Question, generate_question

    spec = depth_spec_for(request.skill, request.subskill)
    if spec is None:
        question = generate_question(
            request.skill, request.level, request.question_type,
            subskill=request.subskill, preferred_mode=request.preferred_mode,
        )
        return _annotate_legacy(question)

    archetype = _select_archetype(spec.archetypes, request)
    if archetype.reasoning_kind is ReasoningKind.PROOF and spec.proof is not None:
        return Question(
            skill=request.skill,
            prompt=spec.proof.prompt,
            correct_answer=encode_proof_answer(tuple(step.step_id for step in spec.proof.required_steps)),
            explanation="Build the proof from valid statement-and-reason pairs in dependency order.",
            choices=None,
            visual=None,
            subskill=request.subskill,
            question_label="Proof",
            mode="application",
            archetype_id=archetype.archetype_id,
            reasoning_kind=ReasoningKind.PROOF,
            response_kind=ResponseKind.PROOF_BUILDER,
            misconceptions=_proof_misconceptions(spec),
            worked_example=spec.worked_example,
            proof_spec=spec.proof,
        )

    if spec.content_status is ContentStatus.READY:
        if not has_pilot_generator(request.skill, request.subskill):
            raise ValueError(f"Ready depth content has no authored generator: {request.skill}/{request.subskill}")
        return generate_pilot_question(request, spec, archetype)

    base = generate_question(
        request.skill, request.level, request.question_type,
        subskill=request.subskill, preferred_mode=request.preferred_mode,
    )
    candidates = _misconception_candidates(base.correct_answer, spec)
    common = dict(
        archetype_id=archetype.archetype_id,
        reasoning_kind=archetype.reasoning_kind,
        response_kind=ResponseKind.CHOICE if base.choices else ResponseKind.TYPED,
        misconceptions=candidates,
        worked_example=spec.worked_example,
    )
    if archetype.reasoning_kind is ReasoningKind.CONCEPTUAL:
        return _conceptual_question(base, archetype, common)
    if archetype.reasoning_kind is ReasoningKind.TRANSFER:
        wrong = candidates[0].expected_answer
        prompt = f"A learner answered {wrong!r} for this task: {base.prompt}\nFind the correct answer."
        return replace(base, prompt=prompt, question_label="Error Analysis", **common)
    if archetype.reasoning_kind is ReasoningKind.APPLICATION:
        return _application_question(base, archetype, common)
    return replace(base, question_label="Strategy", **common)


def match_misconception(question: "Question", answer: str) -> MisconceptionCandidate | None:
    from ..quiz_answers import is_correct_answer

    for candidate in question.misconceptions:
        if is_correct_answer(candidate.expected_answer, answer):
            return candidate
    return None


def _select_archetype(archetypes: tuple[ArchetypeSpec, ...], request: QuestionRequest) -> ArchetypeSpec:
    if request.preferred_archetype_id:
        preferred = next((item for item in archetypes if item.archetype_id == request.preferred_archetype_id), None)
        if preferred is not None and preferred.archetype_id not in request.excluded_archetype_ids:
            return preferred
    eligible = [item for item in archetypes if item.archetype_id not in request.excluded_archetype_ids]
    if not eligible:
        eligible = list(archetypes)
    if not eligible:
        raise ValueError(f"No depth archetypes for {request.skill}/{request.subskill}")
    return random.choice(eligible)


def _conceptual_question(
    base: "Question", archetype: ArchetypeSpec, common: dict[str, object]
) -> "Question":
    explanation = explanation_for(base.skill, base.subskill)
    correct = explanation.mental_model or base.explanation
    choices = None
    if base.choices is not None:
        raw = [correct, explanation.common_mistake, explanation.try_this, "Use an unrelated shortcut."]
        choices = _unique_choices(raw, correct)
    prompt = archetype.prompt_prefix or f"Which mental model best supports {base.subskill or base.skill}?"
    return replace(
        base,
        prompt=prompt,
        correct_answer=correct,
        explanation=f"Mental model: {correct}",
        choices=choices,
        visual=None,
        question_label="Concept",
        **common,
    )


def _application_question(
    base: "Question", archetype: ArchetypeSpec, common: dict[str, object]
) -> "Question":
    prefix = archetype.prompt_prefix or "Construct a useful mathematical model, then solve this real situation."
    model = _model_label(base.skill, base.subskill)
    prompt = f"{prefix}\n{base.prompt}\nState the model ({model}) and the result."
    correct = f"{model}; {base.correct_answer}"
    choices = None
    if base.choices is not None:
        choices = [f"{model}; {choice}" for choice in base.choices]
        if correct not in choices:
            choices = [correct, *choices[:3]]
        random.shuffle(choices)
    return replace(
        base,
        prompt=prompt,
        correct_answer=correct,
        choices=choices,
        mode="word",
        question_label="Application",
        **common,
    )


def _model_label(skill: str, subskill: str | None) -> str:
    if skill in {"data_displays", "data_analysis", "stats_percent", "stats_mean", "stats_probability"}:
        return "data display or probability model"
    if skill in {"geometry_shapes", "geometry_area", "measurement"}:
        return "labeled diagram"
    if skill in {"fractions", "ratios"}:
        return "bar, number-line, or ratio model"
    if skill in {"algebra_linear", "algebra_1", "pre_algebra"}:
        return "equation, table, or graph"
    if subskill and "money" in subskill.lower():
        return "money table"
    return "equation or drawing"


def _misconception_candidates(
    correct_answer: str, spec: DepthSpec
) -> tuple[MisconceptionCandidate, ...]:
    wrong_answers = _wrong_answers(correct_answer)
    candidates: list[MisconceptionCandidate] = []
    for index, misconception in enumerate(spec.misconceptions):
        candidates.append(
            MisconceptionCandidate(
                misconception.code,
                wrong_answers[index % len(wrong_answers)],
                misconception.feedback,
                misconception.hint,
                misconception.recovery_archetype_id,
            )
        )
    return tuple(candidates)


def _proof_misconceptions(spec: DepthSpec) -> tuple[MisconceptionCandidate, ...]:
    assert spec.proof is not None
    required = tuple(step.step_id for step in spec.proof.required_steps)
    distractor = spec.proof.distractor_steps[0].step_id if spec.proof.distractor_steps else "distractor"
    wrong = (
        json.dumps(list(reversed(required)), separators=(",", ":")),
        json.dumps([*required[:-1], distractor], separators=(",", ":")),
    )
    return tuple(
        MisconceptionCandidate(item.code, wrong[index % 2], item.feedback, item.hint, item.recovery_archetype_id)
        for index, item in enumerate(spec.misconceptions)
    )


def _wrong_answers(correct_answer: str) -> tuple[str, str]:
    cleaned = correct_answer.strip().replace("$", "")
    try:
        value = float(cleaned)
    except ValueError:
        if "/" in cleaned:
            left, _, right = cleaned.partition("/")
            if left and right:
                return (f"{right}/{left}", f"{left}/{max(1, int(float(right)) + 1)}")
        return ("not enough information", f"not {correct_answer}")
    first = _format_number(value + 1)
    second = _format_number(value - 1 if not math.isclose(value, 0.0) else value + 2)
    return first, second


def _format_number(value: float) -> str:
    if math.isclose(value, round(value)):
        return str(int(round(value)))
    return f"{value:.3f}".rstrip("0").rstrip(".")


def _unique_choices(raw: list[str], correct: str) -> list[str]:
    choices: list[str] = []
    for item in raw:
        value = item.strip()
        if value and value not in choices:
            choices.append(value)
    while len(choices) < 4:
        choices.append(f"Different idea {len(choices)}")
    random.shuffle(choices)
    if correct not in choices:
        choices[0] = correct
    return choices[:4]


def _annotate_legacy(question: "Question") -> "Question":
    response = ResponseKind.CHOICE if question.choices else ResponseKind.TYPED
    archetype_id = question.template_external_id or f"legacy.native.{question.skill}"
    return replace(question, archetype_id=archetype_id, response_kind=response)
