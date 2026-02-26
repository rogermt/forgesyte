"""Integration tests for WebSocket progress streaming.

Tests the complete flow: connect → receive progress → complete.
"""

import asyncio
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock

from app.main import app
from app.workers.progress import progress_callback
from app.websocket_manager import ws_manager


async def broadcast_progress(job_id: str, current_frame: int, total_frames: int, **kwargs):
    """Helper to broadcast progress asynchronously."""
    progress_callback(job_id, current_frame, total_frames, **kwargs)
    # Give time for the asyncio.create_task to complete
    await asyncio.sleep(0.05)


class TestProgressStreamingIntegration:
    """Integration tests for WebSocket progress streaming."""

    @pytest.fixture(autouse=True)
    def reset_ws_manager(self):
        """Reset WebSocket manager state before each test."""
        ws_manager.active_connections.clear()
        ws_manager.subscriptions.clear()
        yield
        ws_manager.active_connections.clear()
        ws_manager.subscriptions.clear()

    @pytest.mark.asyncio
    async def test_end_to_end_progress_streaming(self):
        """Test complete flow: connect → receive progress → complete."""
        client = TestClient(app)
        job_id = "integration-test-job"

        with client.websocket_connect(f"/ws/jobs/{job_id}") as ws:
            # 1. Connection established - verify with ping/pong
            ws.send_json({"type": "ping"})
            response = ws.receive_json()
            assert response["type"] == "pong"

            # 2. Simulate progress events from worker
            await broadcast_progress(job_id, 0, 100)
            response = ws.receive_json()
            assert response["percent"] == 0

            await broadcast_progress(job_id, 50, 100)
            response = ws.receive_json()
            assert response["percent"] == 50

            await broadcast_progress(job_id, 100, 100)
            response = ws.receive_json()
            assert response["percent"] == 100

    @pytest.mark.asyncio
    async def test_multiple_clients_same_job(self):
        """Test multiple clients can subscribe to same job."""
        client = TestClient(app)
        job_id = "multi-client-job"

        with client.websocket_connect(f"/ws/jobs/{job_id}") as ws1:
            with client.websocket_connect(f"/ws/jobs/{job_id}") as ws2:
                # Both should receive progress
                await broadcast_progress(job_id, 50, 100)

                response1 = ws1.receive_json()
                response2 = ws2.receive_json()

                assert response1["percent"] == 50
                assert response2["percent"] == 50

    @pytest.mark.asyncio
    async def test_client_isolation(self):
        """Test clients only receive their own job events."""
        client = TestClient(app)

        with client.websocket_connect("/ws/jobs/job-A") as wsA:
            with client.websocket_connect("/ws/jobs/job-B") as wsB:
                # Send progress for job-A
                await broadcast_progress("job-A", 50, 100)

                # Only wsA should receive
                responseA = wsA.receive_json()
                assert responseA["job_id"] == "job-A"

                # wsB should not receive job-A's progress
                # Send ping to verify wsB is still connected but has no pending messages
                wsB.send_json({"type": "ping"})
                responseB = wsB.receive_json()
                assert responseB["type"] == "pong"

    @pytest.mark.asyncio
    async def test_progress_event_with_tool_info(self):
        """Test progress event includes tool metadata."""
        client = TestClient(app)
        job_id = "tool-info-job"

        with client.websocket_connect(f"/ws/jobs/{job_id}") as ws:
            # Send progress with tool info
            await broadcast_progress(
                job_id,
                current_frame=50,
                total_frames=100,
                current_tool="yolo-tracker",
                tools_total=2,
                tools_completed=0,
            )

            response = ws.receive_json()
            assert response["job_id"] == job_id
            assert response["current_frame"] == 50
            assert response["total_frames"] == 100
            assert response["percent"] == 50
            assert response["current_tool"] == "yolo-tracker"
            assert response["tools_total"] == 2
            assert response["tools_completed"] == 0

    def test_websocket_disconnect_cleanup(self):
        """Test that disconnect properly cleans up subscriptions."""
        client = TestClient(app)
        job_id = "cleanup-test-job"

        with client.websocket_connect(f"/ws/jobs/{job_id}") as ws:
            # Verify connection
            ws.send_json({"type": "ping"})
            response = ws.receive_json()
            assert response["type"] == "pong"

        # After disconnect, should have no active connections
        # Allow some time for cleanup
        import time
        time.sleep(0.1)

        # Verify subscriptions are cleaned up
        assert f"job:{job_id}" not in ws_manager.subscriptions or \
               len(ws_manager.subscriptions.get(f"job:{job_id}", set())) == 0
