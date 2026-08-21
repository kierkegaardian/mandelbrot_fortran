from __future__ import annotations

import random
import sqlite3
import unittest
from unittest.mock import patch

from app.question_bank import try_generate_from_templates


class QuestionBankTests(unittest.TestCase):
    def test_uninitialized_schema_falls_back_without_crashing(self) -> None:
        with patch("app.question_bank.db.list_question_templates", side_effect=sqlite3.OperationalError("no such table")):
            result = try_generate_from_templates(
                "calculus_1",
                1,
                "typed",
                rng=random.Random(0),
            )
        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
