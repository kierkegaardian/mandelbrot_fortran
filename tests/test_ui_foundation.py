from __future__ import annotations

import inspect
import unittest
from unittest.mock import patch

from app import db, ui_settings
from app.time_utils import now_iso
from tests.tk_test_utils import TkAppTestCase, tk_available


@unittest.skipUnless(tk_available(), "Tk display unavailable")
class UiFoundationTests(TkAppTestCase):
    def setUp(self) -> None:
        super().setUp()
        db.reset_db_config()
        db.init_db()

    def tearDown(self) -> None:
        db.reset_db_config()
        super().tearDown()

    def _profile(self, role: str):
        return db.create_profile(f"{role}-ui", role, now_iso())

    def test_public_constructor_parameter_names_remain_stable(self) -> None:
        from app.ui_parent import ParentPanel
        from app.ui_quiz import QuizPanel
        from app.ui_root import AppShell

        self.assertEqual(["root", "profile"], list(inspect.signature(AppShell).parameters))
        self.assertEqual(
            ["controls_parent", "view_parent", "profile_getter", "quiz_set_launcher"],
            list(inspect.signature(ParentPanel).parameters),
        )
        self.assertEqual(
            ["controls_parent", "view_parent", "profile_getter"],
            list(inspect.signature(QuizPanel).parameters),
        )

    def test_child_shell_hides_parent_controls_and_navigates(self) -> None:
        from app.ui_root import AppShell

        root = self._new_root(withdraw=True)
        shell = AppShell(root, self._profile("child"))
        self.assertEqual(
            ["Today", "Practice", "Quizzes", "Skill Map"],
            [name for name, _module in shell._modules],
        )
        for index in range(len(shell._modules)):
            shell._select_tab(index)
            shell._show_module(index)
            self._pump(root)
        self._close_shell(root, shell)

    def test_parent_shell_includes_parent_and_fortran_fractal_tabs(self) -> None:
        from app.ui_root import AppShell

        root = self._new_root(withdraw=True)
        shell = AppShell(root, self._profile("parent"))
        labels = [name for name, _module in shell._modules]
        self.assertEqual(
            ["Today", "Practice", "Quizzes", "Skill Map", "Parent", "Bonus Explore"],
            labels,
        )
        self.assertIs(shell.fractal.canvas, shell.fractal.fcanvas.canvas)
        self.assertEqual(
            "NotStarted.Horizontal.TProgressbar",
            shell.dashboard.progress_rows["counting"]["progress_bar"].cget("style"),
        )
        self._close_shell(root, shell)

    def test_offline_setting_is_visible_in_shell_header(self) -> None:
        from app.ui_root import AppShell

        ui_settings.save_show_external_links(True)
        ui_settings.save_enforce_offline_mode(True)
        root = self._new_root(withdraw=True)
        shell = AppShell(root, self._profile("parent"))
        self.assertEqual("Offline mode: enforced", shell.offline_var.get())
        self.assertTrue(shell.arithmetic.lesson_btn.instate(["disabled"]))
        with patch("app.ui_arithmetic.webbrowser.open") as browser_open:
            shell.arithmetic._open_lesson()
        browser_open.assert_not_called()
        self._close_shell(root, shell)

    def test_global_shortcuts_dispatch_to_working_panel_handlers(self) -> None:
        from app.ui_root import AppShell

        root = self._new_root(withdraw=True)
        shell = AppShell(root, self._profile("parent"))

        shell.notebook.select(shell.quiz.controls_frame)
        with patch.object(shell.quiz, "_start_quiz_shortcut") as start_quiz:
            self.assertEqual("break", shell._shortcut_quiz_start())
        start_quiz.assert_called_once_with()

        shell.quiz._questions = []
        with patch.object(shell.quiz, "start_quiz") as start_empty:
            self.assertEqual("break", shell.quiz._submit_or_next_shortcut())
        start_empty.assert_called_once_with()

        shell.quiz._questions = [object()]
        shell.quiz.submit_btn.state(["disabled"])
        shell.quiz.next_btn.state(["!disabled"])
        with patch.object(shell.quiz, "next_question") as next_question:
            self.assertEqual("break", shell.quiz._submit_or_next_shortcut())
        next_question.assert_called_once_with()

        shell.notebook.select(shell.parent.controls_frame)
        with patch.object(shell.parent, "_create_active_item_shortcut") as create:
            self.assertEqual("break", shell._shortcut_parent_create())
        create.assert_called_once_with()
        self.assertEqual("break", shell._shortcut_parent_tab(1))
        self.assertEqual(1, shell.parent.tabs.index(shell.parent.tabs.select()))
        self._close_shell(root, shell)

    def test_fractal_canvas_zoom_math_preserves_fortran_view_contract(self) -> None:
        from app.ui_fractal_canvas import FractalCanvas

        root = self._new_root()
        root.geometry("400x240")
        canvas = FractalCanvas(root)
        canvas.canvas.configure(width=400, height=240)
        self._pump(root)
        original_zoom = canvas.zoom
        self.assertTrue(canvas._zoom_at(200, 120, 1.25))
        self.assertGreater(canvas.zoom, original_zoom)
        canvas.shutdown()


if __name__ == "__main__":
    unittest.main()
