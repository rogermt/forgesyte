"""Tests for MCP protocol handlers - tools methods."""

import asyncio
import base64
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.mcp.jsonrpc import JSONRPCErrorCode, JSONRPCRequest
from app.mcp.transport import MCPTransport

# Valid 1x1 PNG for testing
PNG_1X1 = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8DwHwAFBQIAX8jx0gAAAABJRU5ErkJggg=="
)


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

            for tool in response.result["tools"]:
                assert "name" in tool
                assert "description" in tool
                assert "inputSchema" in tool

        asyncio.run(run_test())


class TestToolsCallHandler:
    """Tests for tools/call handler."""

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
        """tools/call MUST return type='text' with JSON-stringified result."""

        async def run_test():
            transport = MCPTransport()

            class FakePlugin:
                name = "test_plugin"
                tools = {
                    "ocr": {
                        "handler": "analyze_image",
                        "description": "OCR analysis",
                        "input_schema": {"type": "object"},
                        "output_schema": {"type": "object"},
                    }
                }

                def analyze_image(self, image_bytes, options):
                    return {
                        "text": "hello world",
                        "confidence": 0.99,
                        "blocks": [{"x": 0, "y": 0}],
                    }

                def run_tool(self, tool_name, args):
                    if tool_name == "ocr":
                        return self.analyze_image(
                            args["image_bytes"], args.get("options", {})
                        )
                    raise ValueError(f"Unknown tool: {tool_name}")

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
                    "arguments": {"image": "dGVzdF9kYXRh"},  # base64 of "test_data"
                },
                id=7,
            )

            response = await transport.handle_request(request)

            assert response.error is None
            assert response.result is not None

            content = response.result["content"]
            assert isinstance(content, list)
            assert len(content) > 0
            assert content[0]["type"] == "text"

            import json

            json_payload = json.loads(content[0]["text"])
            assert json_payload["text"] == "hello world"
            assert json_payload["confidence"] == 0.99
            assert json_payload["blocks"] == [{"x": 0, "y": 0}]

        asyncio.run(run_test())

    def test_tools_call_plugin_exception(self, monkeypatch):
        """tools/call must wrap plugin exceptions in MCP error."""

        async def run_test():
            transport = MCPTransport()

            class FailingPlugin:
                name = "failing_plugin"
                tools = {
                    "ocr": {
                        "handler": "analyze_image",
                        "description": "OCR analysis",
                        "input_schema": {"type": "object"},
                        "output_schema": {"type": "object"},
                    }
                }

                def analyze_image(self, image_bytes, options):
                    raise Exception("Plugin failed")

                def run_tool(self, tool_name, args):
                    if tool_name == "ocr":
                        return self.analyze_image(
                            args["image_bytes"], args.get("options", {})
                        )
                    raise ValueError(f"Unknown tool: {tool_name}")

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
                    "arguments": {"image": "dGVzdF9kYXRh"},
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

            class UnicodePlugin:
                name = "unicode_plugin"
                tools = {
                    "ocr": {
                        "handler": "analyze_image",
                        "description": "OCR analysis",
                        "input_schema": {"type": "object"},
                        "output_schema": {"type": "object"},
                    }
                }

                def analyze_image(self, image_bytes, options):
                    return {
                        "text": "Héllo wørld 中文 🎉 émojis",
                        "confidence": 0.95,
                        "metadata": {"lang": "multi", "chars": "spëcial"},
                    }

                def run_tool(self, tool_name, args):
                    if tool_name == "ocr":
                        return self.analyze_image(
                            args["image_bytes"], args.get("options", {})
                        )
                    raise ValueError(f"Unknown tool: {tool_name}")

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
                    "arguments": {"image": "dGVzdF9kYXRh"},
                },
                id=9,
            )

            response = await transport.handle_request(request)

            assert response.error is None
            assert response.result is not None

            content = response.result["content"]
            assert content[0]["type"] == "text"

            import json

            json_payload = json.loads(content[0]["text"])
            assert "Héllo wørld 中文" in json_payload["text"]
            assert json_payload["metadata"]["chars"] == "spëcial"

        asyncio.run(run_test())

    def test_tools_call_plugin_returning_non_json_serializable(self, monkeypatch):
        """tools/call must handle plugins returning non-JSON-serializable objects."""

        async def run_test():
            transport = MCPTransport()

            class BadPlugin:
                def analyze(self, image_bytes, options):
                    import datetime

                    return {
                        "timestamp": datetime.datetime.now(),
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
                    "arguments": {"image": "dGVzdF9kYXRh"},
                },
                id=10,
            )

            response = await transport.handle_request(request)

            assert response.error is not None

        asyncio.run(run_test())

    def test_tools_call_plugin_returning_pydantic_model(self, monkeypatch):
        """tools/call must convert Pydantic models to dict for JSON serialization."""

        async def run_test():
            from pydantic import BaseModel

            transport = MCPTransport()

            class AnalysisResult(BaseModel):
                text: str
                confidence: float
                blocks: list

            class PydanticPlugin:
                name = "pydantic_plugin"
                tools = {
                    "ocr": {
                        "handler": "analyze_image",
                        "description": "OCR analysis",
                        "input_schema": {"type": "object"},
                        "output_schema": {"type": "object"},
                    }
                }

                def analyze_image(self, image_bytes, options):
                    return AnalysisResult(
                        text="extracted text",
                        confidence=0.95,
                        blocks=[{"x": 0, "y": 0, "text": "line1"}],
                    )

                def run_tool(self, tool_name, args):
                    if tool_name == "ocr":
                        return self.analyze_image(
                            args["image_bytes"], args.get("options", {})
                        )
                    raise ValueError(f"Unknown tool: {tool_name}")

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
                    "arguments": {"image": "dGVzdF9kYXRh"},
                },
                id=11,
            )

            response = await transport.handle_request(request)

            assert response.error is None
            assert response.result is not None

            content = response.result["content"]
            assert content[0]["type"] == "text"

            import json

            parsed = json.loads(content[0]["text"])
            assert parsed["text"] == "extracted text"
            assert parsed["confidence"] == 0.95
            assert parsed["blocks"] == [{"x": 0, "y": 0, "text": "line1"}]

        asyncio.run(run_test())

    def test_mcp_route_large_json_response_serialization(self, monkeypatch):
        """MCP route must serialize large JSON responses correctly."""

        async def run_test():
            from fastapi import FastAPI
            from fastapi.testclient import TestClient

            from app.mcp.routes import router
            from app.plugin_loader import PluginRegistry

            app = FastAPI()
            app.include_router(router)

            class LargePlugin:
                name = "large_plugin"
                tools = {
                    "ocr": {
                        "handler": "analyze_image",
                        "description": "OCR analysis",
                        "input_schema": {"type": "object"},
                        "output_schema": {"type": "object"},
                    }
                }

                def analyze_image(self, image_bytes, options):
                    return {
                        "text": "x" * 5000,
                        "confidence": 0.9,
                        "blocks": [
                            {"x": i, "y": i, "text": "block" * 50} for i in range(50)
                        ],
                    }

                def run_tool(self, tool_name, args):
                    if tool_name == "ocr":
                        return self.analyze_image(
                            args["image_bytes"], args.get("options", {})
                        )
                    raise ValueError(f"Unknown tool: {tool_name}")

            plugin_manager = PluginRegistry()
            monkeypatch.setattr(plugin_manager, "get", lambda name: LargePlugin())
            monkeypatch.setattr(plugin_manager, "list", lambda: {"ocr": {}})
            app.state.plugins = plugin_manager

            # Reset global transport
            import app.mcp.routes as routes_module

            routes_module._transport = None

            client = TestClient(app)

            response = client.post(
                "/mcp",
                json={
                    "jsonrpc": "2.0",
                    "method": "tools/call",
                    "params": {
                        "name": "ocr",
                        "arguments": {"image": "dGVzdF9kYXRh"},
                    },
                    "id": 14,
                },
            )

            assert (
                response.status_code == 200
            ), f"Status {response.status_code}: {response.text}"

            data = response.json()
            assert data.get("error") is None, f"Error: {data.get('error')}"
            assert data["result"]["content"][0]["type"] == "text"

            import json

            result_json = json.loads(data["result"]["content"][0]["text"])
            assert len(result_json["text"]) == 5000
            assert len(result_json["blocks"]) == 50

        asyncio.run(run_test())
