from __future__ import annotations

import json
import tkinter as tk
import unittest
from unittest.mock import patch

from app import db, ui_settings
from app.quiz_engine import Question
from app.time_utils import now_iso
from tests.tk_test_utils import TkAppTestCase, tk_available


@unittest.skipUnless(tk_available(), "Tk display unavailable")
class QuizContinuityUiTests(TkAppTestCase):
    def setUp(self) -> None:
        super().setUp()
        db.reset_db_config()
        db.init_db()
        self.child = db.create_profile("Resume Child", "child", now_iso())

    def tearDown(self) -> None:
        db.reset_db_config()
        super().tearDown()

    def _panel(self):
        from app.ui_quiz import QuizPanel

        root = self._new_root(withdraw=True)
        controls = tk.Frame(root)
        view = tk.Frame(root)
        return root, QuizPanel(controls, view, lambda: self.child)

    def _question(self, prompt: str = "8 + 5 = ?") -> Question:
        return Question(
            skill="add_subtract",
            prompt=prompt,
            correct_answer="13",
            explanation="Add the two values.",
            choices=None,
            visual=None,
            subskill="Within 20",
        )

    def _seed_in_progress(self, panel, *, answered: bool = True) -> int:
        question = self._question()
        panel._questions = [question]
        panel._attempt_skill = question.skill
        panel._index = 0
        panel._score = 1 if answered else 0
        panel._answers = [(question, "13", True)] if answered else []
        panel._show_question()
        panel._persist_quiz_progress()
        assert panel._quiz_progress_attempt_id is not None
        return panel._quiz_progress_attempt_id

    def test_valid_progress_resumes_and_discard_clears(self) -> None:
        _first_root, first = self._panel()
        attempt_id = self._seed_in_progress(first)

        _resume_root, resumed = self._panel()
        self._askyesno_answers.append(True)
        resumed.on_module_activated()
        self.assertEqual(attempt_id, resumed._quiz_progress_attempt_id)
        self.assertEqual("8 + 5 = ?", resumed._questions[0].prompt)
        self.assertEqual(1, resumed._score)
        self.assertTrue(resumed.next_btn.instate(["!disabled"]))

        resumed._resume_checked_profile_id = None
        resumed._quiz_progress_attempt_id = None
        self._askyesno_answers.append(False)
        resumed.on_module_activated()
        self.assertIsNone(db.load_quiz_progress(self.child.id))

    def test_malformed_progress_is_discarded_without_constructing_questions(self) -> None:
        db.save_quiz_progress(
            self.child.id,
            None,
            0,
            json.dumps({"version": 1, "questions": [{"skill": 7}]}),
            now_iso(),
        )
        _root, panel = self._panel()
        panel.on_module_activated()
        self.assertEqual([], panel._questions)
        self.assertIsNone(db.load_quiz_progress(self.child.id))
        self.assertTrue(self._messagebox_warnings)

    def test_atomic_failure_keeps_resume_then_success_clears_it(self) -> None:
        _root, panel = self._panel()
        attempt_id = self._seed_in_progress(panel)
        with patch(
            "app.ui_quiz_completion.sync_service.record_completed_quiz",
            side_effect=RuntimeError("injected completion failure"),
        ):
            panel._finish_quiz()
        self.assertEqual(attempt_id, db.load_quiz_progress(self.child.id)[0])
        self.assertEqual([], db.list_attempts(self.child.id))
        self.assertTrue(self._messagebox_errors)
        self._messagebox_errors.clear()

        panel._finish_quiz()
        self.assertIsNone(db.load_quiz_progress(self.child.id))
        self.assertEqual(1, len(db.list_attempts(self.child.id)))

    def test_cleanup_failure_remains_idempotent_across_panel_restart(self) -> None:
        _first_root, first = self._panel()
        attempt_id = self._seed_in_progress(first)
        with patch.object(first, "_clear_quiz_progress", side_effect=OSError("locked")):
            first._finish_quiz()
        self.assertEqual(attempt_id, db.load_quiz_progress(self.child.id)[0])
        self.assertEqual(1, len(db.list_attempts(self.child.id)))
        self._messagebox_errors.clear()

        _second_root, second = self._panel()
        self._askyesno_answers.append(True)
        second.on_module_activated()
        self.assertIsNotNone(second._completion_created_at)
        second._finish_quiz()
        self.assertIsNone(db.load_quiz_progress(self.child.id))
        self.assertEqual(1, len(db.list_attempts(self.child.id)))

    def test_wrong_answer_recovery_is_persisted_and_can_complete(self) -> None:
        ui_settings.save_summer_mode(True)
        _root, panel = self._panel()
        question = self._question()
        panel._questions = [question]
        panel._attempt_skill = question.skill
        panel._show_question()
        panel.answer_var.set("12")
        panel.submit_answer()
        self.assertEqual("redo", panel._mistake_recovery.phase)
        self.assertIsNotNone(db.load_quiz_progress(self.child.id))

        panel.answer_var.set("13")
        with patch.object(panel, "_build_mistake_recovery_followup", return_value=None):
            panel.submit_answer()
        self.assertEqual("complete", panel._mistake_recovery.phase)
        self.assertTrue(panel.next_btn.instate(["!disabled"]))

        _resume_root, resumed = self._panel()
        self._askyesno_answers.append(True)
        resumed.on_module_activated()
        self.assertEqual("complete", resumed._mistake_recovery.phase)
        self.assertTrue(resumed.next_btn.instate(["!disabled"]))

    def test_inconsistent_resume_state_is_discarded(self) -> None:
        _root, panel = self._panel()
        attempt_id = self._seed_in_progress(panel)
        _saved_id, index, state_json = db.load_quiz_progress(self.child.id)
        payload = json.loads(state_json)
        payload["score"] = 0
        db.save_quiz_progress(
            self.child.id, attempt_id, index, json.dumps(payload), now_iso()
        )

        _resume_root, resumed = self._panel()
        resumed.on_module_activated()
        self.assertEqual([], resumed._questions)
        self.assertIsNone(db.load_quiz_progress(self.child.id))
        self.assertTrue(self._messagebox_warnings)


if __name__ == "__main__":
    unittest.main()
