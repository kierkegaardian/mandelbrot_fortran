"""Validation for Family Sync protocol responses."""

from __future__ import annotations

from .sync_client_types import (
    FamilyLinkResult,
    SyncBatchChange,
    SyncBatchResult,
    SyncEndpointResult,
)


def family_link_from_response(response: SyncEndpointResult) -> FamilyLinkResult:
    if not response.ok:
        return FamilyLinkResult(
            False, None, None, response.error_code, response.error_message, response
        )
    payload = response.data if isinstance(response.data, dict) else {}
    family_id = _clean_required_string(payload.get("family_id"))
    pairing_token = _clean_required_string(payload.get("pairing_token"))
    if family_id is None or pairing_token is None:
        return FamilyLinkResult(
            False,
            None,
            None,
            "invalid_response",
            "Pairing response was missing family_id or pairing_token.",
            response,
        )
    return FamilyLinkResult(True, family_id, pairing_token, None, None, response)


def sync_batch_from_response(response: SyncEndpointResult) -> SyncBatchResult:
    if not response.ok:
        return SyncBatchResult(
            False, 0, [], [], response.error_code, response.error_message, response
        )
    payload = response.data if isinstance(response.data, dict) else {}
    try:
        server_cursor = max(0, int(payload.get("server_cursor", 0)))
    except (TypeError, ValueError):
        return _invalid_batch(response, "Sync response has an invalid cursor.")
    accepted = _clean_int_list(payload.get("accepted_client_change_ids"))
    if accepted is None:
        return _invalid_batch(response, "Sync response has invalid accepted IDs.")
    change_items = payload.get("changes")
    if not isinstance(change_items, list):
        return _invalid_batch(response, "Sync response was missing a valid changes list.")
    changes: list[SyncBatchChange] = []
    for item in change_items:
        parsed = _parse_sync_batch_change(item)
        if parsed is None:
            return _invalid_batch(response, "Sync response contained an invalid change record.")
        changes.append(parsed)
    return SyncBatchResult(True, server_cursor, accepted, changes, None, None, response)


def _invalid_batch(response: SyncEndpointResult, message: str) -> SyncBatchResult:
    return SyncBatchResult(
        False, 0, [], [], "invalid_response", message, response
    )


def _parse_sync_batch_change(item: object) -> SyncBatchChange | None:
    if not isinstance(item, dict):
        return None
    try:
        server_change_id = int(item.get("server_change_id", 0))
    except (TypeError, ValueError):
        return None
    entity_type = _clean_required_string(item.get("entity_type"))
    action = _clean_required_string(item.get("action"))
    entity_sync_id = _clean_required_string(item.get("entity_sync_id"))
    updated_at = _clean_required_string(item.get("updated_at"))
    data = item.get("data")
    if (
        server_change_id < 0
        or entity_type is None
        or action is None
        or entity_sync_id is None
        or updated_at is None
        or not isinstance(data, dict)
    ):
        return None
    return SyncBatchChange(
        server_change_id,
        entity_type,
        action,
        entity_sync_id,
        updated_at,
        data,
    )


def _clean_required_string(value: object) -> str | None:
    return value.strip() if isinstance(value, str) and value.strip() else None


def _clean_int_list(value: object) -> list[int] | None:
    if not isinstance(value, list):
        return None
    out: list[int] = []
    for item in value:
        try:
            parsed = int(item)
        except (TypeError, ValueError):
            return None
        if parsed < 0:
            return None
        out.append(parsed)
    return out
