from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PilotProblem:
    prompt: str
    answer: str
    explanation: str
    wrong_answers: tuple[str, str]
