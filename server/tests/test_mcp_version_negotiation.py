"""Tests for MCP version negotiation."""

import os
import sys

# Add the server directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.mcp import MCP_PROTOCOL_VERSION, negotiate_mcp_version  # noqa: E402


class TestVersionNegotiation:
    """Test suite for MCP version negotiation."""

    def test_version_negotiation_without_client_version(self):
        """Test returning server version when no client version provided."""
        result = negotiate_mcp_version()

        assert result["server_version"] == MCP_PROTOCOL_VERSION
        assert result["compatible"] is True
        assert "supported_versions" in result
        assert MCP_PROTOCOL_VERSION in result["supported_versions"]

    def test_version_negotiation_with_compatible_version(self):
        """Test compatibility check with matching version."""
        result = negotiate_mcp_version(client_version="1.0.0")

        assert result["server_version"] == MCP_PROTOCOL_VERSION
        assert result["client_version"] == "1.0.0"
        assert result["compatible"] is True
        assert "compatible" in result["message"].lower()

    def test_version_negotiation_with_incompatible_version(self):
        """Test compatibility check with non-matching version."""
        result = negotiate_mcp_version(client_version="2.0.0")

        assert result["server_version"] == MCP_PROTOCOL_VERSION
        assert result["client_version"] == "2.0.0"
        assert result["compatible"] is False
        assert "not compatible" in result["message"].lower()
        assert "supports" in result["message"].lower()

    def test_version_negotiation_includes_supported_versions(self):
        """Test that incompatible response includes supported versions."""
        result = negotiate_mcp_version(client_version="3.0.0")

        assert "supported_versions" in result
        assert isinstance(result["supported_versions"], list)
        assert len(result["supported_versions"]) > 0

    def test_version_negotiation_message_format(self):
        """Test that version negotiation response has clear messages."""
        # Compatible
        compatible_result = negotiate_mcp_version(client_version="1.0.0")
        assert isinstance(compatible_result["message"], str)
        assert len(compatible_result["message"]) > 0

        # Incompatible
        incompatible_result = negotiate_mcp_version(client_version="99.0.0")
        assert isinstance(incompatible_result["message"], str)
        assert len(incompatible_result["message"]) > 0

    def test_version_negotiation_response_structure(self):
        """Test response structure for both compatible and incompatible cases."""
        # With no client version
        result_no_version = negotiate_mcp_version()
        assert "server_version" in result_no_version
        assert "supported_versions" in result_no_version
        assert "compatible" in result_no_version
        assert "message" in result_no_version

        # With compatible version
        result_compatible = negotiate_mcp_version(client_version="1.0.0")
        assert "server_version" in result_compatible
        assert "client_version" in result_compatible
        assert "compatible" in result_compatible
        assert "message" in result_compatible

        # With incompatible version
        result_incompatible = negotiate_mcp_version(client_version="2.0.0")
        assert "server_version" in result_incompatible
        assert "client_version" in result_incompatible
        assert "compatible" in result_incompatible
        assert "supported_versions" in result_incompatible
        assert "message" in result_incompatible

    def test_version_constant_value(self):
        """Test that MCP protocol version constant has expected format."""
        assert isinstance(MCP_PROTOCOL_VERSION, str)
        # Should follow semantic versioning
        parts = MCP_PROTOCOL_VERSION.split(".")
        assert len(parts) >= 2  # At least major.minor
