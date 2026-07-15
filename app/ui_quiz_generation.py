"""Mode selection, variation, and stable question identity helpers."""

from __future__ import annotations

import hashlib
import random

from . import db
from .learning_engine import (
    ModeMix,
    apply_word_gap_boost,
    default_mode_mix_for_stage,
    normalize_mode_mix,
)
from .quiz_engine import Question, generate_question
from .skill_graph import subskills_for
from .story_wrapper import apply_story_wrapper, can_wrap_skill


class QuizGenerationMixin:
    def _mode_mix_for_skill(
        self,
        profile_id: int,
        skill: str,
        skill_stats,
        mode_acc_cache: dict[str, dict[str, float]],
        override: tuple[int, int, int] | None,
    ) -> ModeMix:
        if override is not None:
            return normalize_mode_mix(override[0], override[1], override[2])
        base = default_mode_mix_for_stage(skill_stats.get(skill))
        if skill not in mode_acc_cache:
            mode_acc_cache[skill] = db.mode_accuracy_by_skill(profile_id, skill)
        mode_acc = mode_acc_cache[skill]
        boosted = apply_word_gap_boost(base, mode_acc.get("expression"), mode_acc.get("word"))
        if not can_wrap_skill(skill):
            return normalize_mode_mix(boosted.intuition, boosted.expression + boosted.word, 0)
        return boosted

    def _apply_mode_preference(self, question: Question, preferred_mode: str | None) -> Question:
        if preferred_mode == "intuition":
            if question.visual is not None:
                question.mode = "intuition"
            return question
        if preferred_mode == "word":
            if question.mode == "word":
                return question
            if can_wrap_skill(question.skill):
                return apply_story_wrapper(question, rng=random)
            return question
        if preferred_mode == "expression" and question.mode != "word":
            question.mode = "expression"
        return question

    def _pick_mode(self, mix: ModeMix, skill: str) -> str:
        labels = ["intuition", "expression", "word"]
        weights = [mix.intuition, mix.expression, mix.word]
        if not can_wrap_skill(skill):
            weights[1] += weights[2]
            weights[2] = 0
        if sum(weights) <= 0:
            return "expression"
        return random.choices(labels, weights=weights, k=1)[0]

    def _mode_mix_label(self, mix: ModeMix) -> str:
        return f"{mix.intuition}/{mix.expression}/{mix.word}"

    def _generate_question_with_variation(
        self,
        seen_signatures: set[str],
        skill: str,
        level: int,
        question_type: str,
        *,
        subskill: str | None,
        preferred_mode: str | None,
    ) -> Question:
        if not self.vary_numbers_var.get():
            q = generate_question(skill, level, question_type, subskill=subskill, preferred_mode=preferred_mode)
            seen_signatures.add(_question_session_signature(q))
            return q
        last_q: Question | None = None
        for _ in range(10):
            q = generate_question(skill, level, question_type, subskill=subskill, preferred_mode=preferred_mode)
            sig = _question_session_signature(q)
            last_q = q
            if sig not in seen_signatures:
                seen_signatures.add(sig)
                return q
        assert last_q is not None
        seen_signatures.add(_question_session_signature(last_q))
        return last_q


def _subskill_for_question(question: Question) -> str:
    if getattr(question, "subskill", None):
        return str(question.subskill)
    subskills = subskills_for(question.skill)
    if not subskills:
        return "core"
    seed = _question_identity_seed(question)
    digest = hashlib.sha1(seed.encode("utf-8")).hexdigest()
    index = int(digest[:10], 16) % len(subskills)
    return subskills[index]


def _question_identity_seed(question: Question) -> str:
    # Keep fallback subskill mapping stable across quiz contexts (Core/Prereq/Review)
    # and wrapper styles (word vs expression) when the underlying math item is the same.
    if question.template_external_id:
        return f"{question.skill}|template_external:{question.template_external_id}"
    if question.template_id is not None:
        return f"{question.skill}|template:{int(question.template_id)}"
    prompt = question.prompt
    marker = "\nQuestion: "
    if marker in prompt:
        prompt = prompt.split(marker, 1)[1]
    prompt = " ".join(prompt.split())
    return f"{question.skill}|prompt:{prompt}|answer:{question.correct_answer}"


def _template_family(question: Question) -> str:
    external_id = getattr(question, "template_external_id", None)
    if external_id:
        parts = str(external_id).split(".")
        if len(parts) >= 3:
            return ".".join(parts[:-1])
        return str(external_id)
    template_id = getattr(question, "template_id", None)
    if template_id is not None:
        return f"id:{int(template_id)}"
    return ""


def _question_session_signature(question: Question) -> str:
    prompt = " ".join(str(question.prompt).split())
    answer = str(question.correct_answer)
    return f"{question.skill}|{question.mode}|{prompt}|{answer}"


def _subskill_coverage_by_skill(profile_id: int) -> dict[str, float]:
    progress = db.list_subskill_progress(profile_id)
    by_skill: dict[str, dict[str, int]] = {}
    for item in progress:
        if item.skill not in by_skill:
            by_skill[item.skill] = {"mastered": 0, "total": 0}
        by_skill[item.skill]["total"] += 1
        if item.mastered:
            by_skill[item.skill]["mastered"] += 1
    out: dict[str, float] = {}
    for skill, counts in by_skill.items():
        out[skill] = float(counts["mastered"]) / float(max(1, counts["total"]))
    return out
