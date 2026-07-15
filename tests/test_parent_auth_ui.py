from __future__ import annotations

import unittest
from unittest.mock import patch

from app import db
from app.time_utils import now_iso
from tests.tk_test_utils import TkAppTestCase, tk_available


@unittest.skipUnless(tk_available(), "Tk display unavailable")
class ParentAuthUiTests(TkAppTestCase):
    def setUp(self) -> None:
        super().setUp()
        db.reset_db_config()
        db.init_db()
        self.parent = db.create_profile("PIN Parent", "parent", now_iso())

    def tearDown(self) -> None:
        db.reset_db_config()
        super().tearDown()

    def _shell(self):
        from app.ui_root import AppShell

        root = self._new_root(withdraw=True)
        return root, AppShell(root, self.parent)

    def test_parent_panel_sets_only_valid_pin(self) -> None:
        root, shell = self._shell()
        shell.parent.parent_pin_var.set("12x")
        shell.parent._set_parent_pin()
        self.assertFalse(db.parent_pin_configured())
        self.assertTrue(self._messagebox_errors)
        self._messagebox_errors.clear()

        shell.parent.parent_pin_var.set("2468")
        shell.parent._set_parent_pin()
        self.assertTrue(db.parent_pin_configured())
        self.assertEqual("", shell.parent.parent_pin_var.get())
        self._close_shell(root, shell)

    def test_wrong_pin_locks_navigation_until_lock_expires(self) -> None:
        db.set_parent_pin(self.parent.id, "2468", now_iso())
        root, shell = self._shell()
        for _attempt in range(db.PIN_LOCK_MAX_ATTEMPTS):
            self._askstring_answers.append("9999")
            self.assertFalse(shell._ensure_parent_access())
        locked, locked_until = db.parent_pin_locked(now_iso())
        self.assertTrue(locked)
        assert locked_until is not None

        self._askstring_answers.append("2468")
        with patch("app.ui_parent_access.now_iso", return_value=locked_until):
            self.assertTrue(shell._ensure_parent_access())

        self._messagebox_errors.clear()
        self._close_shell(root, shell)

    def test_pin_owner_profile_cannot_be_deleted(self) -> None:
        db.set_parent_pin(self.parent.id, "2468", now_iso())
        root, shell = self._shell()
        shell.parent.profile_list.selection_set(0)
        shell.parent._delete_profile()
        self.assertEqual(self.parent.id, db.parent_pin_owner_id())
        self.assertEqual(1, len(db.list_profiles()))
        with self.assertRaisesRegex(ValueError, "another parent profile"):
            db.delete_profile(self.parent.id)
        self.assertTrue(self._messagebox_errors)
        self._messagebox_errors.clear()
        self._close_shell(root, shell)

    def test_cancelled_pin_prompt_returns_to_previous_tab(self) -> None:
        db.set_parent_pin(self.parent.id, "2468", now_iso())
        root, shell = self._shell()
        assert shell._parent_tab_index is not None
        self._askstring_answers.append(None)
        shell.notebook.select(shell._parent_tab_index)
        self._pump(root)
        self.assertEqual(0, shell.notebook.index(shell.notebook.select()))

        self._askstring_answers.append("2468")
        shell.notebook.select(shell._parent_tab_index)
        self._pump(root)
        self.assertEqual(
            shell._parent_tab_index, shell.notebook.index(shell.notebook.select())
        )
        self._close_shell(root, shell)


if __name__ == "__main__":
    unittest.main()
