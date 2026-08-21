from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

from app import sync_config


class SyncConfigTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self._orig_repo_root = sync_config.repo_root
        self._orig_env = os.environ.get("MANDELQUEST_SYNC_CONFIG")
        self._root = Path(self._tmp.name)
        (self._root / "config").mkdir(parents=True, exist_ok=True)
        (self._root / "config" / "sync.public.json").write_text(
            """{
  "profile": "public-default",
  "server_base_url": "",
  "server_label": "Family Sync beta unavailable",
  "connect_timeout_seconds": 3,
  "read_timeout_seconds": 10
}"""
        )

        def _tmp_repo_root() -> Path:
            return self._root

        sync_config.repo_root = _tmp_repo_root

    def tearDown(self) -> None:
        sync_config.repo_root = self._orig_repo_root
        if self._orig_env is None:
            os.environ.pop("MANDELQUEST_SYNC_CONFIG", None)
        else:
            os.environ["MANDELQUEST_SYNC_CONFIG"] = self._orig_env
        self._tmp.cleanup()

    def test_default_config_is_local_only(self) -> None:
        os.environ.pop("MANDELQUEST_SYNC_CONFIG", None)
        config = sync_config.load_sync_config()
        self.assertFalse(config.available)
        self.assertEqual(config.profile, "public-default")
        self.assertEqual(config.server_label, "Family Sync beta unavailable")
        self.assertEqual(config.source, "default")

    def test_override_config_enables_server(self) -> None:
        override = self._root / "sync-override.json"
        override.write_text(
            """{
  "profile": "home-lan",
  "server_base_url": "http://127.0.0.1:8091/",
  "server_label": "Home sync server",
  "connect_timeout_seconds": 5,
  "read_timeout_seconds": 12
}"""
        )
        os.environ["MANDELQUEST_SYNC_CONFIG"] = str(override)

        config = sync_config.load_sync_config()
        self.assertTrue(config.available)
        self.assertEqual(config.profile, "home-lan")
        self.assertEqual(config.server_base_url, "http://127.0.0.1:8091")
        self.assertEqual(config.server_label, "Home sync server")
        self.assertEqual(config.connect_timeout_seconds, 5)
        self.assertEqual(config.read_timeout_seconds, 12)
        self.assertEqual(config.source, "override")


if __name__ == "__main__":
    unittest.main()
