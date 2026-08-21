from __future__ import annotations

import unittest

from scripts.ingest_open_textbook_wordproblems import (
    extract_answer_key_map,
    extract_word_problem_candidates,
)


class OpenTextbookIngestTests(unittest.TestCase):
    def test_extract_answer_key_map(self) -> None:
        text = """
        Chapter Exercises

        Answer Key
        1. C
        2) 14
        3 - 7/2
        """
        out = extract_answer_key_map(text)
        self.assertEqual(out.get(1), "C")
        self.assertEqual(out.get(2), "14")
        self.assertEqual(out.get(3), "7/2")

    def test_extract_word_problem_candidates_filters_short_blocks(self) -> None:
        text = """
        1. 3 + 4 = ?

        2. A train travels 120 miles in 3 hours. What is the average speed in miles per hour?

        3. Compute 5 * 9.
        """
        out = extract_word_problem_candidates(text, min_words=8)
        self.assertEqual(len(out), 1)
        qnum, body = out[0]
        self.assertEqual(qnum, 2)
        self.assertIn("average speed", body.lower())


if __name__ == "__main__":
    unittest.main()
