from __future__ import annotations

import json
import os
from pathlib import Path
import unittest
from tkinter import ttk
from unittest.mock import patch

from app import db, sync_service, sync_state
from app.time_utils import now_iso
from app.ui_family_sync import FAMILY_SYNC_BETA_TITLE, FAMILY_SYNC_PRIVACY_COPY
from app.ui_parent import ParentPanel

from tests.tk_test_utils import TkAppTestCase, tk_available


@unittest.skipUnless(tk_available(), "Tk GUI not available")
class FamilySyncUiCopyTests(TkAppTestCase):
    def setUp(self) -> None:
        super().setUp()
        self._old_sync_config = os.environ.pop("MANDELQUEST_SYNC_CONFIG", None)
        db.init_db()
        self.parent = sync_service.create_profile("Parent", "parent", now_iso())

    def tearDown(self) -> None:
        os.environ.pop("MANDELQUEST_SYNC_CONFIG", None)
        if self._old_sync_config is not None:
            os.environ["MANDELQUEST_SYNC_CONFIG"] = self._old_sync_config
        super().tearDown()

    def test_public_build_marks_sync_beta_and_keeps_it_gated(self) -> None:
        root = self._new_root(withdraw=True)
        controls = ttk.Frame(root)
        view = ttk.Frame(root)
        panel = ParentPanel(controls, view, lambda: self.parent)

        self._pump(root)

        settings = panel.family_sync
        self.assertEqual("Family Sync", panel.tabs.tab(panel.sync_tab, "text"))
        self.assertIn(FAMILY_SYNC_BETA_TITLE, self._texts_under(panel.sync_tab))
        self.assertEqual("Enable family sync on this device (optional)", settings.sync_enabled_btn.cget("text"))
        self.assertEqual("Sync now", settings.sync_now_btn.cget("text"))
        self.assertEqual(FAMILY_SYNC_PRIVACY_COPY, settings.privacy_label.cget("text"))
        self.assertIn("profiles", FAMILY_SYNC_PRIVACY_COPY)
        self.assertIn("parent PIN", FAMILY_SYNC_PRIVACY_COPY)
        self.assertTrue(settings.sync_enabled_btn.instate(["disabled"]))
        self.assertIn("Local-only is active", settings.sync_detail_var.get())
        self.assertFalse(sync_state.load_sync_state().sync_enabled)

    def test_parent_can_turn_sync_on_run_it_manually_and_turn_it_off(self) -> None:
        self._configure_sync_server()
        root = self._new_root(withdraw=True)
        panel = ParentPanel(ttk.Frame(root), ttk.Frame(root), lambda: self.parent)
        settings = panel.family_sync
        self._pump(root)

        self.assertFalse(settings.sync_enabled_btn.instate(["disabled"]))
        self.assertTrue(settings.sync_now_btn.instate(["disabled"]))

        settings.sync_enabled_btn.invoke()
        self._pump(root)
        self.assertTrue(sync_state.load_sync_state().sync_enabled)
        self.assertEqual("Family sync is on (uncheck to turn it off)", settings.sync_enabled_btn.cget("text"))
        self.assertFalse(settings.sync_start_btn.instate(["disabled"]))
        self.assertTrue(settings.sync_now_btn.instate(["disabled"]))

        sync_state.save_sync_pairing(family_id="family-1", pairing_token="pair-123")
        settings.refresh()
        self.assertFalse(settings.sync_now_btn.instate(["disabled"]))
        result = sync_service.SyncRunResult(
            attempted=True,
            ok=True,
            enabled=True,
            pending_count=0,
            uploaded_count=1,
            applied_count=0,
            status=None,
            message="Uploaded 1 change.",
        )
        with patch("app.ui_family_sync.sync_service.sync_now", return_value=result) as sync_now:
            settings.sync_now_btn.invoke()
            self._pump(root)
        sync_now.assert_called_once_with(self.parent.id)

        settings.sync_enabled_btn.invoke()
        self._pump(root)
        state = sync_state.load_sync_state()
        self.assertFalse(state.sync_enabled)
        self.assertEqual("family-1", state.family_id)
        self.assertEqual("Enable family sync on this device (optional)", settings.sync_enabled_btn.cget("text"))
        self.assertTrue(settings.sync_now_btn.instate(["disabled"]))
        self.assertIn("no changes are sent", settings.sync_error_var.get())

    def test_child_profile_cannot_manage_sync_settings(self) -> None:
        self._configure_sync_server()
        child = sync_service.create_profile("Child", "child", now_iso())
        root = self._new_root(withdraw=True)
        panel = ParentPanel(ttk.Frame(root), ttk.Frame(root), lambda: child)
        self._pump(root)

        settings = panel.family_sync
        self.assertTrue(settings.sync_enabled_btn.instate(["disabled"]))
        self.assertTrue(settings.sync_start_btn.instate(["disabled"]))
        self.assertTrue(settings.sync_now_btn.instate(["disabled"]))
        self.assertIn("only from a parent profile", settings.sync_status_var.get())
        self.assertFalse(sync_state.load_sync_state().sync_enabled)

    def test_state_write_failure_does_not_claim_sync_was_enabled(self) -> None:
        self._configure_sync_server()
        root = self._new_root(withdraw=True)
        panel = ParentPanel(ttk.Frame(root), ttk.Frame(root), lambda: self.parent)
        settings = panel.family_sync
        self._pump(root)
        settings.sync_enabled_var.set(True)

        with patch(
            "app.ui_family_sync.save_sync_enabled",
            side_effect=sync_state.SyncStateWriteError("state write failed"),
        ):
            settings._toggle_family_sync()

        self.assertFalse(sync_state.load_sync_state().sync_enabled)
        self.assertFalse(settings.sync_enabled_var.get())
        self.assertTrue(
            any("state write failed" in message for message in self._messagebox_errors)
        )

    def _configure_sync_server(self) -> None:
        config_path = Path(self._tmp.name) / "sync.json"
        config_path.write_text(
            json.dumps(
                {
                    "profile": "test",
                    "server_base_url": "http://127.0.0.1:8091",
                    "server_label": "Test family sync",
                }
            ),
            encoding="utf-8",
        )
        os.environ["MANDELQUEST_SYNC_CONFIG"] = str(config_path)


if __name__ == "__main__":
    unittest.main()
