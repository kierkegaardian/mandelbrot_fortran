from __future__ import annotations

import sqlite3
import tempfile
import unittest

from app import db, quiz_flow
from app.quiz_engine import Question
from app.ui_quiz import _subskill_for_question


class _Var:
    def __init__(self, value):
        self._value = value

    def get(self):
        return self._value

    def set(self, value) -> None:
        self._value = value


class _Button:
    def state(self, _states) -> None:
        return None


class _SummaryBox:
    def __init__(self) -> None:
        self.text = ""

    def config(self, **_kwargs) -> None:
        return None

    def delete(self, *_args) -> None:
        self.text = ""

    def insert(self, *_args) -> None:
        self.text += str(_args[-1])


class _PanelStub:
    def __init__(self, profile, question: Question, *, answer: str, correct: bool) -> None:
        self._profile = profile
        self._record_attempt = True
        self._record_progress = True
        self._quiz_started_monotonic = None
        self._attempt_skill = question.skill
        self._score = 1 if correct else 0
        self._questions = [question]
        self._answers = [(question, answer, correct)]
        self._launch_context = "manual"
        self._quiz_progress_cleared = False
        self.skill_var = _Var(question.skill)
        self.type_var = _Var("typed")
        self.level_var = _Var(1)
        self.prompt_var = _Var("")
        self.feedback_var = _Var("")
        self.next_btn = _Button()
        self.summary_box = _SummaryBox()

    def _profile_getter(self):
        return self._profile

    def _clear_quiz_progress(self) -> None:
        self._quiz_progress_cleared = True

    def _subskill_for_question(self, question: Question) -> str | None:
        return _subskill_for_question(question)

    def _subskill_coverage_by_skill(self, _profile_id: int) -> dict[str, float]:
        return {}

    def _show_quiz_summary(self, *args, **kwargs) -> None:
        pass


class MasteryTruthfulnessTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        tmp_path = self._tmp.name

        def _tmp_config() -> db.DbConfig:
            return db.DbConfig(path=f"{tmp_path}/test_app.db")

        self.enterContext(db.override_db_config(_tmp_config))
        db.init_db()
        self.profile = db.create_profile("Student", "child", "2026-03-10T12:00:00+00:00")

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _latest_question_row(self, skill: str) -> sqlite3.Row | None:
        conn = sqlite3.connect(db.db_config().path)
        conn.row_factory = sqlite3.Row
        try:
            return conn.execute(
                """
                SELECT skill, subskill, question_label, mode, prompt, correct_answer, user_answer, is_correct
                FROM quiz_questions
                WHERE skill = ?
                ORDER BY id DESC
                LIMIT 1
                """,
                (skill,),
            ).fetchone()
        finally:
            conn.close()

    def test_finish_quiz_records_explicit_subskill_in_progress_and_history(self) -> None:
        question = Question(
            skill="calculus_1",
            prompt="Find the slope of the line through (1, 2) and (3, 6).",
            correct_answer="2",
            explanation="Slope is rise over run.",
            choices=None,
            visual=None,
            subskill="Average rate of change between two points",
            question_label="Core",
            mode="expression",
        )
        panel = _PanelStub(self.profile, question, answer="2", correct=True)

        quiz_flow.finish_quiz(panel)

        progress = db.list_subskill_progress(self.profile.id, "calculus_1")
        self.assertEqual(len(progress), 1)
        self.assertEqual(progress[0].subskill, "Average rate of change between two points")

        row = self._latest_question_row("calculus_1")
        self.assertIsNotNone(row)
        assert row is not None
        self.assertEqual(row["subskill"], "Average rate of change between two points")
        self.assertEqual(row["user_answer"], "2")
        self.assertEqual(row["is_correct"], 1)
        self.assertTrue(panel._quiz_progress_cleared)

    def test_finish_quiz_keeps_missing_subskill_null_and_untracked(self) -> None:
        question = Question(
            skill="add_subtract",
            prompt="8 + 5 = ?",
            correct_answer="13",
            explanation="Add the two numbers.",
            choices=None,
            visual=None,
            question_label="Core",
            mode="expression",
        )
        panel = _PanelStub(self.profile, question, answer="13", correct=True)

        quiz_flow.finish_quiz(panel)

        self.assertEqual(db.list_subskill_progress(self.profile.id, "add_subtract"), [])

        row = self._latest_question_row("add_subtract")
        self.assertIsNotNone(row)
        assert row is not None
        self.assertIsNone(row["subskill"])
        self.assertEqual(row["user_answer"], "13")
        self.assertEqual(row["is_correct"], 1)
        self.assertTrue(panel._quiz_progress_cleared)


if __name__ == "__main__":
    unittest.main()
