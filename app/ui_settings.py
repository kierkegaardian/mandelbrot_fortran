from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from pathlib import Path

from .paths import data_dir


@dataclass(frozen=True)
class UiSettings:
    detail_geometry: str | None = None
    show_external_links: bool = False
    accessibility_preset: str = "standard"
    enforce_offline_mode: bool = False
    default_grade_band: str = "K-8"
    summer_mode: bool = False


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
    accessibility_preset = "standard"
    if isinstance(data, dict):
        raw_preset = str(data.get("accessibility_preset", "standard")).strip().lower()
        if raw_preset in {"standard", "large_text", "high_contrast"}:
            accessibility_preset = raw_preset
    enforce_offline_mode = bool(data.get("enforce_offline_mode", False)) if isinstance(data, dict) else False
    default_grade_band = str(data.get("default_grade_band", "K-8")).strip() if isinstance(data, dict) else "K-8"
    if not default_grade_band:
        default_grade_band = "K-8"
    summer_mode = bool(data.get("summer_mode", False)) if isinstance(data, dict) else False
    if isinstance(detail_geometry, str) and detail_geometry.strip():
        return UiSettings(
            detail_geometry=detail_geometry,
            show_external_links=show_external_links,
            accessibility_preset=accessibility_preset,
            enforce_offline_mode=enforce_offline_mode,
            default_grade_band=default_grade_band,
            summer_mode=summer_mode,
        )
    return UiSettings(
        show_external_links=show_external_links,
        accessibility_preset=accessibility_preset,
        enforce_offline_mode=enforce_offline_mode,
        default_grade_band=default_grade_band,
        summer_mode=summer_mode,
    )


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


def save_accessibility_preset(preset: str) -> None:
    value = preset.strip().lower()
    if value not in {"standard", "large_text", "high_contrast"}:
        value = "standard"
    payload = _load_raw_settings()
    payload["accessibility_preset"] = value
    _write_settings(payload)


def save_enforce_offline_mode(enabled: bool) -> None:
    payload = _load_raw_settings()
    payload["enforce_offline_mode"] = bool(enabled)
    _write_settings(payload)


def save_default_grade_band(value: str) -> None:
    cleaned = value.strip() or "K-8"
    payload = _load_raw_settings()
    payload["default_grade_band"] = cleaned
    _write_settings(payload)


def save_summer_mode(enabled: bool) -> None:
    payload = _load_raw_settings()
    payload["summer_mode"] = bool(enabled)
    _write_settings(payload)
