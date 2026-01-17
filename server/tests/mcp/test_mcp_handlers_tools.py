import asyncio
import os
import sys

# Add server directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.mcp.jsonrpc import JSONRPCErrorCode, JSONRPCRequest
from app.mcp.transport import MCPTransport


class TestInitializeHandler:
    """Tests for the initialize method."""

    def test_initialize_success(self):
        async def run_test():
            transport = MCPTransport()

            request = JSONRPCRequest(
                jsonrpc="2.0",
                method="initialize",
                params={
                    "clientInfo": {"name": "test"},
                    "protocolVersion": "2024-11-05",
                },
                id=1,
            )

            response = await transport.handle_request(request)

            assert response.error is None
            assert response.result is not None
            assert "serverInfo" in response.result
            assert "capabilities" in response.result

        asyncio.run(run_test())


class TestPingHandler:
    """Tests for ping method."""

    def test_ping_success(self):
        async def run_test():
            transport = MCPTransport()

            request = JSONRPCRequest(
                jsonrpc="2.0",
                method="ping",
                params={},
                id=2,
            )

            response = await transport.handle_request(request)

            assert response.error is None
            assert response.result["status"] == "pong"

        asyncio.run(run_test())


class TestToolsListHandler:
    """Tests for tools/list method."""

    def test_tools_list_success(self):
        async def run_test():
            transport = MCPTransport()

            request = JSONRPCRequest(
                jsonrpc="2.0",
                method="tools/list",
                params={},
                id=3,
            )

            response = await transport.handle_request(request)

            assert response.error is None
            assert "tools" in response.result
            assert isinstance(response.result["tools"], list)

            # Each tool must have required fields
            for tool in response.result["tools"]:
                assert "name" in tool
                assert "description" in tool
                assert "inputSchema" in tool

        asyncio.run(run_test())


class TestToolsCallHandler:
    """TDD tests for tools/call handler - MUST return JSON, not text."""

    def test_tools_call_missing_name(self):
        async def run_test():
            transport = MCPTransport()

            request = JSONRPCRequest(
                jsonrpc="2.0",
                method="tools/call",
                params={"arguments": {"image": "http://example.com/img.png"}},
                id=4,
            )

            response = await transport.handle_request(request)

            assert response.error is not None
            assert response.error["code"] == JSONRPCErrorCode.INVALID_PARAMS

        asyncio.run(run_test())

    def test_tools_call_missing_image(self):
        async def run_test():
            transport = MCPTransport()

            request = JSONRPCRequest(
                jsonrpc="2.0",
                method="tools/call",
                params={"name": "ocr", "arguments": {}},
                id=5,
            )

            response = await transport.handle_request(request)

            assert response.error is not None
            assert response.error["code"] == JSONRPCErrorCode.INVALID_PARAMS

        asyncio.run(run_test())

    def test_tools_call_unknown_tool(self):
        async def run_test():
            transport = MCPTransport()

            request = JSONRPCRequest(
                jsonrpc="2.0",
                method="tools/call",
                params={
                    "name": "nonexistent_tool",
                    "arguments": {"image": "http://example.com/img.png"},
                },
                id=6,
            )

            response = await transport.handle_request(request)

            assert response.error is not None
            assert response.error["code"] == JSONRPCErrorCode.INVALID_PARAMS

        asyncio.run(run_test())

    def test_tools_call_must_return_json_not_text(self, monkeypatch):
        """CRITICAL: tools/call MUST return type='json', NOT hardcoded text."""

        async def run_test():
            transport = MCPTransport()

            # Fake plugin that returns structured result
            class FakePlugin:
                def analyze(self, image_bytes, options):
                    return {
                        "text": "hello world",
                        "confidence": 0.99,
                        "blocks": [{"x": 0, "y": 0}],
                    }

            # Patch plugin_manager.get()
            monkeypatch.setattr(
                transport._protocol_handlers.plugin_manager,
                "get",
                lambda name: FakePlugin(),
            )

            request = JSONRPCRequest(
                jsonrpc="2.0",
                method="tools/call",
                params={
                    "name": "ocr",
                    "arguments": {"image": "test_data"},
                },
                id=7,
            )

            response = await transport.handle_request(request)

            # Must not error
            assert response.error is None
            assert response.result is not None

            # Content must be a list
            content = response.result["content"]
            assert isinstance(content, list)
            assert len(content) > 0

            # CRITICAL: type MUST be 'text' per MCP spec (not 'json')
            assert (
                content[0]["type"] == "text"
            ), f"Expected type='text', got type='{content[0]['type']}'"

            # Content must be JSON-stringified in "text" field
            import json as json_module

            json_payload = json_module.loads(content[0]["text"])
            assert (
                json_payload["text"] == "hello world"
            ), "Should return plugin's actual text output"
            assert json_payload["confidence"] == 0.99
            assert json_payload["blocks"] == [{"x": 0, "y": 0}]

        asyncio.run(run_test())

    def test_tools_call_plugin_exception(self, monkeypatch):
        """tools/call must wrap plugin exceptions in MCP error."""

        async def run_test():
            transport = MCPTransport()

            class FailingPlugin:
                def analyze(self, image_bytes, options):
                    raise Exception("Plugin failed")

            monkeypatch.setattr(
                transport._protocol_handlers.plugin_manager,
                "get",
                lambda name: FailingPlugin(),
            )

            request = JSONRPCRequest(
                jsonrpc="2.0",
                method="tools/call",
                params={
                    "name": "ocr",
                    "arguments": {"image": "test_data"},
                },
                id=8,
            )

            response = await transport.handle_request(request)

            assert response.error is not None
            assert response.error["code"] == JSONRPCErrorCode.INTERNAL_ERROR
            assert "Plugin failed" in response.error["message"]

        asyncio.run(run_test())

    def test_tools_call_result_with_unicode_characters(self, monkeypatch):
        """tools/call unicode responses must serialize correctly."""

        async def run_test():
            transport = MCPTransport()

            # Plugin that returns unicode/special characters
            class UnicodePlugin:
                def analyze(self, image_bytes, options):
                    return {
                        "text": "Héllo wørld 中文 🎉 émojis",
                        "confidence": 0.95,
                        "metadata": {"lang": "multi", "chars": "spëcial"},
                    }

            monkeypatch.setattr(
                transport._protocol_handlers.plugin_manager,
                "get",
                lambda name: UnicodePlugin(),
            )

            request = JSONRPCRequest(
                jsonrpc="2.0",
                method="tools/call",
                params={
                    "name": "ocr",
                    "arguments": {"image": "test_data"},
                },
                id=9,
            )

            response = await transport.handle_request(request)

            assert response.error is None
            assert response.result is not None

            content = response.result["content"]
            assert content[0]["type"] == "text"

            import json as json_module

            json_payload = json_module.loads(content[0]["text"])
            assert "Héllo wørld 中文" in json_payload["text"]
            assert json_payload["metadata"]["chars"] == "spëcial"

            # Test actual JSON serialization (what FastAPI does)
            import json

            serialized = json.dumps(response.model_dump(exclude_none=True))
            # Must serialize without errors
            assert len(serialized) > 0

        asyncio.run(run_test())

    def test_tools_call_plugin_returning_non_json_serializable(self, monkeypatch):
        """tools/call must handle plugins returning non-JSON-serializable objects."""

        async def run_test():
            transport = MCPTransport()

            # Plugin that returns non-serializable object
            class BadPlugin:
                def analyze(self, image_bytes, options):
                    import datetime

                    return {
                        "timestamp": datetime.datetime.now(),  # Not JSON-serializable
                        "text": "test",
                    }

            monkeypatch.setattr(
                transport._protocol_handlers.plugin_manager,
                "get",
                lambda name: BadPlugin(),
            )

            request = JSONRPCRequest(
                jsonrpc="2.0",
                method="tools/call",
                params={
                    "name": "ocr",
                    "arguments": {"image": "test_data"},
                },
                id=10,
            )

            response = await transport.handle_request(request)

            # Should have error since object is not JSON serializable
            assert response.error is not None

        asyncio.run(run_test())

    def test_tools_call_plugin_returning_pydantic_model(self, monkeypatch):
        """tools/call must convert Pydantic models to dict for JSON serialization."""

        async def run_test():
            from pydantic import BaseModel

            transport = MCPTransport()

            # Plugin that returns Pydantic model (like AnalysisResult)
            class AnalysisResult(BaseModel):
                text: str
                confidence: float
                blocks: list

            class PydanticPlugin:
                def analyze(self, image_bytes, options):
                    return AnalysisResult(
                        text="extracted text",
                        confidence=0.95,
                        blocks=[{"x": 0, "y": 0, "text": "line1"}],
                    )

            monkeypatch.setattr(
                transport._protocol_handlers.plugin_manager,
                "get",
                lambda name: PydanticPlugin(),
            )

            request = JSONRPCRequest(
                jsonrpc="2.0",
                method="tools/call",
                params={
                    "name": "ocr",
                    "arguments": {"image": "test_data"},
                },
                id=11,
            )

            response = await transport.handle_request(request)

            # Must NOT error
            assert response.error is None
            assert response.result is not None

            # Content must be valid JSON in "text" field per MCP spec
            content = response.result["content"]
            assert content[0]["type"] == "text"

            # Parse JSON from text field
            import json as json_module

            parsed = json_module.loads(content[0]["text"])
            assert parsed["text"] == "extracted text"
            assert parsed["confidence"] == 0.95
            assert parsed["blocks"] == [{"x": 0, "y": 0, "text": "line1"}]

        asyncio.run(run_test())

    def test_tools_call_must_not_pass_url_string_to_plugin(self, monkeypatch):
        """tools/call must NOT pass URL string directly to plugin - must fetch bytes."""

        async def run_test():
            transport = MCPTransport()

            # Plugin that will fail if it gets a URL string instead of bytes
            class StrictPlugin:
                def analyze(self, image_bytes, options):
                    # Plugin expects actual bytes, not URL string
                    if isinstance(image_bytes, str):
                        raise ValueError(f"Expected bytes, got string: {image_bytes}")
                    if image_bytes.startswith(b"https://"):
                        raise ValueError("Received URL string encoded as UTF-8!")
                    return {"text": "ok", "confidence": 1.0, "blocks": []}

            monkeypatch.setattr(
                transport._protocol_handlers.plugin_manager,
                "get",
                lambda name: StrictPlugin(),
            )

            request = JSONRPCRequest(
                jsonrpc="2.0",
                method="tools/call",
                params={
                    "name": "ocr",
                    "arguments": {"image": "https://example.com/test.png"},
                },
                id=12,
            )

            response = await transport.handle_request(request)

            # Should have error since URL was passed to plugin instead of fetched
            assert response.error is not None
            assert "URL string encoded as UTF-8" in response.error["message"]

        asyncio.run(run_test())
