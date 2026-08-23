from __future__ import annotations

from pathlib import Path
import unittest
from unittest.mock import patch

from app import db, summer_program, sync_service
from app.explanations import ARITHMETIC_MODE_EXPLANATIONS
from app.time_utils import now_iso
from app.ui_profile_picker import ProfilePicker
from app.ui_root import AppShell
from app.ui_settings import UiSettings, load_ui_settings, save_ui_settings

from tests.tk_test_utils import TkAppTestCase, tk_available


@unittest.skipUnless(tk_available(), "Tk GUI not available")
class SummerModeUiFlowTests(TkAppTestCase):
    def setUp(self) -> None:
        super().setUp()

        db.init_db()
        save_ui_settings(UiSettings(default_grade_band="K-5", summer_mode=True))

        now = now_iso()
        self.parent = sync_service.create_profile("Parent One", "parent", now)
        self.child = sync_service.create_profile("Kid One", "child", now)
        db.set_parent_pin(self.parent.id, "1234", now)

    def _tab_texts(self, shell: AppShell) -> list[str]:
        return [shell.notebook.tab(i, "text") for i in range(shell.notebook.index("end"))]

    def test_profile_picker_blocks_extra_parent_creation_in_summer_mode(self) -> None:
        root = self._new_root(withdraw=True)
        picker = ProfilePicker(root)

        self._pump(root)
        self.assertTrue(picker.parent_role_btn.instate(["disabled"]))

        picker.name_entry.insert(0, "Kid Two")
        picker.create_btn.invoke()
        self._pump(root)
        self.assertTrue(any(profile.name == "Kid Two" and profile.role == "child" for profile in picker._profiles))

        for btn in picker.profiles_container.winfo_children():
            try:
                text = str(btn.cget("text"))
            except Exception:
                continue
            if "Kid One" in text:
                btn.invoke()
                break

        self._pump(root)
        self.assertIsNotNone(picker.selected)
        self.assertEqual("Kid One", picker.selected.name)

    def test_parent_toggle_changes_tab_layout_after_relaunch(self) -> None:
        parent_summer_tabs = ["Today", "Practice", "Quizzes", "Parent", "Bonus Explore"]
        child_summer_tabs = ["Today", "Practice", "Quizzes"]
        normal_tabs = ["Today", "Practice", "Quizzes", "Skill Map", "Parent", "Bonus Explore"]

        root = self._new_root()
        shell = AppShell(root, self.parent)
        self._pump(root)
        self.assertEqual(parent_summer_tabs, self._tab_texts(shell))
        self.assertFalse(bool(shell.dashboard.child_next_frame.winfo_manager()))

        self._askstring_answers.append("1234")
        shell.notebook.select(shell._parent_tab_index)
        self._pump(root)
        self.assertTrue(shell._parent_unlocked)

        shell.parent.summer_mode_var.set(False)
        shell.parent._toggle_summer_mode()
        self._pump(root)
        self.assertFalse(load_ui_settings().summer_mode)
        self._close_shell(root, shell)

        root = self._new_root()
        shell = AppShell(root, self.parent)
        self._pump(root)
        self.assertEqual(normal_tabs, self._tab_texts(shell))

        self._askstring_answers.append("1234")
        shell.notebook.select(shell._parent_tab_index)
        self._pump(root)
        shell.parent.summer_mode_var.set(True)
        shell.parent._toggle_summer_mode()
        self._pump(root)
        self.assertTrue(load_ui_settings().summer_mode)
        self._close_shell(root, shell)

        root = self._new_root()
        shell = AppShell(root, self.child)
        self._pump(root)
        self.assertEqual(child_summer_tabs, self._tab_texts(shell))
        self._close_shell(root, shell)

    def test_normal_child_layout_keeps_parent_and_fractal_secondary(self) -> None:
        save_ui_settings(UiSettings(default_grade_band="K-5", summer_mode=False))

        root = self._new_root()
        shell = AppShell(root, self.child)
        self._pump(root)
        self.assertEqual(["Today", "Practice", "Quizzes", "Skill Map"], self._tab_texts(shell))

        shell.dashboard.render()
        self._pump(root)
        self.assertEqual("Today's Math", shell.dashboard.heading_var.get())
        self.assertTrue(bool(shell.dashboard.child_next_frame.winfo_manager()))
        self.assertEqual("Today's Practice", shell.dashboard.child_next_title_var.get())
        self.assertIn("Ask a parent", shell.dashboard.child_progress_var.get())
        self.assertIn("ask a parent", shell.dashboard.child_goal_focus_var.get())
        self.assertIn("Bonus Explore unlocks after practice.", shell.dashboard.child_progress_var.get())
        self.assertNotIn("Parent", self._tab_texts(shell))
        self.assertNotIn("Bonus Explore", self._tab_texts(shell))
        self.assertFalse(bool(shell.dashboard.bonus_frame.winfo_manager()))

        db.record_daily_review_completion(self.child.id, now_iso())
        shell.dashboard.render()
        self._pump(root)
        self.assertIn("Bonus Explore unlocked.", shell.dashboard.child_progress_var.get())
        self.assertTrue(bool(shell.dashboard.bonus_frame.winfo_manager()))

        shell.dashboard.bonus_btn.invoke()
        self._pump(root)
        self.assertIn("Bonus Explore", self._tab_texts(shell))
        self.assertEqual("Bonus Explore", shell.notebook.tab(shell.notebook.select(), "text"))
        self._close_shell(root, shell)

    def test_child_quiz_tab_uses_simple_practice_launcher(self) -> None:
        save_ui_settings(UiSettings(default_grade_band="K-5", summer_mode=False))

        root = self._new_root()
        shell = AppShell(root, self.child)
        self._pump(root)
        shell.notebook.select(shell.quiz.controls_frame)
        self._pump(root)

        self.assertFalse(bool(shell.quiz.history_group.winfo_manager()))
        self.assertFalse(bool(shell.quiz.settings_group.winfo_manager()))
        self.assertEqual("Start Practice", shell.quiz.start_quiz_btn.cget("text"))
        self.assertEqual("learning_blend", shell.quiz.strategy_var.get())
        self.assertEqual("both", shell.quiz.type_var.get())
        self.assertIn("Tests stay in Parent tools", shell.quiz.launch_note_var.get())

        shell.quiz.start_quiz()
        self._pump(root)
        self.assertTrue(shell.quiz._questions)
        self.assertIn("Think:", shell.quiz.intuition_var.get())
        self.assertNotIn("Common mistake:", shell.quiz.intuition_var.get())
        self._close_shell(root, shell)

    def test_parent_quiz_tab_keeps_full_assessment_controls(self) -> None:
        save_ui_settings(UiSettings(default_grade_band="K-5", summer_mode=False))

        root = self._new_root()
        shell = AppShell(root, self.parent)
        self._pump(root)
        shell.notebook.select(shell.quiz.controls_frame)
        self._pump(root)

        self.assertTrue(bool(shell.quiz.history_group.winfo_manager()))
        self.assertTrue(bool(shell.quiz.settings_group.winfo_manager()))
        self.assertEqual("Start Quiz", shell.quiz.start_quiz_btn.cget("text"))
        self.assertIn("historical_practice", shell.quiz.strategy_combo.cget("values"))
        self.assertEqual("", shell.quiz.launch_note_var.get())

        shell.quiz.start_quiz()
        self._pump(root)
        self.assertTrue(shell.quiz._questions)
        self.assertEqual("", shell.quiz.intuition_var.get())
        self._close_shell(root, shell)

    def test_child_quiz_completion_uses_next_step_copy(self) -> None:
        save_ui_settings(UiSettings(default_grade_band="K-5", summer_mode=False))

        root = self._new_root()
        shell = AppShell(root, self.child)
        self._pump(root)
        shell.quiz._show_quiz_summary(
            score=1,
            total=1,
            keyed_total=1,
            retake_required=False,
            assignments=0,
            recommendations=[],
            mistakes=[],
            elapsed_seconds=None,
        )
        self._pump(root)

        summary_text = " | ".join(self._texts_under(shell.quiz.summary_frame))
        self.assertIn("Perfect Practice!", summary_text)
        self.assertIn("What happened: You got every question right.", summary_text)
        self.assertIn("Next step: practice this skill again.", summary_text)
        self.assertIn("Practice This Again", summary_text)
        self.assertIn("Nothing tricky to review today.", summary_text)
        self.assertNotIn("Mastery requires 100%", summary_text)
        self._close_shell(root, shell)

    def test_parent_quiz_completion_keeps_mastery_retake_copy(self) -> None:
        save_ui_settings(UiSettings(default_grade_band="K-5", summer_mode=False))

        root = self._new_root()
        shell = AppShell(root, self.parent)
        self._pump(root)
        shell.quiz._show_quiz_summary(
            score=0,
            total=1,
            keyed_total=1,
            retake_required=True,
            assignments=0,
            recommendations=[],
            mistakes=[],
            elapsed_seconds=None,
        )
        self._pump(root)

        summary_text = " | ".join(self._texts_under(shell.quiz.summary_frame))
        self.assertIn("Quiz Complete!", summary_text)
        self.assertIn("Mastery requires 100%", summary_text)
        self.assertIn("Retake Quiz", summary_text)
        self.assertNotIn("What happened:", summary_text)
        self._close_shell(root, shell)

    def test_child_bonus_explore_unlocks_after_completed_practice(self) -> None:
        root = self._new_root()
        shell = AppShell(root, self.child)
        self._pump(root)

        shell.dashboard.render()
        self._pump(root)
        self.assertNotIn("Bonus Explore", self._tab_texts(shell))
        self.assertFalse(bool(shell.dashboard.bonus_frame.winfo_manager()))

        db.record_daily_review_completion(self.child.id, now_iso())
        shell.dashboard.render()
        self._pump(root)
        self.assertTrue(bool(shell.dashboard.bonus_frame.winfo_manager()))

        shell.dashboard.bonus_btn.invoke()
        self._pump(root)
        self.assertIn("Bonus Explore", self._tab_texts(shell))
        self.assertEqual("Bonus Explore", shell.notebook.tab(shell.notebook.select(), "text"))
        self._close_shell(root, shell)

    def test_parent_school_year_target_and_goal_assignments(self) -> None:
        root = self._new_root()
        shell = AppShell(root, self.parent)
        self._pump(root)

        shell.parent.school_profile_var.set(self.child.name)
        shell.parent.school_grade_var.set("1")
        shell.parent.school_stretch_var.set(True)
        shell.parent._save_school_year_target()
        self._pump(root)

        target = db.get_school_year_target(self.child.id)
        self.assertIsNotNone(target)
        assert target is not None
        self.assertEqual(1, target.grade)
        self.assertTrue(target.stretch_enabled)

        shell.parent._add_grade_goal_assignments()
        self._pump(root)
        assignments = sync_service.list_assignments(self.child.id, active_only=True)
        keys = {(item.skill, item.subskill, item.target_type) for item in assignments}
        self.assertIn(("place_value", "Ones, tens, and hundreds identification", "subskill_mastered"), keys)
        self.assertIn(("add_subtract", "Word problems", "subskill_mastered"), keys)
        self.assertIn(("geometry_shapes", "Compose 2D shapes", "subskill_mastered"), keys)
        self.assertIn(("data_displays", "Picture and bar graphs", "subskill_mastered"), keys)
        self.assertTrue(all(item.notes.startswith("TX Grade 1:") for item in assignments))
        count_after_first_seed = len(assignments)

        shell.parent._add_grade_goal_assignments()
        self._pump(root)
        self.assertEqual(
            count_after_first_seed,
            len(sync_service.list_assignments(self.child.id, active_only=True)),
        )
        self._close_shell(root, shell)

        root = self._new_root()
        shell = AppShell(root, self.child)
        self._pump(root)
        shell.dashboard.render()
        self._pump(root)
        self.assertEqual("Assignment Ready", shell.dashboard.child_next_title_var.get())
        self.assertEqual("Start Assignment", shell.dashboard.child_next_btn.cget("text"))
        self.assertIn("Texas Grade 1", shell.dashboard.school_year_var.get())
        self.assertIn("next:", shell.dashboard.school_year_var.get())
        self.assertIn("Texas Grade 1", shell.dashboard.child_progress_var.get())
        self.assertIn("next goal is", shell.dashboard.child_progress_var.get())
        self.assertIn("Why it matters:", shell.dashboard.child_goal_focus_var.get())
        self.assertIn("Numbers are built", shell.dashboard.child_goal_focus_var.get())
        self.assertIn("Try this next:", shell.dashboard.child_goal_focus_var.get())
        self._close_shell(root, shell)

    def test_child_dashboard_launches_next_texas_goal_practice(self) -> None:
        db.save_school_year_target(self.child.id, 1, True, now_iso())

        root = self._new_root()
        shell = AppShell(root, self.child)
        self._pump(root)
        shell.dashboard.render()
        self._pump(root)

        self.assertEqual("Next Texas Goal", shell.dashboard.child_next_title_var.get())
        self.assertEqual("Practice Next Goal", shell.dashboard.child_next_btn.cget("text"))
        self.assertIn("Place Value", shell.dashboard.child_next_detail_var.get())
        self.assertIn("Ones, tens, and hundreds identification", shell.dashboard.child_next_detail_var.get())

        shell.dashboard.child_next_btn.invoke()
        self._pump(root)

        self.assertEqual("Quizzes", shell.notebook.tab(shell.notebook.select(), "text"))
        self.assertEqual("place_value", shell.quiz.skill_var.get())
        self.assertEqual("Ones, tens, and hundreds identification", shell.quiz.subskill_var.get())
        self.assertEqual(1, shell.quiz.level_var.get())
        self.assertTrue(shell.quiz._questions)
        self.assertIn("Think:", shell.quiz.intuition_var.get())
        self._close_shell(root, shell)

    def test_child_dashboard_targets_unfinished_step_inside_next_texas_goal(self) -> None:
        db.save_school_year_target(self.child.id, 1, True, now_iso())
        for idx in range(3):
            db.upsert_subskill_progress(
                self.child.id,
                "place_value",
                "Ones, tens, and hundreds identification",
                True,
                f"2026-06-26T01:0{idx}:00+00:00",
                streak_to_master=3,
            )

        root = self._new_root()
        shell = AppShell(root, self.child)
        self._pump(root)
        shell.dashboard.render()
        self._pump(root)

        self.assertEqual("Next Texas Goal", shell.dashboard.child_next_title_var.get())
        self.assertIn("Compare numbers by place value", shell.dashboard.child_next_detail_var.get())
        self.assertNotIn("Ones, tens, and hundreds identification", shell.dashboard.child_next_detail_var.get())
        self.assertIn("Goal steps: 1/2 done", shell.dashboard.child_goal_focus_var.get())
        self.assertIn("Next step: Compare numbers by place value", shell.dashboard.child_goal_focus_var.get())
        self.assertIn("Done: Ones, tens, and hundreds identification", shell.dashboard.child_goal_focus_var.get())

        shell.dashboard.child_next_btn.invoke()
        self._pump(root)

        self.assertEqual("Quizzes", shell.notebook.tab(shell.notebook.select(), "text"))
        self.assertEqual("place_value", shell.quiz.skill_var.get())
        self.assertEqual("Compare numbers by place value", shell.quiz.subskill_var.get())
        self._close_shell(root, shell)

    def test_parent_adds_child_specific_next_goal_review_assignments(self) -> None:
        root = self._new_root()
        shell = AppShell(root, self.parent)
        self._pump(root)

        self.assertIn("Add Next Goal Review", self._texts_under(shell.parent.school_year_tab))
        shell.parent.school_profile_var.set(self.child.name)
        shell.parent.school_grade_var.set("1")
        shell.parent.school_stretch_var.set(True)
        shell.parent._save_school_year_target()
        self._pump(root)

        shell.parent._add_next_goal_review_assignments()
        self._pump(root)
        assignments = sync_service.list_assignments(self.child.id, active_only=True)
        keys = {(item.skill, item.subskill, item.target_type) for item in assignments}
        self.assertEqual(
            {
                ("place_value", "Ones, tens, and hundreds identification", "subskill_mastered"),
                ("place_value", "Compare numbers by place value", "subskill_mastered"),
            },
            keys,
        )
        self.assertTrue(all(item.notes.startswith("TX Grade 1 Next Goal:") for item in assignments))

        shell.parent._add_next_goal_review_assignments()
        self._pump(root)
        self.assertEqual(len(assignments), len(sync_service.list_assignments(self.child.id, active_only=True)))

        for subskill in ("Ones, tens, and hundreds identification", "Compare numbers by place value"):
            for idx in range(3):
                db.upsert_subskill_progress(
                    self.child.id,
                    "place_value",
                    subskill,
                    True,
                    f"2026-06-26T01:1{idx}:00+00:00",
                    streak_to_master=3,
                )

        shell.parent._add_next_goal_review_assignments()
        self._pump(root)
        assignments = sync_service.list_assignments(self.child.id, active_only=True)
        keys = {(item.skill, item.subskill, item.target_type) for item in assignments}
        self.assertIn(("add_subtract", "Single-digit addition", "subskill_mastered"), keys)
        self.assertIn(("add_subtract", "Word problems", "subskill_mastered"), keys)
        self.assertTrue(
            any(item.notes.startswith("TX Grade 1 Next Goal: Solve addition") for item in assignments)
        )
        self._close_shell(root, shell)

    def test_parent_adds_selected_texas_goal_review_assignments(self) -> None:
        root = self._new_root()
        shell = AppShell(root, self.parent)
        self._pump(root)

        self.assertIn("Add Selected Goal Review", self._texts_under(shell.parent.school_year_tab))
        shell.parent.school_profile_var.set(self.child.name)
        shell.parent.school_grade_var.set("1")
        shell.parent.school_stretch_var.set(True)
        shell.parent._refresh_school_year_goals()
        self._pump(root)

        matching_rows = [
            idx
            for idx in range(shell.parent.school_year_list.size())
            if "1.8" in shell.parent.school_year_list.get(idx)
        ]
        self.assertTrue(matching_rows)
        shell.parent.school_year_list.selection_set(matching_rows[0])
        shell.parent._add_selected_goal_review_assignments()
        self._pump(root)

        assignments = sync_service.list_assignments(self.child.id, active_only=True)
        keys = {(item.skill, item.subskill, item.target_type) for item in assignments}
        self.assertIn(("data_displays", "Picture and bar graphs", "subskill_mastered"), keys)
        self.assertIn(("data_displays", "Questions from data displays", "subskill_mastered"), keys)
        self.assertTrue(all(item.notes.startswith("TX Grade 1 Selected Goal:") for item in assignments))
        self._close_shell(root, shell)

    def test_parent_generates_school_year_assessment_packet(self) -> None:
        root = self._new_root()
        shell = AppShell(root, self.parent)
        self._pump(root)

        shell.parent.school_profile_var.set(self.child.name)
        shell.parent.school_grade_var.set("1")
        shell.parent.school_stretch_var.set(True)
        with patch("app.ui_parent.webbrowser.open") as open_mock:
            shell.parent._generate_school_year_assessment()
        self._pump(root)

        open_mock.assert_called_once()
        pipeline = db.skill_progress_pipeline(self.child.id)
        self.assertEqual(1, pipeline["texas_grade_1"]["worksheets"])
        with db.managed_connection() as conn:
            row = conn.execute(
                "SELECT num_questions FROM worksheets WHERE profile_id = ? AND skill = ?",
                (self.child.id, "texas_grade_1"),
            ).fetchone()
        self.assertIsNotNone(row)
        assert row is not None
        self.assertGreaterEqual(int(row["num_questions"]), 10)
        self.assertGreaterEqual(shell.parent.school_year_packets_list.size(), 1)
        self.assertIn("TX Grade 1", shell.parent.school_year_packets_list.get(0))
        shell.parent.school_year_packets_list.selection_set(0)
        with patch("app.ui_parent.webbrowser.open") as reopen_mock:
            shell.parent._open_selected_school_year_packet()
        reopen_mock.assert_called_once()
        self.assertTrue(str(reopen_mock.call_args.args[0]).startswith("file://"))
        self.assertIn("texas_grade_1_assessment", str(reopen_mock.call_args.args[0]))

        shell.parent.school_year_packets_list.selection_clear(0, "end")
        shell.parent.school_year_packets_list.selection_set(0)
        shell.parent._archive_selected_school_year_packet()
        self._pump(root)

        self.assertEqual(0, shell.parent.school_year_packets_list.size())
        self.assertIn("none yet", shell.parent.school_year_packets_var.get())
        archived = db.list_worksheets(self.child.id, skill_prefix="texas_grade_", include_archived=True)
        self.assertEqual(1, len(archived))
        self.assertIsNotNone(archived[0].archived_at)
        self.assertTrue(Path(archived[0].file_path).exists())
        pipeline_after_archive = db.skill_progress_pipeline(self.child.id)
        self.assertEqual(1, pipeline_after_archive["texas_grade_1"]["worksheets"])
        self._close_shell(root, shell)

    def test_dashboard_quiz_recovery_resume_flow(self) -> None:
        root = self._new_root()
        shell = AppShell(root, self.child)
        self._pump(root)

        shell.dashboard.render()
        self._pump(root)
        self.assertEqual("Start Today's Practice", shell.dashboard.daily_btn.cget("text"))
        self.assertTrue(bool(shell.dashboard.welcome_frame.winfo_manager()))

        shell.dashboard.welcome_start_btn.invoke()
        self._pump(root)
        self.assertEqual("Quizzes", shell.notebook.tab(shell.notebook.select(), "text"))
        self.assertEqual("counting", shell.quiz.skill_var.get())
        self.assertTrue(shell.quiz._questions)

        question = shell.quiz._questions[shell.quiz._index]
        self._set_answer(shell.quiz, question, self._wrong_answer(question))
        shell.quiz.submit_btn.invoke()
        self._pump(root)
        self.assertTrue(shell.quiz._recovery_active())
        self.assertEqual("Try Again", shell.quiz.submit_btn.cget("text"))
        self._close_shell(root, shell)

        root = self._new_root()
        shell = AppShell(root, self.child)
        self._pump(root)
        self._askyesno_answers.append(True)
        shell.quiz.start_quiz()
        self._pump(root)
        self.assertTrue(shell.quiz._recovery_active())
        self.assertEqual("Resumed recovery step.", shell.quiz.feedback_var.get())

        question = shell.quiz._current_recovery_question()
        self.assertIsNotNone(question)
        self._set_answer(shell.quiz, question, question.correct_answer)
        shell.quiz.submit_btn.invoke()
        self._pump(root)
        self.assertIsNotNone(shell.quiz._mistake_recovery)
        self.assertEqual("followup", shell.quiz._mistake_recovery.phase)
        self._close_shell(root, shell)

        root = self._new_root()
        shell = AppShell(root, self.child)
        self._pump(root)
        self._askyesno_answers.append(True)
        shell.quiz.start_quiz()
        self._pump(root)
        self.assertIsNotNone(shell.quiz._mistake_recovery)
        self.assertEqual("followup", shell.quiz._mistake_recovery.phase)

        question = shell.quiz._current_recovery_question()
        self.assertIsNotNone(question)
        self.assertEqual(
            question.skill in ARITHMETIC_MODE_EXPLANATIONS,
            shell.quiz.stuck_btn.instate(["!disabled"]),
        )
        self._set_answer(shell.quiz, question, question.correct_answer)
        shell.quiz.submit_btn.invoke()
        self._pump(root)
        self.assertIsNotNone(shell.quiz._mistake_recovery)
        self.assertEqual("complete", shell.quiz._mistake_recovery.phase)

        shell.quiz.next_btn.invoke()
        self._pump(root)
        self.assertIsNone(shell.quiz._mistake_recovery)
        self.assertEqual(1, shell.quiz._index)
        self._close_shell(root, shell)

    def test_guided_place_value_lesson_advances(self) -> None:
        root = self._new_root()
        shell = AppShell(root, self.child)
        self._pump(root)

        shell.notebook.select(shell.arithmetic.controls_frame)
        self._pump(root)
        shell.arithmetic.skill_var.set("place_value")
        shell.arithmetic._on_skill_change()
        self._pump(root)
        self.assertTrue(shell.arithmetic.guided_btn.instate(["!disabled"]))

        shell.arithmetic.guided_btn.invoke()
        self._pump(root)
        self.assertIsNotNone(shell.arithmetic.guided_frame)
        self.assertTrue(shell.arithmetic.guided_frame.winfo_ismapped())

        guard = 0
        while shell.arithmetic._lesson_steps[shell.arithmetic._lesson_index].expected_answer is None:
            shell.arithmetic.guided_next_btn.invoke()
            self._pump(root)
            guard += 1
            if guard > 10:
                self.fail("Guided lesson never reached an answer step.")

        step = shell.arithmetic._lesson_steps[shell.arithmetic._lesson_index]
        shell.arithmetic.guided_answer_var.set(str(step.expected_answer))
        shell.arithmetic.guided_submit_btn.invoke()
        self._pump(root)
        self.assertIn("Correct. Move to the next step.", shell.arithmetic.guided_feedback_var.get())

        shell.arithmetic.guided_next_btn.invoke()
        self._pump(root)
        self.assertGreaterEqual(shell.arithmetic._lesson_index, 1)
        self._close_shell(root, shell)

    def test_single_question_recovery_reaches_summary(self) -> None:
        profile = sync_service.create_profile("Kid Last", "child", now_iso())
        root = self._new_root()
        shell = AppShell(root, profile)
        self._pump(root)

        shell.notebook.select(shell.quiz.controls_frame)
        self._pump(root)
        shell.quiz.apply_preset(
            track=shell._preset_track_for_skill("counting"),
            skill="counting",
            num_questions=1,
            level=1,
            question_type="both",
            launch_context="manual",
        )
        shell.quiz.start_quiz()
        self._pump(root)
        self.assertEqual(1, len(shell.quiz._questions))

        question = shell.quiz._questions[0]
        self._set_answer(shell.quiz, question, self._wrong_answer(question))
        shell.quiz.submit_btn.invoke()
        self._pump(root)
        self.assertTrue(shell.quiz._recovery_active())

        question = shell.quiz._current_recovery_question()
        self.assertIsNotNone(question)
        self._set_answer(shell.quiz, question, question.correct_answer)
        shell.quiz.submit_btn.invoke()
        self._pump(root)
        self.assertIsNotNone(shell.quiz._mistake_recovery)
        self.assertEqual("followup", shell.quiz._mistake_recovery.phase)

        question = shell.quiz._current_recovery_question()
        self.assertIsNotNone(question)
        self._set_answer(shell.quiz, question, question.correct_answer)
        shell.quiz.submit_btn.invoke()
        self._pump(root)
        shell.quiz.next_btn.invoke()
        self._pump(root)

        summary_text = " | ".join(self._texts_under(shell.quiz.summary_frame))
        self.assertIn("Practice Complete!", summary_text)
        self.assertIn("What happened:", summary_text)
        self._close_shell(root, shell)

    def test_parent_review_blocks_child_launch_until_parent_decides(self) -> None:
        program = summer_program.create_summer_program(
            profile_id=self.child.id,
            lane="prealgebra_finish",
            start_date="2026-06-01",
            end_date="2026-08-31",
            days_per_week=5,
            minutes_per_session=35,
            student_age_years=9,
            created_at=now_iso(),
        )
        placement = summer_program.next_summer_program_task(program.id)
        assert placement is not None
        summer_program.update_task_outcome(
            task_id=placement.id,
            score_pct=58.0,
            attempt_id=77,
            completed_at=now_iso(),
            strand_results={
                "fractions": 60.0,
                "integer_order_fluency": 58.0,
                "variables_equations": 55.0,
                "ratios_percent": 48.0,
                "exponents_coordinates": 44.0,
            },
        )

        root = self._new_root()
        shell = AppShell(root, self.child)
        self._pump(root)
        shell.dashboard.render()
        self._pump(root)
        self.assertIn("Parent review needed", shell.dashboard.program_var.get())
        self.assertEqual("Waiting On Parent Review", shell.dashboard.daily_btn.cget("text"))
        self.assertFalse(shell.dashboard.daily_btn.instate(["!disabled"]))
        self._close_shell(root, shell)

        root = self._new_root()
        shell = AppShell(root, self.parent)
        self._pump(root)
        self._askstring_answers.append("1234")
        shell.notebook.select(shell._parent_tab_index)
        self._pump(root)
        shell.parent.tabs.select(shell.parent.summer_program_tab)
        shell.parent.program_profile.set("Kid One")
        shell.parent._refresh_summer_program()
        self._pump(root)
        self.assertTrue(shell.parent.program_accept_btn.instate(["!disabled"]))
        self.assertTrue(shell.parent.program_keep_lane_btn.instate(["!disabled"]))
        self.assertIn("Parent review needed", shell.parent.program_alert_var.get())
        shell.parent.program_keep_lane_btn.invoke()
        self._pump(root)
        self.assertFalse(shell.parent.program_next_btn.instate(["disabled"]))
        self._close_shell(root, shell)

    def test_parent_exports_resource_review_without_student_worksheet_credit(self) -> None:
        summer_program.create_summer_program(
            profile_id=self.child.id,
            lane="prealgebra_finish",
            start_date="2026-06-01",
            end_date="2026-08-31",
            days_per_week=5,
            minutes_per_session=35,
            student_age_years=9,
            created_at=now_iso(),
        )

        root = self._new_root()
        shell = AppShell(root, self.parent)
        self._pump(root)
        shell.parent.tabs.select(shell.parent.summer_program_tab)
        shell.parent.program_profile.set("Kid One")
        shell.parent._refresh_summer_program()
        self._pump(root)

        self.assertTrue(shell.parent.resource_review_export_btn.instate(["!disabled"]))
        with patch("app.ui_parent.webbrowser.open") as open_mock:
            shell.parent._export_resource_review()
        self._pump(root)

        open_mock.assert_called_once()
        report_url = str(open_mock.call_args.args[0])
        self.assertTrue(report_url.startswith("file://"))
        report_path = Path(report_url.removeprefix("file://"))
        self.assertTrue(report_path.exists())
        html = report_path.read_text(encoding="utf-8")
        self.assertIn("Pre-Algebra Finish Resource Review", html)
        self.assertIn("Ready: 43</div>", html)
        self.assertIn("Rows: 43</div>", html)
        self.assertEqual([], db.list_worksheets(self.child.id))
        self._close_shell(root, shell)

    def test_blocked_checkpoint_stays_launchable_on_dashboard(self) -> None:
        program = summer_program.create_summer_program(
            profile_id=self.child.id,
            lane="prealgebra_finish",
            start_date="2026-06-01",
            end_date="2026-08-31",
            days_per_week=5,
            minutes_per_session=35,
            student_age_years=9,
            created_at=now_iso(),
        )
        placement = summer_program.next_summer_program_task(program.id)
        assert placement is not None
        summer_program.update_task_outcome(
            task_id=placement.id,
            score_pct=84.0,
            attempt_id=81,
            completed_at=now_iso(),
            strand_results={
                "fractions": 82.0,
                "integer_order_fluency": 84.0,
                "variables_equations": 81.0,
                "ratios_percent": 79.0,
                "exponents_coordinates": 78.0,
            },
        )
        summer_program.accept_summer_program_recommendation(program.id, now_iso())
        active = summer_program.get_active_summer_program(self.child.id)
        assert active is not None
        ordered = db.list_summer_program_tasks(active.id)
        prefix = [task for task in ordered if task.task_kind in {"lesson", "practice_a", "practice_b", "mixed_review"}][:4]
        for offset, task in enumerate(prefix, start=82):
            summer_program.update_task_outcome(
                task_id=task.id,
                score_pct=100.0,
                attempt_id=offset,
                completed_at=now_iso(),
            )
        checkpoint = next(task for task in db.list_summer_program_tasks(active.id) if task.task_kind == "checkpoint")
        summer_program.update_task_outcome(
            task_id=checkpoint.id,
            score_pct=60.0,
            attempt_id=88,
            completed_at=now_iso(),
            strand_results={
                "fractions": 62.0,
                "variables_equations": 57.0,
                "ratios_percent": 54.0,
            },
        )

        root = self._new_root()
        shell = AppShell(root, self.child)
        self._pump(root)
        shell.dashboard.render()
        self._pump(root)
        self.assertIn("Retry checkpoint", shell.dashboard.program_var.get())
        self.assertIn("Projected finish", shell.dashboard.program_var.get())
        self.assertIn("Catch-up plan", shell.dashboard.program_var.get())
        self.assertEqual("Retry Program Task", shell.dashboard.daily_btn.cget("text"))
        self.assertIn("Remediation retry", shell.dashboard.daily_var.get())
        self.assertTrue(shell.dashboard.daily_btn.instate(["!disabled"]))
        self._close_shell(root, shell)


if __name__ == "__main__":
    unittest.main()
