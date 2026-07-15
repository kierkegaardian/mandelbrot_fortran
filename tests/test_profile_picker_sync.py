from __future__ import annotations

import unittest

from app import db, sync_store
from app.ui_profile_picker import ProfilePicker

from tests.tk_test_utils import TkAppTestCase, tk_available


@unittest.skipUnless(tk_available(), "Tk GUI not available")
class ProfilePickerSyncTests(TkAppTestCase):
    def test_first_run_profile_create_enqueues_sync_change(self) -> None:
        db.init_db()
        root = self._new_root(withdraw=True)
        picker = ProfilePicker(root)
        picker.name_entry.insert(0, "First learner")
        picker.role_var.set("child")

        picker._create()
        self._pump(root)

        pending = sync_store.list_pending_changes()
        self.assertEqual(len(pending), 1)
        self.assertEqual(pending[0].entity_type, "profiles")
        self.assertEqual(pending[0].action, "upsert")
        self.assertEqual(pending[0].payload["name"], "First learner")
        picker.win.destroy()


if __name__ == "__main__":
    unittest.main()
