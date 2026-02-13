from __future__ import annotations

import random

from . import db
from .template_engine import instantiate_template, mc_choices


def try_generate_from_templates(skill: str, level: int, question_type: str, *, rng: random.Random):
    # Local import to avoid circular dependency with quiz_engine.
    from .quiz_engine import Question

    templates = db.list_question_templates(skill, level)
    if not templates:
        return None
    template = rng.choice(templates)
    vars_spec = db.list_template_vars(template.id)
    inst = instantiate_template(template, vars_spec, rng=rng)
    choices = None
    if question_type == "mc":
        if inst.numeric_answer is None:
            return None
        choices = mc_choices(inst.numeric_answer, spread=template.choice_spread, rng=rng)
    return Question(skill, inst.prompt, inst.answer, inst.explanation, choices, None)
