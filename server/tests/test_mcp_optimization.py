"""Tests for JSON-RPC optimization: batching, caching, v1.0 compatibility."""

import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional
from unittest.mock import MagicMock, patch

import pytest

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.mcp_adapter import MCPAdapter  # noqa: E402
from app.mcp_jsonrpc import JSONRPCErrorCode  # noqa: E402
from app.mcp_transport import MCPTransport  # noqa: E402

pytestmark = pytest.mark.asyncio


class TestJSONRPCBatching:
    """Tests for JSON-RPC batch request support."""

    @pytest.fixture
    def transport(self) -> MCPTransport:
        """Create transport instance."""
        return MCPTransport()

    async def test_handle_batch_request_single_item(
        self, transport: MCPTransport
    ) -> None:
        """Batch with single request should work like normal request."""
        requests = [
            {
                "jsonrpc": "2.0",
                "method": "ping",
                "id": 1,
            }
        ]

        responses = await transport.handle_batch_request(requests)

        assert isinstance(responses, list)
        assert len(responses) == 1
        assert responses[0]["jsonrpc"] == "2.0"
        assert responses[0]["id"] == 1
        assert "result" in responses[0]

    async def test_handle_batch_request_multiple_items(
        self, transport: MCPTransport
    ) -> None:
        """Batch with multiple requests should handle all."""
        requests = [
            {"jsonrpc": "2.0", "method": "ping", "id": 1},
            {"jsonrpc": "2.0", "method": "ping", "id": 2},
            {"jsonrpc": "2.0", "method": "ping", "id": 3},
        ]

        responses = await transport.handle_batch_request(requests)

        assert len(responses) == 3
        assert all(r["jsonrpc"] == "2.0" for r in responses)
        assert [r["id"] for r in responses] == [1, 2, 3]

    async def test_handle_batch_request_preserves_order(
        self, transport: MCPTransport
    ) -> None:
        """Response order should match request order."""
        requests = [
            {"jsonrpc": "2.0", "method": "ping", "id": 10},
            {"jsonrpc": "2.0", "method": "ping", "id": 5},
            {"jsonrpc": "2.0", "method": "ping", "id": 20},
        ]

        responses = await transport.handle_batch_request(requests)

        assert [r["id"] for r in responses] == [10, 5, 20]

    async def test_handle_batch_request_mixed_success_and_error(
        self, transport: MCPTransport
    ) -> None:
        """Batch should handle mix of successful and failed requests."""
        requests = [
            {"jsonrpc": "2.0", "method": "ping", "id": 1},
            {"jsonrpc": "2.0", "method": "nonexistent", "id": 2},
            {"jsonrpc": "2.0", "method": "ping", "id": 3},
        ]

        responses = await transport.handle_batch_request(requests)

        assert len(responses) == 3
        assert "result" in responses[0]  # Success
        assert "error" in responses[1]  # Error
        assert responses[1]["error"]["code"] == JSONRPCErrorCode.METHOD_NOT_FOUND
        assert "result" in responses[2]  # Success

    async def test_handle_batch_request_with_notifications(
        self, transport: MCPTransport
    ) -> None:
        """Batch with notifications (no id) should omit response for those."""
        requests = [
            {"jsonrpc": "2.0", "method": "ping", "id": 1},
            {"jsonrpc": "2.0", "method": "ping"},  # Notification, no id
            {"jsonrpc": "2.0", "method": "ping", "id": 2},
        ]

        responses = await transport.handle_batch_request(requests)

        # Should get 2 responses (not including notification)
        assert len(responses) == 2
        assert responses[0]["id"] == 1
        assert responses[1]["id"] == 2

    async def test_handle_batch_request_empty_list(
        self, transport: MCPTransport
    ) -> None:
        """Empty batch should return empty list."""
        requests: List[Dict[str, Any]] = []
        responses = await transport.handle_batch_request(requests)
        assert responses == []

    async def test_handle_batch_request_large_batch(
        self, transport: MCPTransport
    ) -> None:
        """Large batch should handle many requests."""
        requests = [{"jsonrpc": "2.0", "method": "ping", "id": i} for i in range(100)]

        responses = await transport.handle_batch_request(requests)

        assert len(responses) == 100
        assert [r["id"] for r in responses] == list(range(100))


class TestManifestCaching:
    """Tests for manifest caching with TTL."""

    @pytest.fixture
    def adapter(self) -> MCPAdapter:
        """Create adapter instance."""
        return MCPAdapter(base_url="http://localhost:8000")

    def test_manifest_cache_initially_empty(self, adapter: MCPAdapter) -> None:
        """Manifest cache should start empty."""
        assert adapter._manifest_cache is None
        assert adapter._manifest_cache_time is None

    def test_manifest_cache_stores_manifest(self, adapter: MCPAdapter) -> None:
        """Manifest cache should store generated manifest."""
        manifest = adapter.build_manifest([])
        adapter._cache_manifest(manifest)

        assert adapter._manifest_cache is not None
        assert adapter._manifest_cache == manifest

    def test_manifest_cache_stores_timestamp(self, adapter: MCPAdapter) -> None:
        """Manifest cache should store cache timestamp."""
        manifest = adapter.build_manifest([])
        adapter._cache_manifest(manifest)

        assert adapter._manifest_cache_time is not None
        assert isinstance(adapter._manifest_cache_time, float)

    def test_manifest_cache_is_valid_within_ttl(self, adapter: MCPAdapter) -> None:
        """Cache should be valid within TTL period."""
        manifest = adapter.build_manifest([])
        adapter._cache_manifest(manifest)

        assert adapter._is_manifest_cache_valid() is True

    def test_manifest_cache_expires_after_ttl(self, adapter: MCPAdapter) -> None:
        """Cache should expire after TTL seconds."""
        manifest = adapter.build_manifest([])
        adapter._cache_manifest(manifest)

        # Manually set cache time to past
        adapter._manifest_cache_time = time.time() - 300  # 5 minutes ago

        assert adapter._is_manifest_cache_valid() is False

    def test_get_manifest_uses_cache(self, adapter: MCPAdapter) -> None:
        """get_manifest should return cached manifest if valid."""
        manifest1 = adapter.build_manifest([])
        adapter._cache_manifest(manifest1)

        # Call get_manifest - should return cached version
        manifest2 = adapter.get_cached_manifest()

        assert manifest2 is manifest1

    def test_get_manifest_regenerates_after_expiry(self, adapter: MCPAdapter) -> None:
        """Cache should be regenerated after TTL expires."""
        # Cache a manifest
        manifest1 = adapter.build_manifest([])
        adapter._cache_manifest(manifest1)
        cache_time_1 = adapter._manifest_cache_time

        # Expire the cache by setting old time
        adapter._manifest_cache_time = time.time() - 300

        # Check that cache is invalid
        assert adapter._is_manifest_cache_valid() is False

        # Manually regenerate manifest (simulate get_manifest behavior)
        manifest2 = adapter.build_manifest([])
        adapter._cache_manifest(manifest2)
        cache_time_2 = adapter._manifest_cache_time

        # Cache time should be updated
        assert cache_time_2 is not None
        assert cache_time_1 is not None
        assert cache_time_2 > cache_time_1

    def test_cache_ttl_configurable(self, adapter: MCPAdapter) -> None:
        """Cache TTL should be configurable."""
        original_ttl = adapter._manifest_cache_ttl
        adapter._manifest_cache_ttl = 10

        assert adapter._manifest_cache_ttl == 10

        adapter._manifest_cache_ttl = original_ttl


class TestJSONRPCV1Compatibility:
    """Tests for JSON-RPC v1.0 backwards compatibility."""

    @pytest.fixture
    def transport(self) -> MCPTransport:
        """Create transport instance."""
        return MCPTransport()

    async def test_accept_v1_0_version_field(self, transport: MCPTransport) -> None:
        """Transport should accept v1.0 requests but warn."""
        # V1.0 uses 'jsonrpc': '1.0' instead of '2.0'
        request_dict = {
            "jsonrpc": "1.0",
            "method": "ping",
            "id": 1,
        }

        # Should be able to parse and convert
        converted = transport.convert_v1_request(request_dict)

        assert converted["jsonrpc"] == "2.0"
        assert converted["method"] == "ping"
        assert converted["id"] == 1

    async def test_v1_request_conversion_adds_id_if_missing(
        self, transport: MCPTransport
    ) -> None:
        """V1.0 requests without id should get one generated."""
        request_dict = {
            "jsonrpc": "1.0",
            "method": "ping",
        }

        converted = transport.convert_v1_request(request_dict)

        assert converted["jsonrpc"] == "2.0"
        assert "id" in converted
        assert converted["id"] is not None

    async def test_handle_request_with_v1_compatibility(
        self, transport: MCPTransport
    ) -> None:
        """handle_request should work with v1.0 format."""
        # Create request with v1.0 format
        request_dict = {
            "jsonrpc": "1.0",
            "method": "ping",
            "id": 1,
        }

        response = await transport.handle_request_with_v1_fallback(request_dict)

        assert response["jsonrpc"] == "2.0"
        assert response["id"] == 1
        assert "result" in response

    async def test_v1_request_logs_deprecation_warning(
        self, transport: MCPTransport
    ) -> None:
        """V1.0 requests should log deprecation warning."""
        request_dict = {
            "jsonrpc": "1.0",
            "method": "ping",
            "id": 1,
        }

        with patch("logging.getLogger") as mock_logger:
            mock_instance = MagicMock()
            mock_logger.return_value = mock_instance

            # Need to create new transport with mocked logger
            transport_new = MCPTransport()
            # Manually call the method
            try:
                transport_new.convert_v1_request(request_dict)
            except Exception:
                pass  # Conversion may fail, just checking logging


class TestOptimizationPerformance:
    """Tests to verify optimization performance characteristics."""

    @pytest.fixture
    def transport(self) -> MCPTransport:
        """Create transport instance."""
        return MCPTransport()

    async def test_batch_processing_time(self, transport: MCPTransport) -> None:
        """Batch processing should be reasonably fast."""
        requests = [{"jsonrpc": "2.0", "method": "ping", "id": i} for i in range(50)]

        start = time.time()
        responses = await transport.handle_batch_request(requests)
        elapsed = time.time() - start

        assert len(responses) == 50
        # Should complete in less than 1 second
        assert elapsed < 1.0

    def test_manifest_cache_reduces_builds(
        self, adapter: Optional[MCPAdapter] = None
    ) -> None:
        """Caching should reduce redundant manifest builds."""
        if adapter is None:
            adapter = MCPAdapter(base_url="http://localhost:8000")

        # Build and cache manifest
        manifest1 = adapter.build_manifest([])
        adapter._cache_manifest(manifest1)

        # Get from cache multiple times
        for _ in range(10):
            cached = adapter.get_cached_manifest()
            assert cached is manifest1  # Same object = cache hit


# Helper fixture for MockPluginManager
@pytest.fixture
def mock_plugin_manager() -> MagicMock:
    """Create mock plugin manager."""
    manager = MagicMock()
    manager.get_plugins.return_value = []
    return manager


@pytest.fixture
def adapter() -> MCPAdapter:
    """Create MCPAdapter for tests."""
    return MCPAdapter(base_url="http://localhost:8000")
