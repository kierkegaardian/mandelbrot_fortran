from __future__ import annotations

import random

from . import db
from .template_engine import instantiate_template, mc_choices


def try_generate_from_templates(skill: str, level: int, question_type: str, *, rng: random.Random, subskill: str | None = None):
    # Local import to avoid circular dependency with quiz_engine.
    from .quiz_engine import Question

    templates = db.list_question_templates(skill, level, subskill=subskill)
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
                subskill=template.subskill,
            )
        except Exception:
            continue
    return None
