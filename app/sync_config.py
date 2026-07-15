from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path

from .paths import repo_root

DEFAULT_SYNC_CONFIG = Path("config") / "sync.public.json"


@dataclass(frozen=True)
class SyncConfig:
    profile: str
    server_base_url: str
    server_label: str
    connect_timeout_seconds: int
    read_timeout_seconds: int
    source: str
    path: str

    @property
    def available(self) -> bool:
        return bool(self.server_base_url.strip())


def default_sync_config_path() -> Path:
    return repo_root() / DEFAULT_SYNC_CONFIG


def load_sync_config() -> SyncConfig:
    default_path = default_sync_config_path()
    payload = _load_payload(default_path)
    source = "default"
    config_path = str(default_path)

    override_text = os.environ.get("MANDELQUEST_SYNC_CONFIG", "").strip()
    if override_text:
        override_path = Path(override_text).expanduser().resolve()
        override_payload = _load_payload(override_path)
        if override_payload:
            payload.update(override_payload)
            source = "override"
            config_path = str(override_path)

    return SyncConfig(
        profile=_clean_string(payload.get("profile"), "public-default"),
        server_base_url=_clean_base_url(payload.get("server_base_url")),
        server_label=_clean_string(payload.get("server_label"), "Family sync"),
        connect_timeout_seconds=_clean_timeout(payload.get("connect_timeout_seconds"), 3),
        read_timeout_seconds=_clean_timeout(payload.get("read_timeout_seconds"), 10),
        source=source,
        path=config_path,
    )


def _load_payload(path: Path) -> dict[str, object]:
    try:
        data = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
        return {}
    if isinstance(data, dict):
        return data
    return {}


def _clean_string(value: object, default: str) -> str:
    if isinstance(value, str):
        cleaned = value.strip()
        if cleaned:
            return cleaned
    return default


def _clean_base_url(value: object) -> str:
    if not isinstance(value, str):
        return ""
    cleaned = value.strip().rstrip("/")
    if cleaned.startswith("http://") or cleaned.startswith("https://"):
        return cleaned
    return ""


def _clean_timeout(value: object, default: int) -> int:
    try:
        cleaned = int(value)
    except (TypeError, ValueError):
        return default
    return min(120, max(1, cleaned))
