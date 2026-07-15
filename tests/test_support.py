from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
import os
from pathlib import Path
import sqlite3
import tempfile
from unittest.mock import patch


@contextmanager
def temporary_data_root() -> Iterator[Path]:
    """Route all mutable MandelQuest state to a fresh temporary directory."""

    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory).resolve()
        with patch.dict(os.environ, {"MANDELQUEST_DATA_DIR": str(root)}):
            yield root


@contextmanager
def temporary_database() -> Iterator[Path]:
    """Initialize and yield a fresh schema-v9 application database path."""

    from app import db

    original_connect = db.connect

    @contextmanager
    def closing_connect() -> Iterator[sqlite3.Connection]:
        connection = original_connect()
        try:
            with connection:
                yield connection
        finally:
            connection.close()

    with temporary_data_root() as root:
        with patch.object(db, "connect", closing_connect):
            db.init_db()
            yield root / "app.db"
