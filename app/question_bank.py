from __future__ import annotations

import random
import sqlite3
import json

from . import db
from .content_depth.models import MisconceptionCandidate, ReasoningKind, ResponseKind
from .template_engine import evaluate_diagnostic_answer, instantiate_template, mc_choices


def try_generate_from_templates(
    skill: str,
    level: int,
    question_type: str,
    *,
    rng: random.Random,
    subskill: str | None = None,
    mode: str | None = None,
):
    # Local import to avoid circular dependency with quiz_engine.
    from .quiz_engine import Question

    try:
        templates = db.list_question_templates(skill, level, subskill=subskill, mode=mode)
    except sqlite3.OperationalError:
        # If DB schema is not initialized yet, fall back to generator logic.
        return None
    if not templates:
        return None
    # Try a few templates; constraints or eval errors should not crash the app.
    candidates = list(templates)
    rng.shuffle(candidates)
    for template in candidates[: min(12, len(candidates))]:
        try:
            vars_spec = db.list_template_vars(template.id)
            inst = instantiate_template(template, vars_spec, rng=rng)
            choices = None
            if question_type == "mc":
                if inst.numeric_answer is None:
                    continue
                choices = mc_choices(inst.numeric_answer, spread=template.choice_spread, rng=rng)
                diagnostic_choices = [item.expected_answer for item in _template_misconceptions(template, inst.values)]
                choices = _merge_diagnostic_choices(inst.answer, diagnostic_choices, choices, rng=rng)
            misconceptions = _template_misconceptions(template, inst.values)
            try:
                reasoning_kind = ReasoningKind(template.reasoning_kind)
            except ValueError:
                reasoning_kind = ReasoningKind.LEGACY
            return Question(
                skill,
                inst.prompt,
                inst.answer,
                inst.explanation,
                choices,
                None,
                template_id=template.id,
                template_external_id=template.external_id,
                subskill=template.subskill,
                mode=template.mode,
                archetype_id=template.archetype_id or template.external_id,
                reasoning_kind=reasoning_kind,
                response_kind=ResponseKind.CHOICE if choices else ResponseKind.TYPED,
                misconceptions=misconceptions,
            )
        except Exception:
            continue
    return None


def _template_misconceptions(template, values: dict[str, float]) -> tuple[MisconceptionCandidate, ...]:
    try:
        raw = json.loads(template.misconceptions_json or "[]")
    except json.JSONDecodeError:
        return ()
    if not isinstance(raw, list):
        return ()
    out: list[MisconceptionCandidate] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        try:
            expected = evaluate_diagnostic_answer(str(item["answer_expr"]), values)
        except (KeyError, ValueError, ZeroDivisionError, OverflowError):
            continue
        out.append(
            MisconceptionCandidate(
                code=str(item.get("code", "template_misconception")),
                expected_answer=expected,
                feedback=str(item.get("feedback", "That answer follows a common setup error.")),
                hint=str(item.get("hint", "Recheck the model before calculating.")),
                recovery_archetype_id=str(item.get("recovery_archetype_id", template.archetype_id or "")),
            )
        )
    return tuple(out)


def _merge_diagnostic_choices(
    correct: str,
    diagnostics: list[str],
    fallback: list[str],
    *,
    rng: random.Random,
) -> list[str]:
    choices = [correct]
    for value in [*diagnostics, *fallback]:
        if value not in choices:
            choices.append(value)
        if len(choices) >= 4:
            break
    rng.shuffle(choices)
    return choices
