"""Typed Family Sync client responses."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class SyncEndpointResult:
    ok: bool
    url: str
    status_code: int | None
    data: Any | None
    raw_text: str | None
    error_code: str | None
    error_message: str | None


@dataclass(frozen=True)
class SyncStatus:
    ok: bool
    config_available: bool
    server_base_url: str
    server_label: str
    profile: str
    config_source: str
    config_path: str
    health: SyncEndpointResult
    api_root: SyncEndpointResult | None
    error_code: str | None
    error_message: str | None


@dataclass(frozen=True)
class FamilyLinkResult:
    ok: bool
    family_id: str | None
    pairing_token: str | None
    error_code: str | None
    error_message: str | None
    response: SyncEndpointResult


@dataclass(frozen=True)
class SyncBatchChange:
    server_change_id: int
    entity_type: str
    action: str
    entity_sync_id: str
    updated_at: str
    data: dict[str, Any]


@dataclass(frozen=True)
class SyncBatchResult:
    ok: bool
    server_cursor: int
    accepted_client_change_ids: list[int]
    changes: list[SyncBatchChange]
    error_code: str | None
    error_message: str | None
    response: SyncEndpointResult
