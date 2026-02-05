"""Tests for URL image fetching in tools/call."""

import asyncio
import base64
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.mcp.jsonrpc import JSONRPCRequest
from app.mcp.transport import MCPTransport

# Valid 1x1 PNG
PNG_1X1 = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8DwHwAFBQIAX8jx0gAAAABJRU5ErkJggg=="
)


class TestToolsCallURLFetch:
    """Tests that tools/call fetches URL images before passing to plugin."""

    def test_url_image_is_fetched_and_bytes_passed_to_plugin(self, monkeypatch):
        """Plugin must receive actual image bytes when given a URL."""

        async def run_test():
            transport = MCPTransport()

            received_data = {}

            class InspectorPlugin:
                name = "inspector_plugin"
                tools = {
                    "ocr": {
                        "handler": "analyze_image",
                        "description": "OCR analysis",
                        "input_schema": {"type": "object"},
                        "output_schema": {"type": "object"},
                    }
                }

                def analyze_image(self, image_bytes, options):
                    received_data["bytes"] = image_bytes
                    received_data["type"] = type(image_bytes).__name__
                    if isinstance(image_bytes, bytes) and image_bytes.startswith(
                        b"http"
                    ):
                        raise ValueError(
                            "Received URL as bytes instead of fetching image!"
                        )
                    if not image_bytes.startswith(b"\x89PNG"):
                        raise ValueError(
                            f"Expected PNG signature, got: {image_bytes[:20]!r}"
                        )
                    return {"text": "extracted", "confidence": 0.95}

                def run_tool(self, tool_name, args):
                    if tool_name == "ocr":
                        return self.analyze_image(
                            args["image"], args.get("options", {})
                        )
                    raise ValueError(f"Unknown tool: {tool_name}")

            monkeypatch.setattr(
                transport._protocol_handlers.plugin_manager,
                "get",
                lambda name: InspectorPlugin(),
            )

            import httpx

            class MockResponse:
                status_code = 200
                content = PNG_1X1

                def raise_for_status(self):
                    pass

            class MockAsyncClient:
                def __init__(self, *args, **kwargs):
                    pass

                async def __aenter__(self):
                    return self

                async def __aexit__(self, *args):
                    pass

                async def get(self, url, **kwargs):
                    received_data["fetched_url"] = url
                    return MockResponse()

            monkeypatch.setattr(httpx, "AsyncClient", MockAsyncClient)

            request = JSONRPCRequest(
                jsonrpc="2.0",
                method="tools/call",
                params={
                    "name": "ocr",
                    "arguments": {"image": "https://example.com/test.png"},
                },
                id=1,
            )

            response = await transport.handle_request(request)

            assert response.error is None, f"Unexpected error: {response.error}"
            assert received_data.get("fetched_url") == "https://example.com/test.png"
            assert received_data["bytes"] == PNG_1X1
            assert received_data["type"] == "bytes"

        asyncio.run(run_test())

    def test_url_fetch_http_error_returns_jsonrpc_error(self, monkeypatch):
        """HTTP errors during URL fetch must return JSON-RPC error."""

        async def run_test():
            transport = MCPTransport()

            class DummyPlugin:
                def analyze(self, image_bytes, options):
                    return {"ok": True}

            monkeypatch.setattr(
                transport._protocol_handlers.plugin_manager,
                "get",
                lambda name: DummyPlugin(),
            )

            import httpx

            class MockAsyncClient:
                def __init__(self, *args, **kwargs):
                    pass

                async def __aenter__(self):
                    return self

                async def __aexit__(self, *args):
                    pass

                async def get(self, url, **kwargs):
                    response = httpx.Response(404, request=httpx.Request("GET", url))
                    raise httpx.HTTPStatusError(
                        "Not Found", request=response.request, response=response
                    )

            monkeypatch.setattr(httpx, "AsyncClient", MockAsyncClient)

            request = JSONRPCRequest(
                jsonrpc="2.0",
                method="tools/call",
                params={
                    "name": "ocr",
                    "arguments": {"image": "https://example.com/notfound.png"},
                },
                id=2,
            )

            response = await transport.handle_request(request)

            assert response.error is not None
            assert (
                "404" in response.error["message"]
                or "fetch" in response.error["message"].lower()
            )

        asyncio.run(run_test())

    def test_url_fetch_network_error_returns_jsonrpc_error(self, monkeypatch):
        """Network errors during URL fetch must return JSON-RPC error."""

        async def run_test():
            transport = MCPTransport()

            class DummyPlugin:
                def analyze(self, image_bytes, options):
                    return {"ok": True}

            monkeypatch.setattr(
                transport._protocol_handlers.plugin_manager,
                "get",
                lambda name: DummyPlugin(),
            )

            import httpx

            class MockAsyncClient:
                def __init__(self, *args, **kwargs):
                    pass

                async def __aenter__(self):
                    return self

                async def __aexit__(self, *args):
                    pass

                async def get(self, url, **kwargs):
                    raise httpx.ConnectError("Connection refused")

            monkeypatch.setattr(httpx, "AsyncClient", MockAsyncClient)

            request = JSONRPCRequest(
                jsonrpc="2.0",
                method="tools/call",
                params={
                    "name": "ocr",
                    "arguments": {"image": "https://unreachable.test/img.png"},
                },
                id=3,
            )

            response = await transport.handle_request(request)

            assert response.error is not None

        asyncio.run(run_test())

    def test_base64_image_still_decoded_correctly(self, monkeypatch):
        """Base64 images must still work after URL fetch is implemented."""

        async def run_test():
            transport = MCPTransport()

            received_bytes = []

            class InspectorPlugin:
                name = "inspector_plugin"
                tools = {
                    "ocr": {
                        "handler": "analyze_image",
                        "description": "OCR analysis",
                        "input_schema": {"type": "object"},
                        "output_schema": {"type": "object"},
                    }
                }

                def analyze_image(self, image_bytes, options):
                    received_bytes.append(image_bytes)
                    return {"ok": True}

                def run_tool(self, tool_name, args):
                    if tool_name == "ocr":
                        return self.analyze_image(
                            args["image"], args.get("options", {})
                        )
                    raise ValueError(f"Unknown tool: {tool_name}")

            monkeypatch.setattr(
                transport._protocol_handlers.plugin_manager,
                "get",
                lambda name: InspectorPlugin(),
            )

            b64_image = base64.b64encode(PNG_1X1).decode("ascii")

            request = JSONRPCRequest(
                jsonrpc="2.0",
                method="tools/call",
                params={
                    "name": "ocr",
                    "arguments": {"image": b64_image},
                },
                id=4,
            )

            response = await transport.handle_request(request)

            assert response.error is None
            assert len(received_bytes) == 1
            assert received_bytes[0] == PNG_1X1

        asyncio.run(run_test())

    def test_data_url_still_decoded_correctly(self, monkeypatch):
        """Data URLs must still work after URL fetch is implemented."""

        async def run_test():
            transport = MCPTransport()

            received_bytes = []

            class InspectorPlugin:
                name = "inspector_plugin"
                tools = {
                    "ocr": {
                        "handler": "analyze_image",
                        "description": "OCR analysis",
                        "input_schema": {"type": "object"},
                        "output_schema": {"type": "object"},
                    }
                }

                def analyze_image(self, image_bytes, options):
                    received_bytes.append(image_bytes)
                    return {"ok": True}

                def run_tool(self, tool_name, args):
                    if tool_name == "ocr":
                        return self.analyze_image(
                            args["image"], args.get("options", {})
                        )
                    raise ValueError(f"Unknown tool: {tool_name}")

            monkeypatch.setattr(
                transport._protocol_handlers.plugin_manager,
                "get",
                lambda name: InspectorPlugin(),
            )

            b64_image = base64.b64encode(PNG_1X1).decode("ascii")
            data_url = f"data:image/png;base64,{b64_image}"

            request = JSONRPCRequest(
                jsonrpc="2.0",
                method="tools/call",
                params={
                    "name": "ocr",
                    "arguments": {"image": data_url},
                },
                id=5,
            )

            response = await transport.handle_request(request)

            assert response.error is None
            assert len(received_bytes) == 1
            assert received_bytes[0] == PNG_1X1

        asyncio.run(run_test())

    def test_http_url_is_also_fetched(self, monkeypatch):
        """HTTP (not HTTPS) URLs must also be fetched."""

        async def run_test():
            transport = MCPTransport()

            fetched_urls = []

            class DummyPlugin:
                name = "dummy_plugin"
                tools = {
                    "ocr": {
                        "handler": "analyze_image",
                        "description": "OCR analysis",
                        "input_schema": {"type": "object"},
                        "output_schema": {"type": "object"},
                    }
                }

                def analyze_image(self, image_bytes, options):
                    return {"ok": True}

                def run_tool(self, tool_name, args):
                    if tool_name == "ocr":
                        return self.analyze_image(
                            args["image"], args.get("options", {})
                        )
                    raise ValueError(f"Unknown tool: {tool_name}")

            monkeypatch.setattr(
                transport._protocol_handlers.plugin_manager,
                "get",
                lambda name: DummyPlugin(),
            )

            import httpx

            class MockResponse:
                status_code = 200
                content = PNG_1X1

                def raise_for_status(self):
                    pass

            class MockAsyncClient:
                def __init__(self, *args, **kwargs):
                    pass

                async def __aenter__(self):
                    return self

                async def __aexit__(self, *args):
                    pass

                async def get(self, url, **kwargs):
                    fetched_urls.append(url)
                    return MockResponse()

            monkeypatch.setattr(httpx, "AsyncClient", MockAsyncClient)

            request = JSONRPCRequest(
                jsonrpc="2.0",
                method="tools/call",
                params={
                    "name": "ocr",
                    "arguments": {"image": "http://example.com/test.png"},
                },
                id=6,
            )

            response = await transport.handle_request(request)

            assert response.error is None
            assert "http://example.com/test.png" in fetched_urls

        asyncio.run(run_test())
