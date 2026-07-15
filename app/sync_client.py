"""Public Family Sync HTTP client boundary."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .sync_client_parsing import family_link_from_response, sync_batch_from_response
from .sync_client_types import (
    FamilyLinkResult,
    SyncBatchChange,
    SyncBatchResult,
    SyncEndpointResult,
    SyncStatus,
)
from .sync_config import SyncConfig, load_sync_config
from .sync_http import request_json


@dataclass(frozen=True)
class SyncClient:
    config: SyncConfig

    @classmethod
    def from_env(cls) -> "SyncClient":
        return cls(load_sync_config())

    def healthcheck(self) -> SyncEndpointResult:
        return self._request_json(
            "/health", timeout_seconds=self.config.connect_timeout_seconds
        )

    def api_root(self) -> SyncEndpointResult:
        return self._request_json(
            "/api/v1", timeout_seconds=self.config.read_timeout_seconds
        )

    def bootstrap_family(
        self, *, device_id: str, device_label: str
    ) -> FamilyLinkResult:
        response = self._request_json(
            "/api/v1/family/bootstrap",
            timeout_seconds=self.config.read_timeout_seconds,
            payload={"device_id": device_id, "device_label": device_label},
        )
        return family_link_from_response(response)

    def join_family(
        self, *, pairing_token: str, device_id: str, device_label: str
    ) -> FamilyLinkResult:
        response = self._request_json(
            "/api/v1/family/join",
            timeout_seconds=self.config.read_timeout_seconds,
            payload={
                "pairing_token": pairing_token,
                "device_id": device_id,
                "device_label": device_label,
            },
        )
        return family_link_from_response(response)

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
        return sync_batch_from_response(response)

    def sync_now(self) -> SyncStatus:
        health = self.healthcheck()
        if not health.ok:
            return _status_from_results(self.config, health, None)
        return _status_from_results(self.config, health, self.api_root())

    def _request_json(
        self,
        path: str,
        *,
        timeout_seconds: int,
        payload: dict[str, Any] | None = None,
    ) -> SyncEndpointResult:
        if not self.config.available:
            return SyncEndpointResult(
                False,
                "",
                None,
                None,
                None,
                "missing_config",
                "Sync server is not configured.",
            )
        endpoint = f"{self.config.server_base_url.rstrip('/')}{path}"
        return request_json(endpoint, float(timeout_seconds), payload)


def healthcheck(config: SyncConfig | None = None) -> SyncEndpointResult:
    return SyncClient(config or load_sync_config()).healthcheck()


def api_root(config: SyncConfig | None = None) -> SyncEndpointResult:
    return SyncClient(config or load_sync_config()).api_root()


def sync_now(config: SyncConfig | None = None) -> SyncStatus:
    return SyncClient(config or load_sync_config()).sync_now()


def bootstrap_family(
    *, device_id: str, device_label: str, config: SyncConfig | None = None
) -> FamilyLinkResult:
    return SyncClient(config or load_sync_config()).bootstrap_family(
        device_id=device_id, device_label=device_label
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
    api: SyncEndpointResult | None,
) -> SyncStatus:
    ok = health.ok and bool(api and api.ok)
    error = api if api is not None and not api.ok else health
    return SyncStatus(
        ok,
        config.available,
        config.server_base_url,
        config.server_label,
        config.profile,
        config.source,
        config.path,
        health,
        api,
        None if ok else error.error_code,
        None if ok else error.error_message,
    )


__all__ = (
    "FamilyLinkResult",
    "SyncBatchChange",
    "SyncBatchResult",
    "SyncClient",
    "SyncEndpointResult",
    "SyncStatus",
    "api_root",
    "bootstrap_family",
    "healthcheck",
    "join_family",
    "sync_batch",
    "sync_now",
)
