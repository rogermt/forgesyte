"""Tests for Content-Length correctness in MCP responses."""

import asyncio
import os
import socket
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def _free_port() -> int:
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


class TestContentLengthCorrectness:
    """Tests that Content-Length header matches actual response body."""

    def test_large_json_response_content_length(self, monkeypatch):
        """Large responses must have correct Content-Length."""

        async def run_test():
            from fastapi import FastAPI
            from fastapi.testclient import TestClient

            from app.mcp.routes import router
            from app.plugin_loader import PluginRegistry

            app = FastAPI()
            app.include_router(router)

            class LargePlugin:
                def analyze(self, image_bytes, options):
                    return {
                        "text": "x" * 10000,
                        "confidence": 0.95,
                        "blocks": [{"id": i, "t": "block" * 100} for i in range(100)],
                    }

            pm = PluginRegistry()
            monkeypatch.setattr(pm, "get", lambda name: LargePlugin())
            monkeypatch.setattr(pm, "list", lambda: {"ocr": {}})
            app.state.plugins = pm

            import app.mcp.routes as routes_module

            routes_module._transport = None

            client = TestClient(app)
            resp = client.post(
                "/mcp",
                json={
                    "jsonrpc": "2.0",
                    "method": "tools/call",
                    "params": {"name": "ocr", "arguments": {"image": "dGVzdA=="}},
                    "id": 1,
                },
            )

            assert resp.status_code == 200

            content_length = int(resp.headers.get("content-length", 0))
            actual_length = len(resp.content)

            assert content_length == actual_length, (
                f"Content-Length header ({content_length}) != "
                f"actual body ({actual_length})"
            )

            data = resp.json()
            assert data.get("error") is None

        asyncio.run(run_test())

    def test_unicode_response_content_length(self, monkeypatch):
        """Unicode responses must count UTF-8 bytes, not characters."""

        async def run_test():
            from fastapi import FastAPI
            from fastapi.testclient import TestClient

            from app.mcp.routes import router
            from app.plugin_loader import PluginRegistry

            app = FastAPI()
            app.include_router(router)

            class UnicodePlugin:
                def analyze(self, image_bytes, options):
                    return {
                        "text": "中文日本語한국어🎉🚀" * 500,
                        "confidence": 0.99,
                    }

            pm = PluginRegistry()
            monkeypatch.setattr(pm, "get", lambda name: UnicodePlugin())
            monkeypatch.setattr(pm, "list", lambda: {"ocr": {}})
            app.state.plugins = pm

            import app.mcp.routes as routes_module

            routes_module._transport = None

            client = TestClient(app)
            resp = client.post(
                "/mcp",
                json={
                    "jsonrpc": "2.0",
                    "method": "tools/call",
                    "params": {"name": "ocr", "arguments": {"image": "dGVzdA=="}},
                    "id": 2,
                },
            )

            assert resp.status_code == 200

            content_length = int(resp.headers.get("content-length", 0))
            actual_length = len(resp.content)

            assert (
                content_length == actual_length
            ), f"Content-Length ({content_length}) != body bytes ({actual_length})"

        asyncio.run(run_test())

    @pytest.mark.asyncio
    async def test_uvicorn_no_content_length_mismatch(self, monkeypatch, caplog):
        """Real uvicorn must not log 'Response content longer than Content-Length'."""
        import httpx
        import uvicorn
        from fastapi import FastAPI

        from app.mcp.routes import router
        from app.plugin_loader import PluginRegistry

        app = FastAPI()
        app.include_router(router)

        class BigPlugin:
            def analyze(self, image_bytes, options):
                return {
                    "text": "テスト" * 3000,
                    "blocks": [{"x": i, "data": "日本語" * 100} for i in range(50)],
                }

        pm = PluginRegistry()
        monkeypatch.setattr(pm, "get", lambda name: BigPlugin())
        monkeypatch.setattr(pm, "list", lambda: {"ocr": {}})
        app.state.plugins = pm

        import app.mcp.routes as routes_module

        routes_module._transport = None

        port = _free_port()
        config = uvicorn.Config(app, host="127.0.0.1", port=port, log_level="warning")
        server = uvicorn.Server(config)

        task = asyncio.create_task(server.serve())
        while not server.started:
            await asyncio.sleep(0.01)

        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    f"http://127.0.0.1:{port}/mcp",
                    json={
                        "jsonrpc": "2.0",
                        "method": "tools/call",
                        "params": {"name": "ocr", "arguments": {"image": "dGVzdA=="}},
                        "id": 99,
                    },
                    timeout=10,
                )

            assert resp.status_code == 200
            data = resp.json()
            assert data.get("error") is None
        finally:
            server.should_exit = True
            await task

        assert "Response content longer than Content-Length" not in caplog.text
