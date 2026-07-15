from __future__ import annotations

import json
import os
import uuid
from contextlib import suppress
from dataclasses import asdict, dataclass, replace
from pathlib import Path

from .paths import data_dir


@dataclass(frozen=True)
class SyncState:
    sync_enabled: bool = False
    device_id: str | None = None
    family_id: str | None = None
    pairing_token: str | None = None
    server_cursor: int = 0
    last_sync_at: str | None = None
    last_error: str | None = None


class SyncStateWriteError(OSError):
    """The durable sync state could not be replaced safely."""


def load_sync_state() -> SyncState:
    data = _load_raw_state()
    return SyncState(
        sync_enabled=bool(data.get("sync_enabled", False)),
        device_id=_clean_optional_string(data.get("device_id")),
        family_id=_clean_optional_string(data.get("family_id")),
        pairing_token=_clean_optional_string(data.get("pairing_token")),
        server_cursor=_clean_non_negative_int(data.get("server_cursor")),
        last_sync_at=_clean_optional_string(data.get("last_sync_at")),
        last_error=_clean_optional_string(data.get("last_error")),
    )


def save_sync_state(state: SyncState) -> SyncState:
    path = _state_path()
    payload = asdict(state)
    temporary = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    try:
        descriptor = os.open(
            temporary,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL,
            0o600,
        )
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, ensure_ascii=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        os.chmod(path, 0o600)
        if os.name == "posix":
            directory = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
            try:
                os.fsync(directory)
            finally:
                os.close(directory)
    except OSError as exc:
        with suppress(OSError):
            temporary.unlink(missing_ok=True)
        raise SyncStateWriteError(f"Could not save sync state at {path}.") from exc
    return state


def save_sync_enabled(enabled: bool) -> SyncState:
    state = load_sync_state()
    updated = replace(state, sync_enabled=bool(enabled))
    if updated.sync_enabled and not updated.device_id:
        updated = replace(updated, device_id=str(uuid.uuid4()))
    return save_sync_state(updated)


def ensure_device_id() -> SyncState:
    state = load_sync_state()
    if state.device_id:
        return state
    updated = replace(state, device_id=str(uuid.uuid4()))
    return save_sync_state(updated)


def save_sync_pairing(*, family_id: str, pairing_token: str, server_cursor: int = 0) -> SyncState:
    state = ensure_device_id()
    updated = replace(
        state,
        family_id=_clean_optional_string(family_id),
        pairing_token=_clean_optional_string(pairing_token),
        server_cursor=max(0, int(server_cursor)),
        last_error=None,
    )
    return save_sync_state(updated)


def clear_sync_pairing() -> SyncState:
    state = load_sync_state()
    updated = replace(state, family_id=None, pairing_token=None, server_cursor=0)
    return save_sync_state(updated)


def save_sync_server_cursor(server_cursor: int) -> SyncState:
    state = load_sync_state()
    requested = max(0, int(server_cursor))
    if requested < state.server_cursor:
        raise ValueError("Sync server cursor cannot move backward.")
    updated = replace(state, server_cursor=requested)
    return save_sync_state(updated)


def save_sync_probe_result(*, succeeded: bool, at_iso: str, error_message: str | None = None) -> SyncState:
    state = load_sync_state()
    if succeeded:
        updated = replace(state, last_sync_at=at_iso, last_error=None)
    else:
        updated = replace(state, last_error=_clean_optional_string(error_message) or "Sync probe failed.")
    return save_sync_state(updated)


def save_sync_success(*, server_cursor: int, at_iso: str) -> SyncState:
    state = load_sync_state()
    return save_sync_state(
        replace(
            state,
            server_cursor=max(0, int(server_cursor)),
            last_sync_at=at_iso,
            last_error=None,
        )
    )


def save_sync_registration(*, device_id: str, family_id: str) -> SyncState:
    state = load_sync_state()
    updated = replace(
        state,
        device_id=_clean_optional_string(device_id),
        family_id=_clean_optional_string(family_id),
    )
    return save_sync_state(updated)


def _state_path() -> Path:
    return data_dir() / "sync_state.json"


def _load_raw_state() -> dict[str, object]:
    path = _state_path()
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
        return {}
    if isinstance(data, dict):
        return data
    return {}


def _clean_optional_string(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    cleaned = value.strip()
    return cleaned or None


def _clean_non_negative_int(value: object) -> int:
    try:
        cleaned = int(value)
    except (TypeError, ValueError):
        return 0
    return max(0, cleaned)
