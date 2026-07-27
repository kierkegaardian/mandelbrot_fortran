from __future__ import annotations

import random
import unittest

from app.content_depth.audit import build_depth_audit
from app.content_depth.generation import generate_depth_question
from app.content_depth.models import ContentStatus, QuestionRequest, ReasoningKind
from app.content_depth.registry import depth_spec_for
from app.texas_grade_goals import texas_grade_plan


TARGETS: tuple[tuple[str, str], ...] = (
    ("place_value", "Ones, tens, and hundreds identification"),
    ("place_value", "Compare numbers by place value"),
)


class ContentDepthPlaceValueTests(unittest.TestCase):
    def test_grade_one_place_value_goal_is_fully_depth_ready(self) -> None:
        goal = next(goal for goal in texas_grade_plan(1).goals if goal.code == "g1_place_value")
        self.assertEqual(tuple((str(goal.skill), subskill) for subskill in goal.subskills), TARGETS)
        for target in TARGETS:
            spec = depth_spec_for(*target)
            assert spec is not None
            with self.subTest(target=target):
                self.assertIs(spec.content_status, ContentStatus.READY)
                self.assertEqual(
                    tuple(step.stage for step in spec.worked_example.steps),
                    ("model", "guided", "transfer"),
                )
                self.assertEqual(len({step.prompt for step in spec.worked_example.steps}), 3)
                self.assertTrue(all(step.expected_answer for step in spec.worked_example.steps))

    def test_every_place_value_archetype_has_typed_and_choice_forms(self) -> None:
        for target in TARGETS:
            spec = depth_spec_for(*target)
            assert spec is not None
            for archetype in spec.archetypes:
                for question_type in ("typed", "mc"):
                    random.seed(f"{target}:{archetype.archetype_id}:{question_type}")
                    question = generate_depth_question(
                        QuestionRequest(
                            target[0],
                            1,
                            question_type,
                            target[1],
                            preferred_archetype_id=archetype.archetype_id,
                        )
                    )
                    with self.subTest(target=target, kind=archetype.reasoning_kind, form=question_type):
                        self.assertEqual(question.archetype_id, archetype.archetype_id)
                        self.assertEqual(question.reasoning_kind, archetype.reasoning_kind)
                        self.assertEqual(len(question.misconceptions), 2)
                        misconception_answers = {item.expected_answer for item in question.misconceptions}
                        self.assertNotIn(question.correct_answer, misconception_answers)
                        if question_type == "mc":
                            assert question.choices is not None
                            self.assertIn(question.correct_answer, question.choices)
                            self.assertTrue(misconception_answers <= set(question.choices))
                        if archetype.reasoning_kind is ReasoningKind.TRANSFER:
                            self.assertIn("learner", question.prompt.lower())
                            self.assertIn("correct", question.prompt.lower())
                        if archetype.reasoning_kind is ReasoningKind.APPLICATION:
                            self.assertIn("model", question.prompt.lower())
                            self.assertIn(";", question.correct_answer)

    def test_release_audit_promotes_only_the_two_authored_rows(self) -> None:
        report = build_depth_audit(seeds_per_archetype=25)
        rows = {(row.skill, row.subskill): row for row in report.rows}
        self.assertEqual((report.ready_count, report.thin_count, report.missing_count), (16, 142, 0))
        for target in TARGETS:
            with self.subTest(target=target):
                self.assertEqual(rows[target].readiness, "ready")
                self.assertEqual(rows[target].notes, ())


if __name__ == "__main__":
    unittest.main()
