from __future__ import annotations

import argparse
import os
import sys
import tempfile
import unittest
from unittest.mock import patch


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--smoke", action="store_true")
    return parser.parse_args(argv)


def _run_tests() -> bool:
    suite = unittest.defaultTestLoader.discover("tests")
    result = unittest.TextTestRunner(verbosity=0).run(suite)
    return result.wasSuccessful()


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    with tempfile.TemporaryDirectory() as directory:
        with patch.dict(os.environ, {"MANDELQUEST_DATA_DIR": directory}):
            if args.smoke:
                from app.main import _run_smoke_test

                _run_smoke_test()
                print("[smoke-test] OK")
                return 0
            return 0 if _run_tests() else 1


if __name__ == "__main__":
    sys.exit(main())
