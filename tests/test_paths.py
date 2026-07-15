from __future__ import annotations

import unittest
from unittest.mock import patch

from app.main import _parse_args, _run_smoke_test
from app.paths import data_dir
from tests.test_support import temporary_data_root


class DataPathTests(unittest.TestCase):
    def test_environment_override_owns_all_runtime_data(self) -> None:
        with temporary_data_root() as root:
            self.assertEqual(root, data_dir())
            self.assertTrue(root.is_dir())

    def test_gui_startup_ignores_launcher_arguments(self) -> None:
        args = _parse_args(["-psn_0_12345"])
        self.assertFalse(args.smoke_test)

    def test_smoke_requires_explicit_data_root(self) -> None:
        with patch.dict("os.environ", {"MANDELQUEST_DATA_DIR": ""}):
            with self.assertRaisesRegex(RuntimeError, "MANDELQUEST_DATA_DIR"):
                _run_smoke_test()


if __name__ == "__main__":
    unittest.main()
