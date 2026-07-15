"""Stable user-facing Family Sync service results."""

from __future__ import annotations

from dataclasses import dataclass

from .sync_client import SyncStatus


@dataclass(frozen=True)
class SyncRunResult:
    attempted: bool
    ok: bool
    enabled: bool
    pending_count: int
    uploaded_count: int
    applied_count: int
    status: SyncStatus | None
    message: str


@dataclass(frozen=True)
class PairingActionResult:
    ok: bool
    family_id: str | None
    pairing_token: str | None
    message: str
