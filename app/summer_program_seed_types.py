from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SeedPattern:
    prompt_template: str
    answer_expr: str
    constraint_expr: str
    explanation_template: str
    vars: tuple[dict[str, object], ...]
    choice_spread: float = 6.0
