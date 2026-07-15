"""Small JSON-over-HTTP transport for Family Sync."""

from __future__ import annotations

import json
import socket
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .sync_client_types import SyncEndpointResult


def request_json(
    url: str,
    timeout_seconds: float,
    payload: dict[str, Any] | None = None,
) -> SyncEndpointResult:
    raw_payload = None
    method = "GET"
    headers = {"Accept": "application/json"}
    if payload is not None:
        raw_payload = json.dumps(
            payload, ensure_ascii=True, sort_keys=True
        ).encode("utf-8")
        method = "POST"
        headers["Content-Type"] = "application/json"
    request = Request(url, data=raw_payload, headers=headers, method=method)
    try:
        with urlopen(request, timeout=timeout_seconds) as response:
            body = response.read()
            status_code = int(getattr(response, "status", response.getcode()))
            ok = 200 <= status_code < 300
            return _build_result(
                url=url,
                status_code=status_code,
                raw_bytes=body,
                ok_status=ok,
                error_code=None if ok else f"http_{status_code}",
                error_message=None if ok else response.reason,
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
            error_code=("timeout" if isinstance(exc.reason, socket.timeout) else "network_error"),
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
            False, url, status_code, None, raw_text, "invalid_json", parse_error
        )
    parsed_ok = ok_status and parse_error is None
    return SyncEndpointResult(
        ok=parsed_ok,
        url=url,
        status_code=status_code,
        data=data if parse_error is None else None,
        raw_text=raw_text,
        error_code=None if parsed_ok else error_code,
        error_message=None if parsed_ok else error_message,
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
