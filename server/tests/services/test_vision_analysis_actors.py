"""TDD tests for VisionAnalysisService Ray Actor lifecycle.

v0.13.0 (Phase C): Real-time Ray Actors for WebSocket streaming.

These tests verify the Actor Lifecycle Contract:
1. CREATE actor on first frame
2. REUSE actor on subsequent frames (caching)
3. KILL actor on client disconnect

Acceptance Criteria covered:
- AC 1: Strict TDD Compliance
- AC 2: Zero-Latency Frame Processing (Actor Reuse)
- AC 3: Bulletproof Garbage Collection (VRAM Release)
- AC 4: Graceful Local Fallback
- AC 5: Multi-Tool Streaming Support
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class MockRayActorHandle:
    """Mock Ray Actor handle for testing."""

    def __init__(self, plugin_id: str, tool_name: str):
        self.plugin_id = plugin_id
        self.tool_name = tool_name
        self.process_frame = MagicMock()
        self.process_frame.remote = MagicMock(return_value="mock_future")


class MockStreamingToolActor:
    """Mock StreamingToolActor class for testing."""

    _instances: list["MockStreamingToolActor"] = []
    _handle: MockRayActorHandle

    def __init__(self, plugin_id: str, tool_name: str):
        self.plugin_id = plugin_id
        self.tool_name = tool_name
        MockStreamingToolActor._instances.append(self)

    @classmethod
    def reset(cls):
        """Reset mock state between tests."""
        cls._instances = []

    @classmethod
    def remote(cls, plugin_id: str, tool_name: str):
        """Mock remote constructor."""
        instance = cls(plugin_id, tool_name)
        handle = MockRayActorHandle(plugin_id, tool_name)
        instance._handle = handle
        return handle


@pytest.fixture(autouse=True)
def reset_mock_actor():
    """Reset mock actor state between tests."""
    MockStreamingToolActor.reset()
    yield


@pytest.mark.asyncio
async def test_actor_lifecycle_caching_and_cleanup():
    """Test AC 1, AC 2, AC 3: Actor creation, caching, and cleanup.

    This test verifies:
    - First frame creates a new actor (AC 2)
    - Second frame reuses the same actor (AC 2)
    - cleanup_client kills the actor and removes from tracking (AC 3)
    """
    from app.services.vision_analysis import VisionAnalysisService

    # 1. Setup mocks
    plugin_service = MagicMock()
    ws_manager = AsyncMock()
    service = VisionAnalysisService(plugin_service, ws_manager)

    frame_data = {
        "data": "YmFzZTY0",  # valid base64
        "tools": ["test_tool"],
        "options": {},
    }

    # Mock Ray components
    with patch("ray.is_initialized", return_value=True):
        with patch("ray.get", return_value={"mock": "result"}):
            with patch("ray.kill") as mock_kill:
                with patch(
                    "app.workers.ray_actors.StreamingToolActor",
                    MockStreamingToolActor,
                ):
                    # 2. First Frame: Should CREATE the actor
                    await service.handle_frame("client-123", "test-plugin", frame_data)

                    assert "client-123" in service.active_actors
                    assert "test_tool" in service.active_actors["client-123"]

                    # 3. Second Frame: Should REUSE the actor (no new instantiation)
                    await service.handle_frame("client-123", "test-plugin", frame_data)

                    # Verify only one actor was created (caching works)
                    assert len(MockStreamingToolActor._instances) == 1

                    # 4. Cleanup: Should KILL the actor and remove from tracking dict
                    await service.cleanup_client("client-123")
                    mock_kill.assert_called_once()
                    assert "client-123" not in service.active_actors


@pytest.mark.asyncio
async def test_graceful_local_fallback_when_ray_not_initialized():
    """Test AC 4: Graceful Local Fallback.

    When Ray is not initialized, the service should fall back to
    synchronous local execution without attempting to spawn an actor.
    """
    from app.services.vision_analysis import VisionAnalysisService

    plugin_service = MagicMock()
    plugin_service.run_plugin_tool.return_value = {"local": "result"}
    ws_manager = AsyncMock()
    service = VisionAnalysisService(plugin_service, ws_manager)

    frame_data = {
        "data": "YmFzZTY0",  # valid base64
        "tools": ["test_tool"],
        "options": {},
    }

    # Process frame when Ray is not initialized
    with patch("ray.is_initialized", return_value=False):
        await service.handle_frame("client-123", "test-plugin", frame_data)

    # Should NOT have created any actors
    assert "client-123" not in service.active_actors

    # Should have called local plugin_service.run_plugin_tool instead
    plugin_service.run_plugin_tool.assert_called_once()


@pytest.mark.asyncio
async def test_multi_tool_streaming_support():
    """Test AC 5: Multi-Tool Streaming Support.

    When a user selects multiple tools simultaneously, the service
    should track and create separate Ray Actors under the same client_id.
    """
    from app.services.vision_analysis import VisionAnalysisService

    # Setup mocks
    plugin_service = MagicMock()
    ws_manager = AsyncMock()
    service = VisionAnalysisService(plugin_service, ws_manager)

    frame_data = {
        "data": "YmFzZTY0",  # valid base64
        "tools": ["player_detection", "ball_detection"],  # Two tools
        "options": {},
    }

    # Process frame with multiple tools
    with patch("ray.is_initialized", return_value=True):
        with patch("ray.get", return_value={"mock": "result"}):
            with patch("ray.kill") as mock_kill:
                with patch(
                    "app.workers.ray_actors.StreamingToolActor",
                    MockStreamingToolActor,
                ):
                    # Process frame with multiple tools
                    await service.handle_frame("client-123", "test-plugin", frame_data)

                    # Should have created two actors under the same client_id
                    assert "client-123" in service.active_actors
                    assert "player_detection" in service.active_actors["client-123"]
                    assert "ball_detection" in service.active_actors["client-123"]

                    # Two actors should have been created
                    assert len(MockStreamingToolActor._instances) == 2

                    # Cleanup should kill both actors
                    await service.cleanup_client("client-123")
                    assert mock_kill.call_count == 2  # Both actors killed
                    assert "client-123" not in service.active_actors


@pytest.mark.asyncio
async def test_actor_isolation_between_clients():
    """Test that actors are isolated between different clients.

    Each client should have its own set of actors, and cleanup
    of one client should not affect another.
    """
    from app.services.vision_analysis import VisionAnalysisService

    # Setup mocks
    plugin_service = MagicMock()
    ws_manager = AsyncMock()
    service = VisionAnalysisService(plugin_service, ws_manager)

    frame_data = {
        "data": "YmFzZTY0",
        "tools": ["test_tool"],
        "options": {},
    }

    # Process frames from two different clients
    with patch("ray.is_initialized", return_value=True):
        with patch("ray.get", return_value={"mock": "result"}):
            with patch("ray.kill") as mock_kill:
                with patch(
                    "app.workers.ray_actors.StreamingToolActor",
                    MockStreamingToolActor,
                ):
                    await service.handle_frame("client-1", "test-plugin", frame_data)
                    await service.handle_frame("client-2", "test-plugin", frame_data)

                    # Both clients should have their own actors
                    assert "client-1" in service.active_actors
                    assert "client-2" in service.active_actors

                    # Cleanup client-1 should not affect client-2
                    await service.cleanup_client("client-1")
                    assert mock_kill.call_count == 1
                    assert "client-1" not in service.active_actors
                    assert "client-2" in service.active_actors  # Still there!

                    # Cleanup client-2
                    await service.cleanup_client("client-2")
                    assert mock_kill.call_count == 2
                    assert "client-2" not in service.active_actors
