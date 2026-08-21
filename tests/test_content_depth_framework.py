from __future__ import annotations

import random
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app import db
from app.content_depth.audit import build_depth_audit
from app.content_depth.generation import generate_depth_question
from app.content_depth.models import ContentStatus, QuestionRequest, ReasoningKind
from app.content_depth.pilot_specs import PILOT_TARGETS
from app.content_depth.registry import IN_SCOPE_SKILLS, in_scope_pairs, load_depth_specs
from app.content_depth.report import generate_depth_review_report, render_depth_review_html
from app.content_depth.quiz_controller import DepthQuizController
from app.content_depth.recovery_controller import transfer_request
from app.ui_settings import UiSettings


class ContentDepthFrameworkTests(unittest.TestCase):
    def test_all_158_subskills_have_reviewable_depth_scaffolds(self) -> None:
        specs = load_depth_specs()
        self.assertEqual(len(IN_SCOPE_SKILLS), 26)
        self.assertEqual(len(in_scope_pairs()), 158)
        self.assertEqual(set(specs), set(in_scope_pairs()))
        for key, spec in specs.items():
            with self.subTest(target=key):
                kinds = {item.reasoning_kind for item in spec.archetypes}
                self.assertTrue(
                    {ReasoningKind.CONCEPTUAL, ReasoningKind.PROCEDURAL, ReasoningKind.TRANSFER} <= kinds
                )
                self.assertIn(ReasoningKind.APPLICATION, kinds)
                self.assertEqual(tuple(step.stage for step in spec.worked_example.steps), ("model", "guided", "transfer"))
                self.assertGreaterEqual(len(spec.misconceptions), 2)
                archetype_ids = {item.archetype_id for item in spec.archetypes}
                self.assertTrue(all(item.recovery_archetype_id in archetype_ids for item in spec.misconceptions))
        ready = {key for key, spec in specs.items() if spec.content_status is ContentStatus.READY}
        self.assertEqual(ready, set(PILOT_TARGETS))

    def test_packaging_includes_one_versioned_manifest_per_skill(self) -> None:
        root = Path(__file__).resolve().parents[1]
        manifests = sorted((root / "data" / "content_depth").glob("*.json"))
        self.assertEqual(len(manifests), 26)
        self.assertEqual({path.stem for path in manifests}, set(IN_SCOPE_SKILLS))
        self.assertIn('"data/content_depth"', (root / "mandelquest.spec").read_text(encoding="utf-8"))

    def test_ci_depth_audit_uses_25_deterministic_seeds_without_overstating_rollout(self) -> None:
        report = build_depth_audit(seeds_per_archetype=25)
        self.assertFalse(report.depth_ready)
        self.assertEqual(report.ready_count, 16)
        self.assertEqual(report.thin_count, 142)
        self.assertFalse(any(row.generation_failures for row in report.rows if row.readiness == "ready"))

    def test_exclusions_prevent_repetition_until_every_archetype_is_seen(self) -> None:
        target = ("fractions", "Equivalent fractions")
        spec = load_depth_specs()[target]
        seen: set[str] = set()
        random.seed(41)
        for _ in spec.archetypes:
            question = generate_depth_question(
                QuestionRequest(*target[:1], 2, "typed", target[1], excluded_archetype_ids=frozenset(seen))
            )
            self.assertNotIn(question.archetype_id, seen)
            self.assertIsNotNone(question.archetype_id)
            seen.add(str(question.archetype_id))
        self.assertEqual(seen, {item.archetype_id for item in spec.archetypes})

    def test_representative_application_requires_model_and_result(self) -> None:
        for skill, subskill in sorted(PILOT_TARGETS):
            spec = load_depth_specs()[(skill, subskill)]
            application = next(
                item for item in spec.archetypes if item.reasoning_kind is ReasoningKind.APPLICATION
            )
            question = generate_depth_question(
                QuestionRequest(skill, 2, "typed", subskill, preferred_archetype_id=application.archetype_id)
            )
            with self.subTest(target=(skill, subskill)):
                self.assertIn("model", question.prompt.lower())
                self.assertIn(";", question.correct_answer)
                self.assertNotIn("Construct a useful mathematical model, then solve", question.prompt)

    def test_runtime_controller_is_default_off_and_scaffolds_still_fall_back(self) -> None:
        controller = DepthQuizController()
        with patch(
            "app.content_depth.quiz_controller.load_ui_settings",
            return_value=UiSettings(),
        ):
            disabled_question = controller.generate(
                set(), "fractions", 1, "typed", subskill="Equivalent fractions", preferred_mode=None
            )
        with patch(
            "app.content_depth.quiz_controller.load_ui_settings",
            return_value=UiSettings(curriculum_depth_beta=True),
        ):
            question = controller.generate(
                set(), "counting", 1, "typed", subskill="Number recognition", preferred_mode=None
            )
            any_question = controller.generate(
                set(), "fractions", 1, "typed", subskill=None, preferred_mode=None
            )
        self.assertIsNone(disabled_question)
        self.assertIsNone(question)
        self.assertIsNone(any_question)

    def test_depth_review_renders_and_exports_the_ci_audit_counts(self) -> None:
        report = build_depth_audit(seeds_per_archetype=25)
        rendered = render_depth_review_html(report)
        self.assertIn("Ready: 16", rendered)
        self.assertIn("Thin: 142", rendered)
        self.assertIn("Missing: 0", rendered)
        self.assertIn("Total: 158", rendered)
        with tempfile.TemporaryDirectory() as tmp_dir:
            with patch("app.content_depth.report.build_depth_audit", return_value=report) as audit:
                path = generate_depth_review_report(Path(tmp_dir))
            audit.assert_called_once_with(seeds_per_archetype=25)
            self.assertEqual(path.parent, Path(tmp_dir))
            self.assertEqual(path.read_text(encoding="utf-8"), rendered)

    def test_first_launch_lesson_is_guided_then_three_independent_questions(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            with db.override_db_config(db.DbConfig(path=str(Path(tmp_dir) / "app.db"))):
                db.init_db()
                controller = DepthQuizController()
                with patch(
                    "app.content_depth.quiz_controller.load_ui_settings",
                    return_value=UiSettings(curriculum_depth_beta=True),
                ):
                    lesson = controller.prepare_first_lesson(
                        1, "child", "add_subtract", "Single-digit addition", "focused", 1, set()
                    )
                    parent_lesson = controller.prepare_first_lesson(
                        1, "parent", "add_subtract", "Single-digit addition", "focused", 1, set()
                    )
        self.assertIsNotNone(lesson)
        assert lesson is not None
        self.assertEqual(
            [question.question_label for question in lesson],
            ["Guided Check", "Independent 1", "Independent 2", "Independent 3"],
        )
        self.assertEqual(len({question.archetype_id for question in lesson}), 4)
        self.assertIsNone(parent_lesson)

    def test_recovery_transfer_uses_a_different_archetype(self) -> None:
        spec = load_depth_specs()[("fractions", "Equivalent fractions")]
        concept = next(item for item in spec.archetypes if item.reasoning_kind is ReasoningKind.CONCEPTUAL)
        source = generate_depth_question(
            QuestionRequest("fractions", 2, "mc", "Equivalent fractions", preferred_archetype_id=concept.archetype_id)
        )
        preferred, excluded = transfer_request(source)
        followup = generate_depth_question(
            QuestionRequest(
                "fractions", 2, "mc", "Equivalent fractions",
                preferred_archetype_id=preferred,
                excluded_archetype_ids=excluded,
            )
        )
        self.assertNotEqual(followup.archetype_id, source.archetype_id)
        self.assertEqual(followup.reasoning_kind, ReasoningKind.TRANSFER)


if __name__ == "__main__":
    unittest.main()
