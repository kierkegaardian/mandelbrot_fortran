from __future__ import annotations

from collections import defaultdict
import random
import unittest

from app.content_depth.audit import build_depth_audit
from app.content_depth.cumulative import build_texas_cumulative_quiz
from app.content_depth.generation import generate_depth_question
from app.content_depth.models import ContentStatus, QuestionRequest, ReasoningKind
from app.content_depth.pilot_income_gifts import (
    PURPOSE_CASES,
    ROLE_SKILLS,
    income_gifts_wants_needs,
)
from app.content_depth.registry import depth_spec_for
from app.financial_literacy import FINANCIAL_LITERACY_SUBSKILLS
from app.texas_grade_goals import texas_grade_plan
from app.ui_arithmetic import khan_url_for_selection, lesson_link_state
from app.ui_settings import UiSettings


TARGET = ("financial_literacy", "Income, gifts, wants, and needs")
ADVANCED_READY = "Budget percentages, net worth, interest, and incentives"


class ContentDepthIncomeGiftsTests(unittest.TestCase):
    def test_grade_one_personal_finance_goal_is_depth_ready(self) -> None:
        goal = next(goal for goal in texas_grade_plan(1).goals if goal.code == "g1_personal_finance")
        self.assertEqual((str(goal.skill), *goal.subskills), TARGET)
        spec = depth_spec_for(*TARGET)
        assert spec is not None
        self.assertIs(spec.content_status, ContentStatus.READY)
        self.assertEqual(
            tuple(step.stage for step in spec.worked_example.steps),
            ("model", "guided", "transfer"),
        )
        self.assertEqual(len({step.prompt for step in spec.worked_example.steps}), 3)
        self.assertTrue(all(step.expected_answer for step in spec.worked_example.steps))

    def test_archetypes_have_typed_and_answer_keyed_choice_forms(self) -> None:
        spec = depth_spec_for(*TARGET)
        assert spec is not None
        self.assertEqual(
            tuple(item.code for item in spec.misconceptions),
            ("gift_as_income", "context_need_want"),
        )
        for archetype in spec.archetypes:
            for question_type in ("typed", "mc"):
                for seed in range(8):
                    random.seed(f"income-gifts:{archetype.archetype_id}:{question_type}:{seed}")
                    question = generate_depth_question(
                        QuestionRequest(
                            TARGET[0],
                            1,
                            question_type,
                            TARGET[1],
                            preferred_archetype_id=archetype.archetype_id,
                        )
                    )
                    with self.subTest(
                        kind=archetype.reasoning_kind, form=question_type, seed=seed
                    ):
                        self.assertEqual(question.reasoning_kind, archetype.reasoning_kind)
                        self.assertEqual(len(question.misconceptions), 2)
                        wrong = tuple(item.expected_answer for item in question.misconceptions)
                        self.assertEqual(len(set(wrong)), 2)
                        self.assertNotIn(question.correct_answer, wrong)
                        if question_type == "mc":
                            assert question.choices is not None
                            self.assertIn(question.correct_answer, question.choices)
                            self.assertTrue(set(wrong) <= set(question.choices))
                        if archetype.reasoning_kind is ReasoningKind.TRANSFER:
                            self.assertIn("learner", question.prompt.lower())
                            self.assertIn("correct", question.prompt.lower())
                        if archetype.reasoning_kind is ReasoningKind.APPLICATION:
                            self.assertIn("model", question.prompt.lower())
                            self.assertIn(";", question.correct_answer)
                            assert question.choices is not None or question_type == "typed"
                            if question.choices is not None:
                                models = {
                                    choice.partition(";")[0].strip()
                                    for choice in question.choices
                                    if ";" in choice
                                }
                                self.assertGreaterEqual(len(models), 2)

    def test_seed_pool_covers_three_axes_without_later_grade_content(self) -> None:
        seen_axes: set[str] = set()
        seen_labels: set[str] = set()
        seen_skills: set[str] = set()
        banned = ("interest", "tax", "profit", "credit", "budget", "weekly", "salary", "wage")
        moralizing = ("selfish", "bad want", "irresponsible", "always a need", "always a want")
        for seed in range(100):
            for kind in ReasoningKind.CONCEPTUAL, ReasoningKind.PROCEDURAL, ReasoningKind.APPLICATION:
                random.seed(f"{seed}:{kind.value}")
                problem = income_gifts_wants_needs(kind)
                content = f"{problem.prompt} {problem.answer} {problem.explanation}".lower()
                if "source" in content or "income-or-gift" in content:
                    seen_axes.add("source")
                if "purpose" in content or "need-want" in content:
                    seen_axes.add("purpose")
                if "job-skill" in content or "useful skill" in content:
                    seen_axes.add("skill")
                result = problem.answer.rpartition("; ")[2]
                if result in {"income", "gift", "need", "want"}:
                    seen_labels.add(result)
                seen_skills.update(item.skill for item in ROLE_SKILLS if item.skill in problem.answer)
                self.assertFalse(any(term in content for term in banned))
                self.assertFalse(any(term in content for term in moralizing))
                if result in {"need", "want"}:
                    self.assertTrue(any(case.context in problem.prompt for case in PURPOSE_CASES))
        self.assertEqual(seen_axes, {"source", "purpose", "skill"})
        self.assertEqual(seen_labels, {"income", "gift", "need", "want"})
        self.assertEqual(seen_skills, {item.skill for item in ROLE_SKILLS})

    def test_same_items_can_be_needs_or_wants_from_context(self) -> None:
        answers_by_item: dict[str, set[str]] = defaultdict(set)
        for case in PURPOSE_CASES:
            self.assertTrue(case.context)
            answers_by_item[case.item].add(case.answer)
        self.assertTrue(answers_by_item)
        self.assertTrue(all(answers == {"need", "want"} for answers in answers_by_item.values()))

    def test_external_lesson_link_remains_parent_controlled(self) -> None:
        disabled = lesson_link_state(
            *TARGET,
            UiSettings(show_external_links=False, enforce_offline_mode=False),
        )
        enabled = lesson_link_state(
            *TARGET,
            UiSettings(show_external_links=True, enforce_offline_mode=False),
        )
        self.assertFalse(disabled.enabled)
        self.assertTrue(enabled.enabled)
        self.assertEqual(khan_url_for_selection(*TARGET), enabled.url)

    def test_grade_one_cumulative_windows_preserve_authorship_and_honesty(self) -> None:
        personal_finance_questions = []
        saw_check_three_legacy = False
        for seed in range(100):
            check_two = build_texas_cumulative_quiz(1, 2, seed=seed)
            self.assertTrue(all(question.scaffold_steps is None for question in check_two.questions))
            self.assertTrue(
                all(question.reasoning_kind is not ReasoningKind.LEGACY for question in check_two.questions)
            )
            personal_finance_questions.extend(
                question for question in check_two.questions if question.skill == TARGET[0]
            )

            check_three = build_texas_cumulative_quiz(1, 3, seed=seed)
            self.assertTrue(all(question.scaffold_steps is None for question in check_three.questions))
            saw_check_three_legacy = saw_check_three_legacy or any(
                question.reasoning_kind is ReasoningKind.LEGACY for question in check_three.questions
            )
        self.assertTrue(personal_finance_questions)
        self.assertTrue(saw_check_three_legacy)
        self.assertTrue(
            all(
                question.reasoning_kind in {ReasoningKind.PROCEDURAL, ReasoningKind.APPLICATION}
                for question in personal_finance_questions
            )
        )

    def test_audit_promotes_target_without_overstating_finance_siblings(self) -> None:
        report = build_depth_audit(seeds_per_archetype=25)
        rows = {(row.skill, row.subskill): row for row in report.rows}
        self.assertEqual((report.ready_count, report.thin_count, report.missing_count), (16, 142, 0))
        self.assertEqual(rows[TARGET].readiness, "ready")
        self.assertEqual(rows[(TARGET[0], ADVANCED_READY)].readiness, "ready")
        for subskill in FINANCIAL_LITERACY_SUBSKILLS:
            if subskill in {TARGET[1], ADVANCED_READY}:
                continue
            with self.subTest(subskill=subskill):
                spec = depth_spec_for(TARGET[0], subskill)
                assert spec is not None
                self.assertIs(spec.content_status, ContentStatus.SCAFFOLD)
                self.assertEqual(rows[(TARGET[0], subskill)].readiness, "thin")


if __name__ == "__main__":
    unittest.main()
