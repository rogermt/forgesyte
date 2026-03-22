"""Tests for debug endpoint /v1/debug/db_pool.

Issue #357: DB timeout causing knock-on problems.
"""

import pytest


@pytest.mark.unit
@pytest.mark.asyncio
class TestDebugPoolEndpoint:
    """Tests for debug endpoint."""

    async def test_debug_db_pool_returns_200(self, client) -> None:
        """Debug endpoint should return 200 OK."""
        response = await client.get("/v1/debug/db_pool")
        assert response.status_code == 200

    async def test_debug_db_pool_returns_pool_status(self, client) -> None:
        """Debug endpoint should return pool status."""
        response = await client.get("/v1/debug/db_pool")
        data = response.json()

        assert "pool" in data
        assert "active_sessions" in data

    async def test_debug_db_pool_returns_active_sessions(self, client) -> None:
        """Debug endpoint should return active sessions list."""
        response = await client.get("/v1/debug/db_pool")
        data = response.json()

        assert isinstance(data["active_sessions"], list)
