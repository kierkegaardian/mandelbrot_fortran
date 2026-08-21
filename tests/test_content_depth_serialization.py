from __future__ import annotations

import unittest

from app.content_depth.generation import generate_depth_question
from app.content_depth.models import QuestionRequest, ReasoningKind
from app.content_depth.serialization import question_depth_kwargs, question_depth_payload
from app.content_depth.registry import load_depth_specs
from app.quiz_engine import Question


class ContentDepthSerializationTests(unittest.TestCase):
    def test_question_depth_round_trip_includes_example_and_misconceptions(self) -> None:
        spec = load_depth_specs()[("fractions", "Equivalent fractions")]
        transfer = next(item for item in spec.archetypes if item.reasoning_kind is ReasoningKind.TRANSFER)
        source = generate_depth_question(
            QuestionRequest("fractions", 2, "typed", "Equivalent fractions", preferred_archetype_id=transfer.archetype_id)
        )
        source.matched_misconception_code = source.misconceptions[0].code
        payload = question_depth_payload(source)
        restored = Question(
            source.skill,
            source.prompt,
            source.correct_answer,
            source.explanation,
            source.choices,
            source.visual,
            subskill=source.subskill,
            **question_depth_kwargs(payload),
        )
        self.assertEqual(restored.archetype_id, source.archetype_id)
        self.assertEqual(restored.reasoning_kind, ReasoningKind.TRANSFER)
        self.assertEqual(restored.misconceptions, source.misconceptions)
        self.assertEqual(restored.worked_example, source.worked_example)
        self.assertEqual(restored.matched_misconception_code, source.matched_misconception_code)

    def test_proof_spec_round_trip_keeps_dependencies_and_distractors(self) -> None:
        spec = load_depth_specs()[("geometry_area", "Triangle congruence criteria")]
        proof = next(item for item in spec.archetypes if item.reasoning_kind is ReasoningKind.PROOF)
        source = generate_depth_question(
            QuestionRequest(
                "geometry_area", 2, "typed", "Triangle congruence criteria",
                preferred_archetype_id=proof.archetype_id,
            )
        )
        kwargs = question_depth_kwargs(question_depth_payload(source))
        self.assertEqual(kwargs["proof_spec"], source.proof_spec)


if __name__ == "__main__":
    unittest.main()
