from __future__ import annotations

import json
import socket
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .sync_config import SyncConfig, load_sync_config


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


@dataclass(frozen=True)
class SyncClient:
    config: SyncConfig

    @classmethod
    def from_env(cls) -> SyncClient:
        return cls(load_sync_config())

    def healthcheck(self) -> SyncEndpointResult:
        return self._request_json("/health", timeout_seconds=self.config.connect_timeout_seconds)

    def api_root(self) -> SyncEndpointResult:
        return self._request_json("/api/v1", timeout_seconds=self.config.read_timeout_seconds)

    def bootstrap_family(self, *, device_id: str, device_label: str) -> FamilyLinkResult:
        response = self._request_json(
            "/api/v1/family/bootstrap",
            timeout_seconds=self.config.read_timeout_seconds,
            payload={"device_id": device_id, "device_label": device_label},
        )
        return _family_link_from_response(response)

    def join_family(self, *, pairing_token: str, device_id: str, device_label: str) -> FamilyLinkResult:
        response = self._request_json(
            "/api/v1/family/join",
            timeout_seconds=self.config.read_timeout_seconds,
            payload={
                "pairing_token": pairing_token,
                "device_id": device_id,
                "device_label": device_label,
            },
        )
        return _family_link_from_response(response)

    def sync_batch(
        self,
        *,
        family_id: str,
        pairing_token: str,
        device_id: str,
        since_cursor: int,
        changes: list[dict[str, Any]],
    ) -> SyncBatchResult:
        response = self._request_json(
            "/api/v1/sync",
            timeout_seconds=self.config.read_timeout_seconds,
            payload={
                "family_id": family_id,
                "pairing_token": pairing_token,
                "device_id": device_id,
                "since_cursor": int(since_cursor),
                "changes": changes,
            },
        )
        return _sync_batch_from_response(response)

    def sync_now(self) -> SyncStatus:
        health = self.healthcheck()
        if not health.ok:
            return _status_from_results(self.config, health, None)
        api_root = self.api_root()
        return _status_from_results(self.config, health, api_root)

    def _endpoint(self, path: str) -> str:
        return f"{self.config.server_base_url.rstrip('/')}{path}"

    def _request_json(
        self,
        path: str,
        *,
        timeout_seconds: int,
        payload: dict[str, Any] | None = None,
    ) -> SyncEndpointResult:
        if not self.config.available:
            return SyncEndpointResult(
                ok=False,
                url="",
                status_code=None,
                data=None,
                raw_text=None,
                error_code="missing_config",
                error_message="Sync server is not configured.",
            )
        return _request_json(self._endpoint(path), float(timeout_seconds), payload)


def healthcheck(config: SyncConfig | None = None) -> SyncEndpointResult:
    return SyncClient(config or load_sync_config()).healthcheck()


def api_root(config: SyncConfig | None = None) -> SyncEndpointResult:
    return SyncClient(config or load_sync_config()).api_root()


def sync_now(config: SyncConfig | None = None) -> SyncStatus:
    return SyncClient(config or load_sync_config()).sync_now()


def bootstrap_family(
    *,
    device_id: str,
    device_label: str,
    config: SyncConfig | None = None,
) -> FamilyLinkResult:
    return SyncClient(config or load_sync_config()).bootstrap_family(
        device_id=device_id,
        device_label=device_label,
    )


def join_family(
    *,
    pairing_token: str,
    device_id: str,
    device_label: str,
    config: SyncConfig | None = None,
) -> FamilyLinkResult:
    return SyncClient(config or load_sync_config()).join_family(
        pairing_token=pairing_token,
        device_id=device_id,
        device_label=device_label,
    )


def sync_batch(
    *,
    family_id: str,
    pairing_token: str,
    device_id: str,
    since_cursor: int,
    changes: list[dict[str, Any]],
    config: SyncConfig | None = None,
) -> SyncBatchResult:
    return SyncClient(config or load_sync_config()).sync_batch(
        family_id=family_id,
        pairing_token=pairing_token,
        device_id=device_id,
        since_cursor=since_cursor,
        changes=changes,
    )


def _status_from_results(
    config: SyncConfig,
    health: SyncEndpointResult,
    api_root: SyncEndpointResult | None,
) -> SyncStatus:
    ok = health.ok and (api_root.ok if api_root is not None else False)
    error = api_root if api_root is not None and not api_root.ok else health
    return SyncStatus(
        ok=ok,
        config_available=config.available,
        server_base_url=config.server_base_url,
        server_label=config.server_label,
        profile=config.profile,
        config_source=config.source,
        config_path=config.path,
        health=health,
        api_root=api_root,
        error_code=None if ok else error.error_code,
        error_message=None if ok else error.error_message,
    )


def _request_json(url: str, timeout_seconds: float, payload: dict[str, Any] | None = None) -> SyncEndpointResult:
    raw_payload = None
    method = "GET"
    headers = {"Accept": "application/json"}
    if payload is not None:
        raw_payload = json.dumps(payload, ensure_ascii=True, sort_keys=True).encode("utf-8")
        method = "POST"
        headers["Content-Type"] = "application/json"
    request = Request(url, data=raw_payload, headers=headers, method=method)
    try:
        with urlopen(request, timeout=timeout_seconds) as response:
            body = response.read()
            status_code = int(getattr(response, "status", response.getcode()))
            return _build_result(
                url=url,
                status_code=status_code,
                raw_bytes=body,
                ok_status=200 <= status_code < 300,
                error_code=None if 200 <= status_code < 300 else f"http_{status_code}",
                error_message=None if 200 <= status_code < 300 else response.reason,
            )
    except HTTPError as exc:
        body = exc.read()
        exc.close()
        return _build_result(
            url=url,
            status_code=int(exc.code),
            raw_bytes=body,
            ok_status=False,
            error_code=f"http_{exc.code}",
            error_message=str(exc.reason) if exc.reason else f"HTTP {exc.code}",
        )
    except URLError as exc:
        return SyncEndpointResult(
            ok=False,
            url=url,
            status_code=None,
            data=None,
            raw_text=None,
            error_code=_network_error_code(exc.reason),
            error_message=str(exc.reason),
        )
    except socket.timeout:
        return SyncEndpointResult(
            ok=False,
            url=url,
            status_code=None,
            data=None,
            raw_text=None,
            error_code="timeout",
            error_message="Request timed out.",
        )


def _build_result(
    *,
    url: str,
    status_code: int,
    raw_bytes: bytes,
    ok_status: bool,
    error_code: str | None,
    error_message: str | None,
) -> SyncEndpointResult:
    raw_text = _decode_text(raw_bytes)
    data, parse_error = _parse_json(raw_text)
    if ok_status and parse_error is not None:
        return SyncEndpointResult(
            ok=False,
            url=url,
            status_code=status_code,
            data=None,
            raw_text=raw_text,
            error_code="invalid_json",
            error_message=parse_error,
        )
    return SyncEndpointResult(
        ok=ok_status and parse_error is None,
        url=url,
        status_code=status_code,
        data=data if parse_error is None else None,
        raw_text=raw_text,
        error_code=error_code if not (ok_status and parse_error is None) else None,
        error_message=error_message if not (ok_status and parse_error is None) else None,
    )


def _decode_text(raw_bytes: bytes) -> str:
    if not raw_bytes:
        return ""
    for encoding in ("utf-8", "latin-1"):
        try:
            return raw_bytes.decode(encoding)
        except UnicodeDecodeError:
            continue
    return raw_bytes.decode("utf-8", errors="replace")


def _parse_json(raw_text: str) -> tuple[Any | None, str | None]:
    cleaned = raw_text.strip()
    if not cleaned:
        return None, "Response body was empty."
    try:
        return json.loads(cleaned), None
    except json.JSONDecodeError as exc:
        return None, f"Invalid JSON response: {exc.msg}."


def _network_error_code(reason: object) -> str:
    if isinstance(reason, socket.timeout):
        return "timeout"
    return "network_error"


def _family_link_from_response(response: SyncEndpointResult) -> FamilyLinkResult:
    if not response.ok:
        return FamilyLinkResult(
            ok=False,
            family_id=None,
            pairing_token=None,
            error_code=response.error_code,
            error_message=response.error_message,
            response=response,
        )
    payload = response.data if isinstance(response.data, dict) else {}
    family_id = _clean_required_string(payload.get("family_id"))
    pairing_token = _clean_required_string(payload.get("pairing_token"))
    if family_id is None or pairing_token is None:
        return FamilyLinkResult(
            ok=False,
            family_id=None,
            pairing_token=None,
            error_code="invalid_response",
            error_message="Pairing response was missing family_id or pairing_token.",
            response=response,
        )
    return FamilyLinkResult(
        ok=True,
        family_id=family_id,
        pairing_token=pairing_token,
        error_code=None,
        error_message=None,
        response=response,
    )


def _sync_batch_from_response(response: SyncEndpointResult) -> SyncBatchResult:
    if not response.ok:
        return SyncBatchResult(
            ok=False,
            server_cursor=0,
            accepted_client_change_ids=[],
            changes=[],
            error_code=response.error_code,
            error_message=response.error_message,
            response=response,
        )
    payload = response.data if isinstance(response.data, dict) else {}
    try:
        server_cursor = max(0, int(payload.get("server_cursor", 0)))
    except (TypeError, ValueError):
        server_cursor = 0
    accepted = _clean_int_list(payload.get("accepted_client_change_ids"))
    change_items = payload.get("changes")
    if not isinstance(change_items, list):
        return SyncBatchResult(
            ok=False,
            server_cursor=server_cursor,
            accepted_client_change_ids=accepted,
            changes=[],
            error_code="invalid_response",
            error_message="Sync response was missing a valid changes list.",
            response=response,
        )
    changes: list[SyncBatchChange] = []
    for item in change_items:
        parsed = _parse_sync_batch_change(item)
        if parsed is None:
            return SyncBatchResult(
                ok=False,
                server_cursor=server_cursor,
                accepted_client_change_ids=accepted,
                changes=[],
                error_code="invalid_response",
                error_message="Sync response contained an invalid change record.",
                response=response,
            )
        changes.append(parsed)
    return SyncBatchResult(
        ok=True,
        server_cursor=server_cursor,
        accepted_client_change_ids=accepted,
        changes=changes,
        error_code=None,
        error_message=None,
        response=response,
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
        entity_type is None
        or action is None
        or entity_sync_id is None
        or updated_at is None
        or not isinstance(data, dict)
    ):
        return None
    return SyncBatchChange(
        server_change_id=max(0, server_change_id),
        entity_type=entity_type,
        action=action,
        entity_sync_id=entity_sync_id,
        updated_at=updated_at,
        data=data,
    )


def _clean_required_string(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    cleaned = value.strip()
    return cleaned or None


def _clean_int_list(value: object) -> list[int]:
    if not isinstance(value, list):
        return []
    out: list[int] = []
    for item in value:
        try:
            out.append(int(item))
        except (TypeError, ValueError):
            return []
    return out
