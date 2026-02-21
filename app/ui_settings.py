from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from pathlib import Path

from .paths import data_dir


@dataclass(frozen=True)
class UiSettings:
    detail_geometry: str | None = None
    show_external_links: bool = False


def _settings_path() -> Path:
    return data_dir() / "ui_settings.json"


def _load_raw_settings() -> dict[str, object]:
    path = _settings_path()
    if not path.exists():
        return {}
    try:
        raw = path.read_text()
        data = json.loads(raw)
    except (OSError, json.JSONDecodeError):
        return {}
    if isinstance(data, dict):
        return data
    return {}


def _write_settings(payload: dict[str, object]) -> None:
    path = _settings_path()
    try:
        path.write_text(json.dumps(payload, indent=2, ensure_ascii=True))
    except OSError:
        return


def load_ui_settings() -> UiSettings:
    data = _load_raw_settings()
    detail_geometry = data.get("detail_geometry") if isinstance(data, dict) else None
    show_external_links = bool(data.get("show_external_links", False)) if isinstance(data, dict) else False
    if isinstance(detail_geometry, str) and detail_geometry.strip():
        return UiSettings(detail_geometry=detail_geometry, show_external_links=show_external_links)
    return UiSettings(show_external_links=show_external_links)


def save_ui_settings(settings: UiSettings) -> None:
    payload = _load_raw_settings()
    payload.update(asdict(settings))
    _write_settings(payload)


def save_detail_geometry(geometry: str) -> None:
    payload = _load_raw_settings()
    payload["detail_geometry"] = geometry
    _write_settings(payload)


def save_show_external_links(enabled: bool) -> None:
    payload = _load_raw_settings()
    payload["show_external_links"] = bool(enabled)
    _write_settings(payload)
