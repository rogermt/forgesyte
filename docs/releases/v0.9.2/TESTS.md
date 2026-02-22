# v0.9.2 Image Submit Test Plan

The existing `tests/api/routes/test_image_submit.py` uses real plugins, real DB,
and real storage — making it slow and brittle. Replace with two fast test layers.

---

## 1. Fully Mocked Version (FAST)

**No disk, no plugins, no DB.** Tests only the route logic.

### What is mocked?

- `app.api_routes.routes.image_submit.storage` (LocalStorageService)
- `app.api_routes.routes.image_submit.plugin_manager` (PluginRegistry)
- `app.api_routes.routes.image_submit.plugin_service` (PluginManagementService)
- `app.api_routes.routes.image_submit.SessionLocal` (DB session)

### `tests/image/test_image_submit_mocked.py`

```python
"""Fully mocked image submit tests — no disk, no plugins, no DB."""

from io import BytesIO
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    return TestClient(app)


ROUTE = "app.api_routes.routes.image_submit"


def _mock_plugin_found():
    """Patches so plugin_manager.get() and plugin_service.get_plugin_manifest() succeed."""
    mock_plugin = MagicMock()
    mock_manifest = {
        "tools": {
            "extract_text": {
                "inputs": ["image_bytes"],
            }
        }
    }
    return (
        patch(f"{ROUTE}.plugin_manager", **{"get.return_value": mock_plugin}),
        patch(f"{ROUTE}.plugin_service", **{"get_plugin_manifest.return_value": mock_manifest}),
    )


@patch(f"{ROUTE}.SessionLocal")
@patch(f"{ROUTE}.storage")
def test_image_submit_png_fast(mock_storage, mock_db, client):
    with _mock_plugin_found()[0], _mock_plugin_found()[1]:
        fake_png = b"\x89PNG\r\n\x1a\n" + b"\x00" * 10
        response = client.post(
            "/v1/image/submit?plugin_id=ocr&tool=extract_text",
            files={"file": ("test.png", BytesIO(fake_png), "image/png")},
        )
        assert response.status_code == 200
        data = response.json()
        assert "job_id" in data
        mock_storage.save_file.assert_called_once()


@patch(f"{ROUTE}.SessionLocal")
@patch(f"{ROUTE}.storage")
def test_image_submit_jpeg_fast(mock_storage, mock_db, client):
    with _mock_plugin_found()[0], _mock_plugin_found()[1]:
        fake_jpeg = b"\xFF\xD8\xFF" + b"\x00" * 10
        response = client.post(
            "/v1/image/submit?plugin_id=ocr&tool=extract_text",
            files={"file": ("test.jpg", BytesIO(fake_jpeg), "image/jpeg")},
        )
        assert response.status_code == 200
        assert "job_id" in response.json()


def test_image_submit_invalid_file_fast(client):
    fake_file = b"this is not an image"
    response = client.post(
        "/v1/image/submit?plugin_id=ocr&tool=extract_text",
        files={"file": ("test.txt", BytesIO(fake_file), "text/plain")},
    )
    # Plugin validation runs first, but magic-byte check catches invalid files
    assert response.status_code == 400


def test_image_submit_unknown_plugin_fast(client):
    with patch(f"{ROUTE}.plugin_manager", **{"get.return_value": None}):
        fake_png = b"\x89PNG\r\n\x1a\n" + b"\x00" * 10
        response = client.post(
            "/v1/image/submit?plugin_id=nonexistent&tool=extract_text",
            files={"file": ("test.png", BytesIO(fake_png), "image/png")},
        )
        assert response.status_code == 400
        assert "not found" in response.json()["detail"].lower()


def test_image_submit_unknown_tool_fast(client):
    mock_plugin = MagicMock()
    mock_manifest = {"tools": {}}  # no tools
    with (
        patch(f"{ROUTE}.plugin_manager", **{"get.return_value": mock_plugin}),
        patch(f"{ROUTE}.plugin_service", **{"get_plugin_manifest.return_value": mock_manifest}),
    ):
        fake_png = b"\x89PNG\r\n\x1a\n" + b"\x00" * 10
        response = client.post(
            "/v1/image/submit?plugin_id=ocr&tool=nonexistent",
            files={"file": ("test.png", BytesIO(fake_png), "image/png")},
        )
        assert response.status_code == 400
        assert "not found" in response.json()["detail"].lower()
```

### Speed: ~10–50 ms per test. Run in CI.

---

## 2. Hybrid Integration Test (MEDIUM)

Uses **real FastAPI app** and **real storage** in a temp directory.
Patches only plugin_manager so no real plugin loading is needed.

### `tests/image/test_image_submit_hybrid.py`

```python
"""Hybrid integration test — real storage in tmpdir, mocked plugins."""

import tempfile
from io import BytesIO
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app

ROUTE = "app.api_routes.routes.image_submit"


@pytest.fixture
def tmp_storage(monkeypatch):
    """Patch the module-level storage object to use a temp directory."""
    from app.services.storage.local_storage import LocalStorageService
    import app.services.storage.local_storage as storage_mod

    tmpdir = tempfile.mkdtemp()
    monkeypatch.setattr(storage_mod, "BASE_DIR", tmpdir)

    svc = LocalStorageService.__new__(LocalStorageService)
    monkeypatch.setattr(f"{ROUTE}.storage", svc)
    return tmpdir


@pytest.fixture
def client(tmp_storage):
    return TestClient(app)


def _patch_plugin_ok():
    mock_plugin = MagicMock()
    mock_manifest = {
        "tools": {
            "extract_text": {"inputs": ["image_bytes"]},
        }
    }
    return (
        patch(f"{ROUTE}.plugin_manager", **{"get.return_value": mock_plugin}),
        patch(f"{ROUTE}.plugin_service", **{"get_plugin_manifest.return_value": mock_manifest}),
        patch(f"{ROUTE}.SessionLocal"),
    )


def test_image_submit_png_saves_file(client, tmp_storage):
    from pathlib import Path

    with _patch_plugin_ok()[0], _patch_plugin_ok()[1], _patch_plugin_ok()[2]:
        fake_png = b"\x89PNG\r\n\x1a\n" + b"\x00" * 50
        response = client.post(
            "/v1/image/submit?plugin_id=ocr&tool=extract_text",
            files={"file": ("test.png", BytesIO(fake_png), "image/png")},
        )
        assert response.status_code == 200

        # Verify file was actually written to temp storage
        saved_files = list(Path(tmp_storage).rglob("*.png"))
        assert len(saved_files) == 1
        assert saved_files[0].read_bytes() == fake_png
```

### Speed: ~50–150 ms. Run locally during development.

---

## Summary

| Test Type | Purpose | Speed | Mocks | Location |
|-----------|---------|-------|-------|----------|
| **Fully mocked** | Route logic only | ⚡ ~10 ms | All deps | `tests/image/test_image_submit_mocked.py` |
| **Hybrid** | Storage integration | ⚡⚡ ~100 ms | Plugin + DB | `tests/image/test_image_submit_hybrid.py` |

Both replace the current `tests/api/routes/test_image_submit.py` which hits
real plugins and hangs on auth/DB issues.
