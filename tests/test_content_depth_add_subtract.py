from __future__ import annotations

import random
import unittest

from app.content_depth.audit import build_depth_audit
from app.content_depth.cumulative import build_texas_cumulative_quiz
from app.content_depth.generation import generate_depth_question
from app.content_depth.models import ContentStatus, QuestionRequest, ReasoningKind
from app.content_depth.registry import depth_spec_for
from app.texas_grade_goals import texas_grade_plan


NEW_TARGETS: tuple[tuple[str, str], ...] = (
    ("add_subtract", "Single-digit subtraction"),
    ("add_subtract", "Missing addends"),
    ("add_subtract", "Word problems"),
)


class ContentDepthAddSubtractTests(unittest.TestCase):
    def test_grade_one_add_subtract_goal_is_fully_depth_ready(self) -> None:
        goal = next(goal for goal in texas_grade_plan(1).goals if goal.code == "g1_add_subtract")
        self.assertEqual(
            goal.subskills,
            ("Single-digit addition", "Single-digit subtraction", "Missing addends", "Word problems"),
        )
        for subskill in goal.subskills:
            spec = depth_spec_for("add_subtract", subskill)
            assert spec is not None
            with self.subTest(subskill=subskill):
                self.assertIs(spec.content_status, ContentStatus.READY)
                self.assertEqual(
                    tuple(step.stage for step in spec.worked_example.steps),
                    ("model", "guided", "transfer"),
                )
                self.assertEqual(len({step.prompt for step in spec.worked_example.steps}), 3)
                self.assertTrue(all(step.expected_answer for step in spec.worked_example.steps))

    def test_new_archetypes_have_typed_and_diagnostic_choice_forms(self) -> None:
        for target in NEW_TARGETS:
            spec = depth_spec_for(*target)
            assert spec is not None
            for archetype in spec.archetypes:
                for question_type in ("typed", "mc"):
                    random.seed(f"{target}:{archetype.archetype_id}:{question_type}")
                    question = generate_depth_question(
                        QuestionRequest(
                            target[0], 1, question_type, target[1],
                            preferred_archetype_id=archetype.archetype_id,
                        )
                    )
                    with self.subTest(target=target, kind=archetype.reasoning_kind, form=question_type):
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
                            self.assertTrue(
                                any(word in question.prompt.lower() for word in ("diagnose", "correct"))
                            )
                        if archetype.reasoning_kind is ReasoningKind.APPLICATION:
                            self.assertIn("model", question.prompt.lower())
                            self.assertIn(";", question.correct_answer)

    def test_word_problems_cover_join_separate_and_compare_models(self) -> None:
        spec = depth_spec_for("add_subtract", "Word problems")
        assert spec is not None
        application = next(
            item for item in spec.archetypes if item.reasoning_kind is ReasoningKind.APPLICATION
        )
        models: set[str] = set()
        for seed in range(30):
            random.seed(seed)
            question = generate_depth_question(
                QuestionRequest(
                    "add_subtract", 1, "typed", "Word problems",
                    preferred_archetype_id=application.archetype_id,
                )
            )
            models.add(question.correct_answer.partition(";")[0].strip())
        self.assertEqual(models, {"joining addition", "take-away subtraction", "comparison subtraction"})

    def test_grade_one_cumulative_check_uses_depth_without_scaffolds(self) -> None:
        quiz = build_texas_cumulative_quiz(1, 1, seed=2)
        self.assertEqual(len(quiz.questions), 8)
        self.assertEqual(sum(q.reasoning_kind is ReasoningKind.PROCEDURAL for q in quiz.questions), 6)
        self.assertEqual(sum(q.reasoning_kind is ReasoningKind.APPLICATION for q in quiz.questions), 2)
        self.assertTrue(all(q.reasoning_kind is not ReasoningKind.LEGACY for q in quiz.questions))
        self.assertTrue(all(q.scaffold_steps is None for q in quiz.questions))

    def test_audit_promotes_three_rows_but_keeps_grade_two_regrouping_thin(self) -> None:
        report = build_depth_audit(seeds_per_archetype=25)
        rows = {(row.skill, row.subskill): row for row in report.rows}
        self.assertEqual((report.ready_count, report.thin_count, report.missing_count), (16, 142, 0))
        for target in NEW_TARGETS:
            self.assertEqual(rows[target].readiness, "ready")
        for subskill in ("Borrowing and carrying basics", "Multi-digit regrouping"):
            with self.subTest(subskill=subskill):
                spec = depth_spec_for("add_subtract", subskill)
                assert spec is not None
                self.assertIs(spec.content_status, ContentStatus.SCAFFOLD)
                self.assertEqual(rows[("add_subtract", subskill)].readiness, "thin")


if __name__ == "__main__":
    unittest.main()
