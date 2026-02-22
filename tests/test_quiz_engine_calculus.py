from __future__ import annotations

import unittest

from app.quiz_engine import generate_question


class QuizEngineCalculusTests(unittest.TestCase):
    def test_generate_calculus_1_question(self) -> None:
        q = generate_question("calculus_1", 1, "typed")
        self.assertEqual(q.skill, "calculus_1")
        self.assertTrue(q.correct_answer)

    def test_generate_calculus_2_question(self) -> None:
        q = generate_question("calculus_2", 2, "typed")
        self.assertEqual(q.skill, "calculus_2")
        self.assertTrue(q.correct_answer)

    def test_generate_calculus_3_question(self) -> None:
        q = generate_question("calculus_3", 2, "typed")
        self.assertEqual(q.skill, "calculus_3")
        self.assertTrue(q.correct_answer)

    def test_legacy_calculus_slope_alias_maps_to_calculus_1(self) -> None:
        q = generate_question("calculus_slope", 1, "typed")
        self.assertEqual(q.skill, "calculus_1")


if __name__ == "__main__":
    unittest.main()
