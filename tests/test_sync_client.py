from __future__ import annotations

import json
import threading
import time
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

from app.sync_client import SyncClient, api_root, healthcheck, sync_now
from app.sync_config import SyncConfig


ResponseSpec = tuple[int, str, str, float]


class _SyncRequestHandler(BaseHTTPRequestHandler):
    routes: dict[str, ResponseSpec] = {}
    requests: list[str] = []
    bodies: list[dict[str, Any]] = []

    def do_GET(self) -> None:  # noqa: N802 - stdlib handler name
        type(self).requests.append(self.path)
        status, body, content_type, delay = type(self).routes.get(
            self.path,
            (404, '{"error":"not_found"}', "application/json", 0.0),
        )
        if delay:
            time.sleep(delay)
        body_bytes = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body_bytes)))
        self.end_headers()
        try:
            self.wfile.write(body_bytes)
        except (BrokenPipeError, ConnectionResetError):
            pass

    def do_POST(self) -> None:  # noqa: N802 - stdlib handler name
        type(self).requests.append(self.path)
        raw_length = self.headers.get("Content-Length", "0")
        try:
            length = max(0, int(raw_length))
        except ValueError:
            length = 0
        raw_body = self.rfile.read(length) if length else b""
        try:
            body_json = json.loads(raw_body.decode("utf-8")) if raw_body else {}
        except json.JSONDecodeError:
            body_json = {"_invalid": True}
        type(self).bodies.append(body_json)
        status, body, content_type, delay = type(self).routes.get(
            self.path,
            (404, '{"error":"not_found"}', "application/json", 0.0),
        )
        if delay:
            time.sleep(delay)
        body_bytes = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body_bytes)))
        self.end_headers()
        try:
            self.wfile.write(body_bytes)
        except (BrokenPipeError, ConnectionResetError):
            pass

    def log_message(self, format: str, *args: Any) -> None:  # noqa: A003
        return


class _LocalSyncServer:
    def __init__(self, routes: dict[str, ResponseSpec]) -> None:
        self.routes = routes
        self.server: ThreadingHTTPServer | None = None
        self.thread: threading.Thread | None = None
        self.handler: type[_SyncRequestHandler] | None = None

    def __enter__(self) -> "_LocalSyncServer":
        handler = type(
            "LocalSyncRequestHandler",
            (_SyncRequestHandler,),
            {
                "routes": self.routes,
                "requests": [],
                "bodies": [],
            },
        )
        self.handler = handler
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        if self.server is not None:
            self.server.shutdown()
            self.server.server_close()
        if self.thread is not None:
            self.thread.join(timeout=2)

    @property
    def base_url(self) -> str:
        assert self.server is not None
        host, port = self.server.server_address
        return f"http://{host}:{port}"

    @property
    def requests(self) -> list[str]:
        assert self.handler is not None
        return self.handler.requests

    @property
    def bodies(self) -> list[dict[str, Any]]:
        assert self.handler is not None
        return self.handler.bodies


class SyncClientTests(unittest.TestCase):
    def _config(self, base_url: str, connect_timeout: int = 1, read_timeout: int = 1) -> SyncConfig:
        return SyncConfig(
            profile="home-lan",
            server_base_url=base_url,
            server_label="Home sync server",
            connect_timeout_seconds=connect_timeout,
            read_timeout_seconds=read_timeout,
            source="override",
            path="/tmp/sync.json",
        )

    def test_healthcheck_and_api_root_use_local_server(self) -> None:
        with _LocalSyncServer(
            {
                "/health": (200, '{"status":"ok"}', "application/json", 0.0),
                "/api/v1": (200, '{"api":"root"}', "application/json", 0.0),
            }
        ) as server:
            client = SyncClient(self._config(server.base_url))

            health = client.healthcheck()
            api = client.api_root()

        self.assertTrue(health.ok)
        self.assertEqual(health.status_code, 200)
        self.assertEqual(health.data, {"status": "ok"})
        self.assertTrue(api.ok)
        self.assertEqual(api.status_code, 200)
        self.assertEqual(api.data, {"api": "root"})
        self.assertEqual(server.requests, ["/health", "/api/v1"])

    def test_sync_now_returns_structured_status_without_mutation(self) -> None:
        with _LocalSyncServer(
            {
                "/health": (200, '{"status":"ok"}', "application/json", 0.0),
                "/api/v1": (200, '{"capabilities":["discover"]}', "application/json", 0.0),
            }
        ) as server:
            client = SyncClient(self._config(server.base_url))

            status = client.sync_now()

        self.assertTrue(status.ok)
        self.assertTrue(status.config_available)
        self.assertTrue(status.health.ok)
        self.assertTrue(status.api_root is not None and status.api_root.ok)
        self.assertIsNone(status.error_code)
        self.assertEqual(server.requests, ["/health", "/api/v1"])

    def test_missing_config_returns_missing_config_result(self) -> None:
        client = SyncClient(self._config(""))

        health = client.healthcheck()
        api = client.api_root()
        status = client.sync_now()

        self.assertFalse(health.ok)
        self.assertEqual(health.error_code, "missing_config")
        self.assertFalse(api.ok)
        self.assertEqual(api.error_code, "missing_config")
        self.assertFalse(status.ok)
        self.assertFalse(status.config_available)
        self.assertEqual(status.error_code, "missing_config")

    def test_http_error_is_reported_cleanly(self) -> None:
        with _LocalSyncServer(
            {
                "/health": (503, '{"error":"busy"}', "application/json", 0.0),
            }
        ) as server:
            client = SyncClient(self._config(server.base_url))

            result = client.healthcheck()

        self.assertFalse(result.ok)
        self.assertEqual(result.status_code, 503)
        self.assertEqual(result.error_code, "http_503")
        self.assertIn("Service Unavailable", result.error_message or "")
        self.assertEqual(result.data, {"error": "busy"})

    def test_invalid_json_is_reported_cleanly(self) -> None:
        with _LocalSyncServer(
            {
                "/api/v1": (200, "not-json", "text/plain", 0.0),
            }
        ) as server:
            client = SyncClient(self._config(server.base_url))

            result = client.api_root()

        self.assertFalse(result.ok)
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.error_code, "invalid_json")
        self.assertEqual(result.raw_text, "not-json")
        self.assertIsNone(result.data)

    def test_timeout_is_reported_cleanly(self) -> None:
        with _LocalSyncServer(
            {
                "/health": (200, '{"status":"slow"}', "application/json", 1.5),
            }
        ) as server:
            client = SyncClient(self._config(server.base_url, connect_timeout=1, read_timeout=1))

            result = client.healthcheck()

        self.assertFalse(result.ok)
        self.assertEqual(result.error_code, "timeout")
        self.assertIsNone(result.status_code)

    def test_sync_now_short_circuits_when_health_fails(self) -> None:
        with _LocalSyncServer(
            {
                "/health": (500, '{"error":"down"}', "application/json", 0.0),
                "/api/v1": (200, '{"api":"root"}', "application/json", 0.0),
            }
        ) as server:
            client = SyncClient(self._config(server.base_url))

            status = client.sync_now()

        self.assertFalse(status.ok)
        self.assertEqual(status.health.status_code, 500)
        self.assertIsNone(status.api_root)
        self.assertEqual(server.requests, ["/health"])

    def test_bootstrap_family_posts_device_payload(self) -> None:
        with _LocalSyncServer(
            {
                "/api/v1/family/bootstrap": (
                    200,
                    '{"family_id":"home-lan","pairing_token":"pair-123"}',
                    "application/json",
                    0.0,
                ),
            }
        ) as server:
            client = SyncClient(self._config(server.base_url))
            result = client.bootstrap_family(device_id="device-1", device_label="Kid laptop")

        self.assertTrue(result.ok)
        self.assertEqual(result.family_id, "home-lan")
        self.assertEqual(result.pairing_token, "pair-123")
        self.assertEqual(server.requests, ["/api/v1/family/bootstrap"])
        self.assertEqual(server.bodies[0]["device_id"], "device-1")
        self.assertEqual(server.bodies[0]["device_label"], "Kid laptop")

if __name__ == "__main__":
    unittest.main()
