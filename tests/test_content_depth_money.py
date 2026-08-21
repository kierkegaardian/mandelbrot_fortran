from __future__ import annotations

import random
import re
import unittest

from app.content_depth.audit import build_depth_audit
from app.content_depth.cumulative import build_texas_cumulative_quiz
from app.content_depth.generation import generate_depth_question
from app.content_depth.models import ContentStatus, QuestionRequest, ReasoningKind
from app.content_depth.pilot_money import DENOMINATIONS, coin_values
from app.content_depth.registry import depth_spec_for
from app.texas_grade_goals import texas_grade_plan


TARGET = ("money", "Dollar-coin values")


class ContentDepthMoneyTests(unittest.TestCase):
    def test_grade_one_money_goal_is_depth_ready(self) -> None:
        goal = next(goal for goal in texas_grade_plan(1).goals if goal.code == "g1_money")
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

    def test_money_archetypes_have_typed_and_diagnostic_choice_forms(self) -> None:
        spec = depth_spec_for(*TARGET)
        assert spec is not None
        for archetype in spec.archetypes:
            for question_type in ("typed", "mc"):
                random.seed(f"money:{archetype.archetype_id}:{question_type}")
                question = generate_depth_question(
                    QuestionRequest(
                        TARGET[0], 1, question_type, TARGET[1],
                        preferred_archetype_id=archetype.archetype_id,
                    )
                )
                with self.subTest(kind=archetype.reasoning_kind, form=question_type):
                    self.assertEqual(question.reasoning_kind, archetype.reasoning_kind)
                    self.assertEqual(len(question.misconceptions), 2)
                    wrong = {item.expected_answer for item in question.misconceptions}
                    self.assertNotIn(question.correct_answer, wrong)
                    if question_type == "mc":
                        assert question.choices is not None
                        self.assertIn(question.correct_answer, question.choices)
                        self.assertTrue(wrong <= set(question.choices))
                    if archetype.reasoning_kind is ReasoningKind.TRANSFER:
                        self.assertIn("learner", question.prompt.lower())
                        self.assertIn("correct", question.prompt.lower())
                    if archetype.reasoning_kind is ReasoningKind.APPLICATION:
                        self.assertIn("model", question.prompt.lower())
                        self.assertIn(";", question.correct_answer)

    def test_grade_one_denominations_and_bounds_are_honest(self) -> None:
        seen: set[str] = set()
        for seed in range(100):
            random.seed(seed)
            concept = coin_values(ReasoningKind.CONCEPTUAL)
            seen.update(name for name, _ in DENOMINATIONS if name in concept.prompt)
            for kind in (ReasoningKind.PROCEDURAL, ReasoningKind.TRANSFER, ReasoningKind.APPLICATION):
                random.seed(f"{seed}:{kind.value}")
                problem = coin_values(kind)
                value = int(re.findall(r"\d+", problem.answer)[0])
                self.assertLessEqual(value, 100)
                self.assertNotIn("change", problem.prompt.lower())
                self.assertNotIn("budget", problem.prompt.lower())
        self.assertEqual(seen, {name for name, _ in DENOMINATIONS})

    def test_check_two_keeps_money_authored_after_personal_finance_promotion(self) -> None:
        money_questions = []
        for seed in range(100):
            quiz = build_texas_cumulative_quiz(1, 2, seed=seed)
            self.assertTrue(all(question.scaffold_steps is None for question in quiz.questions))
            self.assertTrue(
                all(question.reasoning_kind is not ReasoningKind.LEGACY for question in quiz.questions)
            )
            money_questions.extend(question for question in quiz.questions if question.skill == "money")
        self.assertTrue(money_questions)
        self.assertTrue(
            all(
                question.reasoning_kind in {ReasoningKind.PROCEDURAL, ReasoningKind.APPLICATION}
                for question in money_questions
            )
        )

    def test_audit_promotes_money_but_keeps_later_money_rows_thin(self) -> None:
        report = build_depth_audit(seeds_per_archetype=25)
        rows = {(row.skill, row.subskill): row for row in report.rows}
        self.assertEqual((report.ready_count, report.thin_count, report.missing_count), (16, 142, 0))
        self.assertEqual(rows[TARGET].readiness, "ready")
        for subskill in ("Making change", "Budget-style totals", "Place-value in currency"):
            with self.subTest(subskill=subskill):
                spec = depth_spec_for("money", subskill)
                assert spec is not None
                self.assertIs(spec.content_status, ContentStatus.SCAFFOLD)
                self.assertEqual(rows[("money", subskill)].readiness, "thin")


if __name__ == "__main__":
    unittest.main()
