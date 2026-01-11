"""Tests for API client and hooks."""

from pathlib import Path


def test_api_client_exists():
    """Test that api/client.ts exists."""
    client = Path(__file__).parent / "src" / "api" / "client.ts"
    assert client.exists(), "src/api/client.ts does not exist"


def test_api_directory_exists():
    """Test that api directory exists."""
    api_dir = Path(__file__).parent / "src" / "api"
    assert api_dir.exists(), "src/api directory does not exist"
    assert api_dir.is_dir(), "api should be a directory"


def test_use_websocket_exists():
    """Test that useWebSocket hook exists."""
    hook = Path(__file__).parent / "src" / "hooks" / "useWebSocket.ts"
    assert hook.exists(), "src/hooks/useWebSocket.ts does not exist"


def test_hooks_directory_exists():
    """Test that hooks directory exists."""
    hooks_dir = Path(__file__).parent / "src" / "hooks"
    assert hooks_dir.exists(), "src/hooks directory does not exist"
    assert hooks_dir.is_dir(), "hooks should be a directory"


def test_api_client_has_class():
    """Test that api/client.ts defines API client class."""
    client = Path(__file__).parent / "src" / "api" / "client.ts"
    content = client.read_text()
    assert "class" in content.lower() or "export" in content, "Should define API client"
    assert "fetch" in content or "api" in content.lower(), "Should have API calls"


def test_use_websocket_is_hook():
    """Test that useWebSocket is a React hook."""
    hook = Path(__file__).parent / "src" / "hooks" / "useWebSocket.ts"
    content = hook.read_text()
    assert "useWebSocket" in content, "Should export useWebSocket"
    assert "useState" in content or "useRef" in content, "Hook should use React hooks"
