from __future__ import annotations

import argparse
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch


REPO_ROOT = Path(__file__).resolve().parents[1]
TEMPLATE_MANIFESTS = tuple(
    sorted((REPO_ROOT / "scripts" / "template_manifests").glob("*.json"))
)


def _prepare_template_database() -> None:
    from app import db
    from scripts.import_template_manifest import import_manifest

    db.init_db()
    for manifest in TEMPLATE_MANIFESTS:
        import_manifest(manifest)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run tests with disposable app data and no desktop windows by default."
    )
    parser.add_argument(
        "--with-ui",
        action="store_true",
        help="Enable Tk tests; run this mode inside a virtual display such as Xvfb.",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    with tempfile.TemporaryDirectory() as directory:
        test_environment = {
            "MANDELQUEST_DATA_DIR": directory,
            "MANDELQUEST_HEADLESS_TESTS": "0" if args.with_ui else "1",
        }
        with patch.dict(os.environ, test_environment):
            _prepare_template_database()
            suite = unittest.defaultTestLoader.discover("tests")
            result = unittest.TextTestRunner(verbosity=0).run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(main())
