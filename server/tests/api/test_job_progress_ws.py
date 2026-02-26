"""Tests for /ws/jobs/{job_id} WebSocket endpoint (TDD - Phase 5).

Tests for real-time job progress streaming via WebSocket.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock


@pytest.fixture(autouse=True)
def reset_ws_manager():
    """Reset ws_manager state before each test."""
    from app.websocket_manager import ws_manager
    
    # Clear all connections and subscriptions
    ws_manager.active_connections.clear()
    ws_manager.subscriptions.clear()
    
    yield
    
    # Cleanup after test
    ws_manager.active_connections.clear()
    ws_manager.subscriptions.clear()


class TestJobProgressWebSocket:
    """Tests for /ws/jobs/{job_id} WebSocket endpoint."""

    def test_websocket_connect(self) -> None:
        """Test WebSocket connection is accepted."""
        from fastapi.testclient import TestClient
        from app.main import app

        client = TestClient(app)
        with client.websocket_connect("/ws/jobs/test-job-123") as websocket:
            # Connection should be accepted
            assert websocket is not None

    def test_websocket_ping_pong(self) -> None:
        """Test ping/pong message handling."""
        from fastapi.testclient import TestClient
        from app.main import app

        client = TestClient(app)
        with client.websocket_connect("/ws/jobs/test-job-123") as websocket:
            websocket.send_json({"type": "ping"})
            response = websocket.receive_json()
            assert response["type"] == "pong"

    @pytest.mark.asyncio
    async def test_websocket_receives_progress_event(self) -> None:
        """Test receiving progress event on subscribed job."""
        from fastapi.testclient import TestClient
        from app.main import app
        from app.workers.progress import progress_callback

        client = TestClient(app)
        
        with client.websocket_connect("/ws/jobs/test-job-456") as websocket:
            # Give connection time to subscribe
            await asyncio.sleep(0.1)
            
            # Trigger progress callback
            progress_callback("test-job-456", 50, 100)
            
            # Give time for async broadcast
            await asyncio.sleep(0.1)
            
            # Should receive the progress event
            response = websocket.receive_json()
            assert response["job_id"] == "test-job-456"
            assert response["current_frame"] == 50
            assert response["total_frames"] == 100
            assert response["percent"] == 50

    @pytest.mark.asyncio
    async def test_websocket_ignores_other_jobs(self) -> None:
        """Test that events for other jobs are not received."""
        from fastapi.testclient import TestClient
        from app.main import app
        from app.workers.progress import progress_callback

        client = TestClient(app)
        
        with client.websocket_connect("/ws/jobs/job-A") as websocket:
            # Give connection time to subscribe
            await asyncio.sleep(0.1)
            
            # Send progress for different job
            progress_callback("job-B", 50, 100)
            
            # Give time for async broadcast
            await asyncio.sleep(0.2)
            
            # Send ping to check connection is alive
            websocket.send_json({"type": "ping"})
            response = websocket.receive_json()
            # The response should be pong, not a progress event from job-B
            # because client is subscribed to job-A, not job-B
            assert response.get("type") == "pong" or response.get("job_id") == "job-A"
