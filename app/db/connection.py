from __future__ import annotations

from collections.abc import Callable, Iterator
from contextlib import contextmanager
import sqlite3
from dataclasses import dataclass

from ..paths import data_dir


@dataclass(frozen=True)
class DbConfig:
    path: str


_DbConfigProvider = Callable[[], DbConfig]
_DbConfigSource = DbConfig | _DbConfigProvider


def _default_db_config() -> DbConfig:
    db_path = data_dir() / "app.db"
    return DbConfig(path=str(db_path))


_db_config_provider: _DbConfigProvider = _default_db_config


def get_db_config() -> DbConfig:
    config = _db_config_provider()
    if not isinstance(config, DbConfig):
        raise TypeError("DB config provider must return DbConfig")
    return config


def db_config() -> DbConfig:
    """Return the active config while preserving the existing public callable."""
    return get_db_config()


def set_db_config(config: _DbConfigSource) -> None:
    """Set the process-wide DB config source used by every connection."""
    global _db_config_provider
    if isinstance(config, DbConfig):
        _db_config_provider = lambda: config
        return
    if not callable(config):
        raise TypeError("DB config must be a DbConfig or callable provider")
    _db_config_provider = config


def reset_db_config() -> None:
    """Restore data-dir-based DB configuration."""
    global _db_config_provider
    _db_config_provider = _default_db_config


@contextmanager
def override_db_config(config: _DbConfigSource) -> Iterator[None]:
    """Temporarily replace the shared DB config source, including nested use."""
    global _db_config_provider
    previous_provider = _db_config_provider
    set_db_config(config)
    try:
        yield
    finally:
        _db_config_provider = previous_provider


def connect() -> sqlite3.Connection:
    cfg = get_db_config()
    conn = sqlite3.connect(cfg.path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


@contextmanager
def managed_connection() -> Iterator[sqlite3.Connection]:
    conn = connect()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
