"""
Test suite for WU-12: Update useWebSocket hook.

Ensures hooks/useWebSocket.ts:
- Properly exports all interfaces and hook function
- Has correct TypeScript typing for WebSocket messages and results
- Implements reconnection logic with configurable parameters
- Supports plugin switching and frame sending
- Has proper error handling and connection state management
"""

from pathlib import Path

# Get web-ui directory
WEB_UI_DIR = Path(__file__).parent


def test_websocket_hook_exists():
    """Verify useWebSocket.ts exists and is readable."""
    hook_path = WEB_UI_DIR / "src" / "hooks" / "useWebSocket.ts"
    assert hook_path.exists(), "useWebSocket.ts not found"
    with open(hook_path, "r") as f:
        content = f.read()
    assert len(content) > 0, "useWebSocket.ts is empty"


def test_websocket_exports_interfaces():
    """Verify all WebSocket-related interfaces are exported."""
    hook_path = WEB_UI_DIR / "src" / "hooks" / "useWebSocket.ts"
    with open(hook_path, "r") as f:
        content = f.read()

    required_interfaces = [
        "WebSocketMessage",
        "FrameResult",
        "UseWebSocketOptions",
        "UseWebSocketReturn",
    ]
    for interface in required_interfaces:
        assert (
            f"export interface {interface}" in content
        ), f"Missing interface {interface}"


def test_websocket_message_type_discriminated():
    """Verify WebSocketMessage has type discriminating field."""
    hook_path = WEB_UI_DIR / "src" / "hooks" / "useWebSocket.ts"
    with open(hook_path, "r") as f:
        content = f.read()

    # Should have message types for different cases
    message_types = [
        "connected",
        "result",
        "error",
        "plugin_switched",
        "pong",
    ]
    for msg_type in message_types:
        assert msg_type in content, f"Missing message type {msg_type}"


def test_hook_function_exported():
    """Verify useWebSocket hook function is exported."""
    hook_path = WEB_UI_DIR / "src" / "hooks" / "useWebSocket.ts"
    with open(hook_path, "r") as f:
        content = f.read()
    assert (
        "export function useWebSocket" in content
    ), "useWebSocket hook function not exported"


def test_hook_accepts_options_parameter():
    """Verify hook accepts UseWebSocketOptions parameter."""
    hook_path = WEB_UI_DIR / "src" / "hooks" / "useWebSocket.ts"
    with open(hook_path, "r") as f:
        content = f.read()
    assert "UseWebSocketOptions" in content, "Hook should use UseWebSocketOptions"


def test_hook_returns_correct_type():
    """Verify hook returns UseWebSocketReturn."""
    hook_path = WEB_UI_DIR / "src" / "hooks" / "useWebSocket.ts"
    with open(hook_path, "r") as f:
        content = f.read()
    assert "UseWebSocketReturn" in content, "Hook should return UseWebSocketReturn"


def test_hook_uses_react_hooks():
    """Verify hook uses React hooks (useState, useEffect, useCallback, useRef)."""
    hook_path = WEB_UI_DIR / "src" / "hooks" / "useWebSocket.ts"
    with open(hook_path, "r") as f:
        content = f.read()

    required_hooks = ["useState", "useEffect", "useCallback", "useRef"]
    for hook in required_hooks:
        assert hook in content, f"Hook should use {hook}"


def test_hook_has_connection_state():
    """Verify hook manages connection state."""
    hook_path = WEB_UI_DIR / "src" / "hooks" / "useWebSocket.ts"
    with open(hook_path, "r") as f:
        content = f.read()

    # Should track isConnected, isConnecting, error
    assert "isConnected" in content, "Missing isConnected state"
    assert "isConnecting" in content, "Missing isConnecting state"
    assert "error" in content, "Missing error state"


def test_hook_has_frame_sending():
    """Verify hook provides sendFrame method."""
    hook_path = WEB_UI_DIR / "src" / "hooks" / "useWebSocket.ts"
    with open(hook_path, "r") as f:
        content = f.read()
    assert "sendFrame" in content, "Missing sendFrame method"
    assert "imageData" in content, "sendFrame should accept imageData"


def test_hook_has_plugin_switching():
    """Verify hook provides switchPlugin method."""
    hook_path = WEB_UI_DIR / "src" / "hooks" / "useWebSocket.ts"
    with open(hook_path, "r") as f:
        content = f.read()
    assert "switchPlugin" in content, "Missing switchPlugin method"


def test_hook_has_reconnection_logic():
    """Verify hook implements reconnection logic."""
    hook_path = WEB_UI_DIR / "src" / "hooks" / "useWebSocket.ts"
    with open(hook_path, "r") as f:
        content = f.read()

    # Should have reconnect attempts and interval
    assert "reconnect" in content, "Missing reconnect method"
    assert (
        "Attempt" in content or "attempt" in content
    ), "Should log reconnection attempts"


def test_hook_has_statistics_tracking():
    """Verify hook tracks frame processing statistics."""
    hook_path = WEB_UI_DIR / "src" / "hooks" / "useWebSocket.ts"
    with open(hook_path, "r") as f:
        content = f.read()

    # Should track processing times and frame count
    assert "framesProcessed" in content, "Missing frame counter"
    assert "processing_time" in content.lower(), "Should track processing times"


def test_hook_handles_websocket_errors():
    """Verify hook handles WebSocket error events."""
    hook_path = WEB_UI_DIR / "src" / "hooks" / "useWebSocket.ts"
    with open(hook_path, "r") as f:
        content = f.read()

    # Should have error handler
    assert (
        "ws.onerror" in content or "onError" in content
    ), "Should handle WebSocket errors"


def test_hook_manages_cleanup():
    """Verify hook cleans up resources in useEffect cleanup."""
    hook_path = WEB_UI_DIR / "src" / "hooks" / "useWebSocket.ts"
    with open(hook_path, "r") as f:
        content = f.read()

    # Should return cleanup function from useEffect
    assert (
        "return ()" in content or "disconnect" in content
    ), "Should cleanup resources on unmount"
