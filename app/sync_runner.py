"""Manual, parent-triggered Family Sync orchestration."""

from __future__ import annotations

import socket

from . import sync_apply, sync_client, sync_payloads, sync_state, sync_store
from .sync_access import is_parent_profile
from .sync_service_types import PairingActionResult, SyncRunResult
from .time_utils import now_iso


def sync_now(parent_profile_id: int | None = None) -> SyncRunResult:
    pending_count = sync_store.count_pending_changes()
    state = sync_state.load_sync_state()
    if not state.sync_enabled:
        return _run_result(
            attempted=False,
            ok=False,
            enabled=False,
            pending_count=pending_count,
            message="Family sync is disabled on this device.",
        )
    if not is_parent_profile(parent_profile_id):
        return _parent_required_result(pending_count)
    if not state.family_id or not state.pairing_token:
        return _run_result(
            attempted=False,
            ok=False,
            enabled=True,
            pending_count=pending_count,
            message="Start or join a family before choosing Sync now.",
        )
    at_iso = now_iso()
    try:
        state = sync_state.ensure_device_id()
    except sync_state.SyncStateWriteError as exc:
        return _state_failure(pending_count, exc)
    health_status = sync_client.sync_now()
    if not health_status.ok:
        detail = health_status.error_message or health_status.error_code or "Sync probe failed."
        try:
            sync_state.save_sync_probe_result(
                succeeded=False, at_iso=at_iso, error_message=detail
            )
        except sync_state.SyncStateWriteError as exc:
            detail = str(exc)
        return _run_result(
            attempted=True,
            ok=False,
            enabled=True,
            pending_count=pending_count,
            status=health_status,
            message=detail,
        )
    pending_entries = sync_store.list_pending_changes(limit=2000)
    outbound: list[dict[str, object]] = []
    for entry in pending_entries:
        change = sync_payloads.build_outbound_change(entry)
        if change is None:
            sync_store.record_change_failure(
                entry.id, at_iso, "Could not build canonical outbound payload."
            )
            continue
        change["client_change_id"] = entry.id
        outbound.append(change)

    batch = sync_client.sync_batch(
        family_id=state.family_id or "",
        pairing_token=state.pairing_token or "",
        device_id=state.device_id or "",
        since_cursor=state.server_cursor,
        changes=outbound,
    )
    if not batch.ok:
        detail = batch.error_message or batch.error_code or "Batch sync failed."
        return _record_batch_failure(
            pending_count, health_status, at_iso, detail
        )
    if batch.server_cursor < state.server_cursor:
        return _record_batch_failure(
            pending_count,
            health_status,
            at_iso,
            f"Server cursor moved backward from {state.server_cursor} to {batch.server_cursor}; retry retained.",
        )

    sent_ids = {
        int(change["client_change_id"])
        for change in outbound
        if isinstance(change.get("client_change_id"), int)
    }
    accepted_ids = list(
        dict.fromkeys(
            item for item in batch.accepted_client_change_ids if item in sent_ids
        )
    )
    if accepted_ids:
        sync_store.mark_changes_synced(accepted_ids, at_iso)
    remote_payloads = [
        {
            "entity_type": item.entity_type,
            "action": item.action,
            "entity_sync_id": item.entity_sync_id,
            "updated_at": item.updated_at,
            "payload": item.data,
        }
        for item in batch.changes
    ]
    try:
        applied = sync_apply.apply_remote_changes(remote_payloads)
    except Exception as exc:  # noqa: BLE001 - fail closed at batch boundary
        return _record_batch_failure(
            sync_store.count_pending_changes(),
            health_status,
            at_iso,
            f"Remote batch rolled back ({type(exc).__name__}).",
            uploaded_count=len(accepted_ids),
        )
    if applied.deferred:
        return _record_batch_failure(
            sync_store.count_pending_changes(),
            health_status,
            at_iso,
            f"Remote batch deferred {applied.deferred} change(s); cursor retained for retry.",
            uploaded_count=len(accepted_ids),
        )
    try:
        sync_state.save_sync_success(server_cursor=batch.server_cursor, at_iso=at_iso)
    except sync_state.SyncStateWriteError as exc:
        return _run_result(
            attempted=True,
            ok=False,
            enabled=True,
            pending_count=sync_store.count_pending_changes(),
            uploaded_count=len(accepted_ids),
            applied_count=applied.applied,
            status=health_status,
            message=str(exc),
        )
    remaining = sync_store.count_pending_changes()
    message = (
        f"Uploaded {len(accepted_ids)} change(s), applied {applied.applied}, "
        f"skipped {applied.stale_skipped} stale and {applied.unsupported} unsupported; "
        f"{remaining} still queued locally."
    )
    return _run_result(
        attempted=True,
        ok=True,
        enabled=True,
        pending_count=remaining,
        uploaded_count=len(accepted_ids),
        applied_count=applied.applied,
        status=health_status,
        message=message,
    )


def start_family_sync(parent_profile_id: int | None = None) -> PairingActionResult:
    if not is_parent_profile(parent_profile_id):
        return PairingActionResult(False, None, None, "A parent profile is required.")
    try:
        state = sync_state.ensure_device_id()
    except sync_state.SyncStateWriteError as exc:
        return PairingActionResult(False, None, None, str(exc))
    link = sync_client.bootstrap_family(
        device_id=state.device_id or "", device_label=_device_label()
    )
    if not link.ok or not link.family_id or not link.pairing_token:
        detail = link.error_message or link.error_code or "Could not enroll device for family sync."
        _try_record_pairing_failure(detail)
        return PairingActionResult(False, None, None, detail)
    try:
        paired = sync_state.save_sync_pairing(
            family_id=link.family_id, pairing_token=link.pairing_token
        )
    except sync_state.SyncStateWriteError as exc:
        return PairingActionResult(False, None, None, str(exc))
    return PairingActionResult(
        True,
        paired.family_id,
        paired.pairing_token,
        f"Family sync started. Pairing code: {link.pairing_token}",
    )


def join_family_sync(
    pairing_token: str, parent_profile_id: int | None = None
) -> PairingActionResult:
    if not is_parent_profile(parent_profile_id):
        return PairingActionResult(False, None, None, "A parent profile is required.")
    cleaned = pairing_token.strip()
    if not cleaned:
        return PairingActionResult(False, None, None, "Enter a pairing code first.")
    try:
        state = sync_state.ensure_device_id()
    except sync_state.SyncStateWriteError as exc:
        return PairingActionResult(False, None, None, str(exc))
    link = sync_client.join_family(
        pairing_token=cleaned,
        device_id=state.device_id or "",
        device_label=_device_label(),
    )
    if not link.ok or not link.family_id or not link.pairing_token:
        detail = link.error_message or link.error_code or "Could not join family sync."
        _try_record_pairing_failure(detail)
        return PairingActionResult(False, None, None, detail)
    try:
        paired = sync_state.save_sync_pairing(
            family_id=link.family_id, pairing_token=link.pairing_token
        )
    except sync_state.SyncStateWriteError as exc:
        return PairingActionResult(False, None, None, str(exc))
    return PairingActionResult(
        True, paired.family_id, paired.pairing_token, "Family sync joined for this device."
    )


def _try_record_pairing_failure(detail: str) -> None:
    try:
        sync_state.save_sync_probe_result(
            succeeded=False, at_iso=now_iso(), error_message=detail
        )
    except sync_state.SyncStateWriteError:
        return


def _record_batch_failure(
    pending_count: int,
    status,
    at_iso: str,
    detail: str,
    *,
    uploaded_count: int = 0,
) -> SyncRunResult:
    try:
        sync_state.save_sync_probe_result(
            succeeded=False, at_iso=at_iso, error_message=detail
        )
    except sync_state.SyncStateWriteError as exc:
        detail = str(exc)
    return _run_result(
        attempted=True,
        ok=False,
        enabled=True,
        pending_count=pending_count,
        uploaded_count=uploaded_count,
        status=status,
        message=detail,
    )


def _state_failure(pending_count: int, exc: Exception) -> SyncRunResult:
    return _run_result(
        attempted=True,
        ok=False,
        enabled=True,
        pending_count=pending_count,
        message=str(exc),
    )


def _parent_required_result(pending_count: int) -> SyncRunResult:
    return _run_result(
        attempted=False,
        ok=False,
        enabled=True,
        pending_count=pending_count,
        message="A parent profile is required to run Family Sync.",
    )


def _run_result(
    *,
    attempted: bool,
    ok: bool,
    enabled: bool,
    pending_count: int,
    message: str,
    uploaded_count: int = 0,
    applied_count: int = 0,
    status=None,
) -> SyncRunResult:
    return SyncRunResult(
        attempted,
        ok,
        enabled,
        pending_count,
        uploaded_count,
        applied_count,
        status,
        message,
    )


def _device_label() -> str:
    return socket.gethostname().strip() or "mandelquest-device"
