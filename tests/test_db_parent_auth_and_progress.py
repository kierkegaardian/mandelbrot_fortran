from __future__ import annotations

import gc
import tempfile
import unittest
import warnings

from app import db


class DbParentAuthAndProgressTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        tmp_path = self._tmp.name

        def _tmp_config() -> db.DbConfig:
            return db.DbConfig(path=f"{tmp_path}/test_app.db")

        self.enterContext(db.override_db_config(_tmp_config))
        db.init_db()
        self.parent = db.create_profile("Parent", "parent", "2026-03-02T00:00:00+00:00")
        self.child = db.create_profile("Child", "child", "2026-03-02T00:00:00+00:00")

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_parent_pin_roundtrip_and_lockout(self) -> None:
        db.set_parent_pin(self.parent.id, "1234", "2026-03-02T00:00:00+00:00")
        self.assertTrue(db.parent_pin_configured())
        self.assertTrue(db.verify_parent_pin("1234", "2026-03-02T00:00:05+00:00"))
        self.assertFalse(db.parent_pin_locked("2026-03-02T00:00:05+00:00")[0])

        for _ in range(4):
            self.assertFalse(db.verify_parent_pin("9999", "2026-03-02T00:01:00+00:00"))
            locked_until = db.record_parent_auth_failure("2026-03-02T00:01:00+00:00")
            self.assertIsNone(locked_until)

        self.assertFalse(db.verify_parent_pin("9999", "2026-03-02T00:01:10+00:00"))
        locked_until = db.record_parent_auth_failure("2026-03-02T00:01:10+00:00")
        self.assertIsNotNone(locked_until)
        self.assertTrue(db.parent_pin_locked("2026-03-02T00:01:11+00:00")[0])
        self.assertFalse(db.verify_parent_pin("1234", "2026-03-02T00:01:12+00:00"))

        db.clear_parent_lock("2026-03-02T00:02:00+00:00")
        self.assertFalse(db.parent_pin_locked("2026-03-02T00:02:01+00:00")[0])
        self.assertTrue(db.verify_parent_pin("1234", "2026-03-02T00:02:01+00:00"))

    def test_set_parent_pin_requires_parent_role(self) -> None:
        with self.assertRaises(ValueError):
            db.set_parent_pin(self.child.id, "1234", "2026-03-02T00:00:00+00:00")

    def test_quiz_progress_save_load_and_clear(self) -> None:
        state = '{"v":1,"x":"y"}'
        attempt_id = db.save_quiz_progress(
            self.child.id,
            None,
            2,
            state,
            "2026-03-02T00:10:00+00:00",
        )
        loaded = db.load_quiz_progress(self.child.id)
        self.assertIsNotNone(loaded)
        assert loaded is not None
        self.assertEqual(loaded[0], attempt_id)
        self.assertEqual(loaded[1], 2)
        self.assertEqual(loaded[2], state)

        db.save_quiz_progress(
            self.child.id,
            attempt_id,
            3,
            '{"v":1,"x":"z"}',
            "2026-03-02T00:11:00+00:00",
        )
        loaded = db.load_quiz_progress(self.child.id)
        self.assertIsNotNone(loaded)
        assert loaded is not None
        self.assertEqual(loaded[1], 3)
        self.assertEqual(loaded[2], '{"v":1,"x":"z"}')

        db.clear_quiz_progress(attempt_id)
        self.assertIsNone(db.load_quiz_progress(self.child.id))

    def test_init_db_emits_no_resource_warning(self) -> None:
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always", ResourceWarning)
            for _ in range(5):
                db.init_db()
            gc.collect()
        resource_warnings = [item for item in caught if issubclass(item.category, ResourceWarning)]
        self.assertEqual(resource_warnings, [])


if __name__ == "__main__":
    unittest.main()
