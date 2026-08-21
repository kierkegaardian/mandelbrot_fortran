from __future__ import annotations

import unittest

from app.content_depth.printable import blank_proof_table, completed_proof_table
from app.content_depth.proof import decode_proof_answer, encode_proof_answer, grade_proof
from app.content_depth.registry import PROOF_SUBSKILLS, load_depth_specs


class ContentDepthProofTests(unittest.TestCase):
    def test_all_required_geometry_proofs_have_steps_and_distractors(self) -> None:
        proof_specs = [spec for spec in load_depth_specs().values() if spec.subskill in PROOF_SUBSKILLS]
        self.assertEqual(len(proof_specs), 5)
        for spec in proof_specs:
            assert spec.proof is not None
            with self.subTest(subskill=spec.subskill):
                self.assertGreaterEqual(len(spec.proof.required_steps), 4)
                self.assertGreaterEqual(len(spec.proof.distractor_steps), 2)

    def test_grader_accepts_alternative_valid_topological_orders(self) -> None:
        spec = next(
            item.proof for item in load_depth_specs().values() if item.subskill == "Triangle congruence criteria"
        )
        assert spec is not None
        first = ("side_one", "angle", "side_two", "conclusion")
        alternative = ("side_two", "side_one", "angle", "conclusion")
        self.assertTrue(grade_proof(spec, first).correct)
        self.assertTrue(grade_proof(spec, alternative).correct)

    def test_grader_rejects_missing_wrong_order_and_distractor(self) -> None:
        spec = next(
            item.proof for item in load_depth_specs().values() if item.subskill == "Transformations and congruence"
        )
        assert spec is not None
        missing = grade_proof(spec, ("map", "length", "conclusion"))
        wrong_order = grade_proof(spec, ("map", "conclusion", "length", "angle"))
        distractor = grade_proof(spec, ("map", "length", "angle", spec.distractor_steps[0].step_id, "conclusion"))
        duplicate = grade_proof(spec, ("map", "length", "angle", "angle", "conclusion"))
        self.assertFalse(missing.correct)
        self.assertTrue(missing.missing_step_ids)
        self.assertFalse(wrong_order.correct)
        self.assertTrue(wrong_order.dependency_errors)
        self.assertFalse(distractor.correct)
        self.assertTrue(distractor.distractor_step_ids)
        self.assertFalse(duplicate.correct)

    def test_proof_resume_encoding_and_print_tables(self) -> None:
        spec = next(item.proof for item in load_depth_specs().values() if item.proof is not None)
        assert spec is not None
        step_ids = tuple(step.step_id for step in spec.required_steps)
        self.assertEqual(decode_proof_answer(encode_proof_answer(step_ids)), step_ids)
        blank = blank_proof_table(spec)
        completed = completed_proof_table(spec)
        self.assertEqual(blank.count("<tr>"), len(spec.required_steps) + 1)
        self.assertIn(spec.required_steps[0].statement, completed)
        self.assertIn(spec.required_steps[0].reason, completed)


if __name__ == "__main__":
    unittest.main()
