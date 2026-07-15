from __future__ import annotations

from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass
import sqlite3

from ..paths import data_dir


@dataclass(frozen=True)
class DbConfig:
    path: str


DbConfigProvider = Callable[[], DbConfig]
DbConfigSource = DbConfig | DbConfigProvider


def _default_db_config() -> DbConfig:
    db_path = data_dir() / "app.db"
    return DbConfig(path=str(db_path))


_db_config_provider: DbConfigProvider = _default_db_config


def get_db_config() -> DbConfig:
    config = _db_config_provider()
    if not isinstance(config, DbConfig):
        raise TypeError("DB config provider must return DbConfig")
    return config


def db_config() -> DbConfig:
    return get_db_config()


def set_db_config(config: DbConfigSource) -> None:
    global _db_config_provider
    if isinstance(config, DbConfig):
        _db_config_provider = lambda: config
        return
    if not callable(config):
        raise TypeError("DB config must be a DbConfig or callable provider")
    _db_config_provider = config


def reset_db_config() -> None:
    global _db_config_provider
    _db_config_provider = _default_db_config


@contextmanager
def override_db_config(config: DbConfigSource) -> Iterator[None]:
    """Temporarily replace process-wide config; overrides must not overlap across threads."""

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
