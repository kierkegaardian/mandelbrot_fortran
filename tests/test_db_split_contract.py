from __future__ import annotations

import ast
from collections import Counter
import importlib
import inspect
import json
from pathlib import Path
import tempfile
import textwrap
import typing
import unittest

from app import db
from tests.test_support import temporary_data_root


CONTRACT_PATH = Path(__file__).parent / "fixtures" / "db_v9_split_contract.json"
CONFIG_EXPORTS = {
    "get_db_config",
    "override_db_config",
    "reset_db_config",
    "set_db_config",
}
PERSISTENCE_SQL_CHANGE_ALLOWLIST = {
    "_run_migrations",
    "add_question_result",
    "create_assignment",
    "create_attempt",
    "create_profile",
    "create_quiz_set",
    "evaluate_assignments_for_attempt",
    "init_db",
    "list_assignments",
    "list_attempts",
    "list_profiles",
    "list_quiz_sets",
    "mode_accuracy_by_skill",
    "set_assignment_active",
    "skill_progress_pipeline",
    "update_quiz_set",
}
PACKAGE_MODULES = (
    "app.db._util",
    "app.db.assignments",
    "app.db.attempts",
    "app.db.books",
    "app.db.connection",
    "app.db.daily_goals",
    "app.db.historical",
    "app.db.migration_helpers",
    "app.db.migrations",
    "app.db.parent_auth",
    "app.db.profiles",
    "app.db.progress",
    "app.db.quiz_progress",
    "app.db.quiz_sets",
    "app.db.schema",
    "app.db.school_year",
    "app.db.summer_assessments",
    "app.db.summer_programs",
    "app.db.summer_tasks",
    "app.db.templates",
    "app.db.worksheets",
)
DB_CONSUMER_MODULES = (
    "app.learning_engine",
    "app.question_bank",
    "app.ui_dashboard",
    "app.ui_parent",
    "app.ui_quiz",
    "app.ui_root",
    "scripts.add_templates_from_json",
    "scripts.import_template_manifest",
    "scripts.ingest_textbook",
    "scripts.template_catalog",
    "scripts.template_dry_run",
)


def _contract() -> dict[str, object]:
    return json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))


def _function_args(function: object) -> str:
    source = textwrap.dedent(inspect.getsource(function))
    node = ast.parse(source).body[0]
    if not isinstance(node, ast.FunctionDef):
        raise TypeError(f"expected function source, received {type(node).__name__}")
    return ast.unparse(node.args)


def _function_sql_literals(node: ast.FunctionDef) -> list[str]:
    calls = [
        candidate
        for candidate in ast.walk(node)
        if isinstance(candidate, ast.Call)
        and isinstance(candidate.func, ast.Attribute)
        and candidate.func.attr in {"execute", "executemany", "executescript"}
        and candidate.args
        and isinstance(candidate.args[0], (ast.Constant, ast.JoinedStr))
    ]
    return [ast.unparse(call.args[0]) for call in sorted(calls, key=lambda call: call.lineno)]


def _package_sql_by_function(expected_names: set[str]) -> dict[str, list[str]]:
    literals: dict[str, list[str]] = {}
    package_dir = Path(db.__file__).parent
    for path in sorted(package_dir.glob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in tree.body:
            if isinstance(node, ast.FunctionDef) and node.name in expected_names:
                values = _function_sql_literals(node)
                if values:
                    literals[node.name] = values
    return literals


class DbSplitContractTests(unittest.TestCase):
    def setUp(self) -> None:
        db.reset_db_config()
        self.addCleanup(db.reset_db_config)

    def test_public_exports_and_legacy_signatures_are_frozen(self) -> None:
        signatures = _contract()["public_signatures"]
        assert isinstance(signatures, dict)
        expected_exports = {"DbConfig", *signatures, *CONFIG_EXPORTS}
        self.assertTrue(expected_exports.issubset(db.__all__))
        self.assertEqual(tuple(sorted(db.__all__)), db.__all__)

        for name, expected_args in signatures.items():
            with self.subTest(name=name):
                self.assertTrue(hasattr(db, name))
                self.assertEqual(expected_args, _function_args(getattr(db, name)))

    def test_new_config_helpers_have_typed_stable_signatures(self) -> None:
        expected = {
            "get_db_config": "",
            "override_db_config": "config: DbConfigSource",
            "reset_db_config": "",
            "set_db_config": "config: DbConfigSource",
        }
        actual = {name: _function_args(getattr(db, name)) for name in expected}
        self.assertEqual(expected, actual)

    def test_unchanged_sql_literals_remain_bound_to_original_functions(self) -> None:
        expected = _contract()["sql_literals_by_function"]
        assert isinstance(expected, dict)
        stable_expected = {
            name: literals
            for name, literals in expected.items()
            if name not in PERSISTENCE_SQL_CHANGE_ALLOWLIST
        }
        actual = _package_sql_by_function(set(stable_expected))
        self.assertEqual(set(stable_expected), set(actual))

        expected_all: Counter[str] = Counter()
        actual_all: Counter[str] = Counter()
        for name, expected_literals in stable_expected.items():
            with self.subTest(function=name):
                self.assertIsInstance(expected_literals, list)
                self.assertEqual(expected_literals, actual[name])
                expected_all.update(expected_literals)
                actual_all.update(actual[name])
        self.assertEqual(expected_all, actual_all)

    def test_package_and_broad_consumers_import(self) -> None:
        with temporary_data_root():
            for module_name in (*PACKAGE_MODULES, *DB_CONSUMER_MODULES):
                with self.subTest(module=module_name):
                    self.assertIsNotNone(importlib.import_module(module_name))

    def test_all_package_function_annotations_resolve(self) -> None:
        for module_name in PACKAGE_MODULES:
            module = importlib.import_module(module_name)
            for name, value in vars(module).items():
                if inspect.isfunction(value) and value.__module__ == module_name:
                    with self.subTest(module=module_name, function=name):
                        typing.get_type_hints(value)

    def test_context_override_routes_all_database_work(self) -> None:
        with temporary_data_root() as default_root:
            db.reset_db_config()
            original = db.get_db_config()
            self.assertEqual(default_root / "app.db", Path(original.path))

            with tempfile.TemporaryDirectory() as directory:
                outer_path = Path(directory) / "outer.db"
                inner_path = Path(directory) / "inner.db"
                with db.override_db_config(db.DbConfig(path=str(outer_path))):
                    self.assertEqual(outer_path, Path(db.get_db_config().path))
                    with db.override_db_config(lambda: db.DbConfig(path=str(inner_path))):
                        self.assertEqual(inner_path, Path(db.db_config().path))
                    self.assertEqual(outer_path, Path(db.get_db_config().path))

                    db.init_db()
                    profile = db.create_profile("Contract Child", "child", "2026-07-15T00:00:00+00:00")
                    connection = db.connect()
                    try:
                        row = connection.execute(
                            "SELECT name FROM profiles WHERE id = ?",
                            (profile.id,),
                        ).fetchone()
                        version = connection.execute(
                            "SELECT version FROM schema_version WHERE id = 1"
                        ).fetchone()
                    finally:
                        connection.close()

                self.assertTrue(outer_path.exists())
                self.assertFalse(inner_path.exists())

            self.assertEqual(original, db.get_db_config())
            self.assertFalse((default_root / "app.db").exists())
            self.assertIsNotNone(row)
            self.assertEqual("Contract Child", str(row["name"]))
            self.assertIsNotNone(version)
            self.assertEqual(17, int(version["version"]))


if __name__ == "__main__":
    unittest.main()
