from __future__ import annotations

import os
from pathlib import Path
import shutil
import sys

APP_DIR_NAME = "MandelQuest"
LEGACY_APP_DIR_NAMES = ("HomeschoolMathVisualizer",)


def _is_frozen() -> bool:
    return bool(getattr(sys, "frozen", False))


def _bundle_root() -> Path:
    if _is_frozen():
        meipass = getattr(sys, "_MEIPASS", "")
        if meipass:
            return Path(meipass).resolve()
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[1]


def _user_data_root() -> Path:
    override = os.environ.get("MANDELQUEST_DATA_DIR", "").strip()
    if override:
        return Path(override).expanduser().resolve()
    if not _is_frozen():
        return repo_root() / "data"
    if sys.platform.startswith("win"):
        base = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
    elif sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support"
    else:
        base = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))
    return base / APP_DIR_NAME


def _legacy_user_data_roots() -> tuple[Path, ...]:
    if not _is_frozen():
        return ()
    if sys.platform.startswith("win"):
        base = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
    elif sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support"
    else:
        base = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))
    return tuple(base / name for name in LEGACY_APP_DIR_NAMES)


def _migrate_legacy_data_if_needed(target: Path) -> None:
    if target.exists():
        return
    for legacy in _legacy_user_data_roots():
        if not legacy.exists():
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        try:
            shutil.copytree(legacy, target)
        except Exception:
            # Non-fatal: app will create a fresh data dir if migration fails.
            pass
        return


def repo_root() -> Path:
    return _bundle_root()


def data_dir() -> Path:
    path = _user_data_root()
    _migrate_legacy_data_if_needed(path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def worksheets_dir() -> Path:
    path = data_dir() / "worksheets"
    path.mkdir(parents=True, exist_ok=True)
    return path


def assets_dir() -> Path:
    path = repo_root() / "assets"
    if path.exists():
        return path
    fallback = Path(__file__).resolve().parents[1] / "assets"
    return fallback


def mandelbrot_binary() -> Path:
    root = repo_root()
    candidates = [root / "mandelbrot_gen"]
    if sys.platform.startswith("win"):
        candidates.insert(0, root / "mandelbrot_gen.exe")
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0]
