from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from app import ui_settings


class UiSettingsTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self._orig_data_dir = ui_settings.data_dir
        tmp_root = Path(self._tmp.name)

        def _tmp_data_dir() -> Path:
            tmp_root.mkdir(parents=True, exist_ok=True)
            return tmp_root

        ui_settings.data_dir = _tmp_data_dir

    def tearDown(self) -> None:
        ui_settings.data_dir = self._orig_data_dir
        self._tmp.cleanup()

    def test_defaults_include_offline_and_accessibility_fields(self) -> None:
        settings = ui_settings.load_ui_settings()
        self.assertEqual(settings.accessibility_preset, "standard")
        self.assertFalse(settings.enforce_offline_mode)
        self.assertEqual(settings.default_grade_band, "K-8")
        self.assertFalse(settings.summer_mode)

    def test_save_helpers_persist_new_fields(self) -> None:
        ui_settings.save_enforce_offline_mode(True)
        ui_settings.save_accessibility_preset("large_text")
        ui_settings.save_default_grade_band("6-8")
        ui_settings.save_summer_mode(True)
        loaded = ui_settings.load_ui_settings()
        self.assertTrue(loaded.enforce_offline_mode)
        self.assertEqual(loaded.accessibility_preset, "large_text")
        self.assertEqual(loaded.default_grade_band, "6-8")
        self.assertTrue(loaded.summer_mode)


if __name__ == "__main__":
    unittest.main()
