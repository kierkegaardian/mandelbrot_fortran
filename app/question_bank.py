from __future__ import annotations

import random
import sqlite3

from . import db
from .template_engine import instantiate_template, mc_choices


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
            )
        except Exception:
            continue
    return None
