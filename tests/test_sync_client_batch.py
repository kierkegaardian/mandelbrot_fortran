from __future__ import annotations

import unittest

from app.sync_client import SyncClient

from tests.test_sync_client import _LocalSyncServer, SyncClientTests


class SyncClientBatchTests(unittest.TestCase):
    def test_sync_batch_posts_changes_and_parses_server_delta(self) -> None:
        with _LocalSyncServer(
            {
                "/api/v1/sync": (
                    200,
                    (
                        '{"server_cursor":7,"accepted_client_change_ids":[3],"changes":['
                        '{"server_change_id":7,"entity_type":"profiles","action":"upsert",'
                        '"entity_sync_id":"profile-sync-1","updated_at":"2026-04-11T10:00:00+00:00",'
                        '"data":{"name":"Sam","role":"child","created_at":"2026-04-11T09:00:00+00:00"}}]}'
                    ),
                    "application/json",
                    0.0,
                ),
            }
        ) as server:
            client = SyncClient(SyncClientTests()._config(server.base_url))
            result = client.sync_batch(
                family_id="home-lan",
                pairing_token="pair-123",
                device_id="device-1",
                since_cursor=0,
                changes=[
                    {
                        "client_change_id": 3,
                        "entity_type": "profiles",
                        "action": "upsert",
                        "entity_sync_id": "profile-sync-1",
                        "updated_at": "2026-04-11T10:00:00+00:00",
                        "data": {"name": "Sam", "role": "child"},
                    }
                ],
            )

        self.assertTrue(result.ok)
        self.assertEqual(result.server_cursor, 7)
        self.assertEqual(result.accepted_client_change_ids, [3])
        self.assertEqual(len(result.changes), 1)
        self.assertEqual(result.changes[0].entity_type, "profiles")
        self.assertEqual(server.requests, ["/api/v1/sync"])
        self.assertEqual(server.bodies[0]["pairing_token"], "pair-123")
        self.assertEqual(server.bodies[0]["changes"][0]["client_change_id"], 3)


if __name__ == "__main__":
    unittest.main()
