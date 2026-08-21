from __future__ import annotations

import json
import random
import tempfile
import unittest
from pathlib import Path

from app import db
from app.content_depth.template_metadata import TemplateMetadataError, validate_misconceptions_json
from app.question_bank import try_generate_from_templates


class ContentDepthTemplateTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        path = Path(self._tmp.name) / "app.db"
        self.enterContext(db.override_db_config(db.DbConfig(path=str(path))))
        db.init_db()

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_safe_misconception_expression_becomes_meaningful_distractor(self) -> None:
        metadata = json.dumps(
            [
                {
                    "code": "subtract_instead",
                    "answer_expr": "a - b",
                    "feedback": "You subtracted instead of joining the groups.",
                    "hint": "Model both groups together.",
                    "recovery_archetype_id": "depth.v1.add_subtract.single_digit_addition.concept",
                }
            ]
        )
        template_id = db.create_question_template(
            book_id=None,
            external_id="test.depth.add",
            skill="add_subtract",
            subskill="Single-digit addition",
            label="Diagnostic addition",
            mode="expression",
            prompt_template="{a} + {b} = ?",
            answer_expr="a + b",
            constraint_expr="a > b",
            explanation_template="Join {a} and {b}.",
            min_level=1,
            max_level=3,
            choice_spread=3,
            active=True,
            created_at="2026-07-14T00:00:00+00:00",
            archetype_id="depth.v1.add_subtract.single_digit_addition.procedure",
            reasoning_kind="procedural",
            misconceptions_json=metadata,
        )
        db.add_template_var(template_id, "a", "int", 5, 9, 1)
        db.add_template_var(template_id, "b", "int", 1, 4, 1)
        question = try_generate_from_templates(
            "add_subtract", 1, "mc", rng=random.Random(7), subskill="Single-digit addition"
        )
        self.assertIsNotNone(question)
        assert question is not None and question.choices is not None
        self.assertEqual(question.archetype_id, "depth.v1.add_subtract.single_digit_addition.procedure")
        self.assertEqual(len(question.misconceptions), 1)
        self.assertIn(question.misconceptions[0].expected_answer, question.choices)

    def test_unsafe_or_incomplete_misconception_json_is_rejected(self) -> None:
        unsafe = json.dumps(
            [{
                "code": "unsafe",
                "answer_expr": "__import__('os').system('echo no')",
                "feedback": "No.",
                "hint": "Retry.",
                "recovery_archetype_id": "depth.x",
            }]
        )
        with self.assertRaises(TemplateMetadataError):
            validate_misconceptions_json(unsafe)
        with self.assertRaises(TemplateMetadataError):
            validate_misconceptions_json('[{"code":"missing"}]')


if __name__ == "__main__":
    unittest.main()
