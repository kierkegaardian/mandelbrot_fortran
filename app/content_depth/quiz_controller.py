from __future__ import annotations

from .. import db
from ..quiz_engine import Question
from ..ui_settings import load_ui_settings
from .example_ui import worked_example_text
from .generation import generate_depth_question
from .models import ContentStatus, QuestionRequest, ReasoningKind
from .registry import depth_spec_for


class DepthQuizController:
    """Own depth-only quiz state so the legacy Tk panel stays an adapter."""

    def __init__(self) -> None:
        self._seen: dict[tuple[str, str], set[str]] = {}
        self.first_lesson = False

    def reset(self) -> None:
        self._seen.clear()
        self.first_lesson = False

    def generate(
        self,
        seen_signatures: set[str],
        skill: str,
        level: int,
        question_type: str,
        *,
        subskill: str | None,
        preferred_mode: str | None,
        preferred_archetype_id: str | None = None,
        excluded_archetype_ids: frozenset[str] = frozenset(),
    ) -> Question | None:
        if not load_ui_settings().curriculum_depth_beta:
            return None
        target = subskill
        if target is None:
            # An "Any" launch must preserve the established mixed-subskill
            # behavior rather than collapsing the whole skill to one pilot.
            return None
        spec = depth_spec_for(skill, target)
        if spec is None or spec.content_status is not ContentStatus.READY or target is None:
            return None
        key = (skill, target)
        used = self._seen.setdefault(key, set())
        eligible_ids = {item.archetype_id for item in spec.archetypes}
        if eligible_ids and eligible_ids.issubset(used):
            used.clear()
        question = generate_depth_question(
            QuestionRequest(
                skill, level, question_type, target, preferred_mode, preferred_archetype_id,
                frozenset(used) | excluded_archetype_ids,
            )
        )
        if question.archetype_id:
            used.add(question.archetype_id)
        seen_signatures.add(_signature(question))
        return question

    def prepare_first_lesson(
        self,
        profile_id: int,
        profile_role: str,
        skill: str,
        subskill: str | None,
        strategy: str,
        level: int,
        seen_signatures: set[str],
    ) -> list[Question] | None:
        spec = depth_spec_for(skill, subskill) if subskill is not None else None
        if (
            not load_ui_settings().curriculum_depth_beta
            or profile_role != "child"
            or strategy != "focused"
            or spec is None
            or spec.content_status is not ContentStatus.READY
            or any(row.subskill == subskill for row in db.list_subskill_progress(profile_id, skill))
        ):
            self.first_lesson = False
            return None
        by_kind = {item.reasoning_kind: item.archetype_id for item in spec.archetypes}
        sequence = (
            (ReasoningKind.PROCEDURAL, "Guided Check", "mc"),
            (ReasoningKind.CONCEPTUAL, "Independent 1", "typed"),
            (ReasoningKind.TRANSFER, "Independent 2", "mc"),
            (ReasoningKind.APPLICATION, "Independent 3", "typed"),
        )
        self._seen.pop((skill, subskill), None)
        questions: list[Question] = []
        for kind, label, question_type in sequence:
            question = self.generate(
                seen_signatures, skill, level, question_type, subskill=subskill, preferred_mode=None,
                preferred_archetype_id=by_kind.get(kind),
            )
            if question is None:
                return None
            question.question_label = label
            questions.append(question)
        self.first_lesson = True
        return questions

    def example_text(self, question: Question | None) -> str:
        return worked_example_text(question.worked_example) if question is not None else ""

    def show_example(self, panel) -> None:
        question = panel._current_recovery_question() if panel._recovery_active() else (
            panel._questions[panel._index] if panel._questions else None
        )
        if question is not None and question.worked_example is not None:
            panel.recovery_var.set(self.example_text(question))


def _signature(question: Question) -> str:
    prompt = " ".join(str(question.prompt).split())
    return f"{question.skill}|{question.mode}|{prompt}|{question.correct_answer}"
