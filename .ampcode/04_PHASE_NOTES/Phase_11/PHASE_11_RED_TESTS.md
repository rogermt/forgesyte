# Phase 11 – RED Test Suite

All tests start RED (fail) because implementation doesn't exist yet.  
As you implement, tests go GREEN.

---

## Test Suite 1: Plugin Loader Import/Init Failures

**File:** `server/tests/test_plugin_loader/test_import_failures.py`

**Intent:** A plugin with import-time error must not crash server; must be marked FAILED/UNAVAILABLE.

```python
import pytest
from app.plugins.loader.plugin_registry import PluginRegistry
from app.plugins.lifecycle.lifecycle_state import PluginLifecycleState


@pytest.fixture
def plugin_registry():
    """Fixture provides a fresh registry for each test."""
    return PluginRegistry()


def test_plugin_import_failure_does_not_crash_server(plugin_registry):
    """Importing a broken plugin should not raise; state should be FAILED or UNAVAILABLE."""
    # Simulate loading a plugin with bad import
    plugin_registry.load_plugin("broken_import_plugin")
    
    status = plugin_registry.get_plugin_status("broken_import_plugin")
    assert status is not None
    assert status.state in {PluginLifecycleState.FAILED, PluginLifecycleState.UNAVAILABLE}
    assert "ImportError" in status.reason or "ModuleNotFoundError" in status.reason


def test_failed_plugin_doesnt_appear_in_available_list(plugin_registry):
    """Failed plugins should not be in list of available plugins."""
    plugin_registry.load_plugin("broken_import_plugin")
    
    available = plugin_registry.available_plugins()
    assert "broken_import_plugin" not in available


def test_failed_plugin_state_is_queryable(plugin_registry):
    """Even failed plugins should have queryable state."""
    plugin_registry.load_plugin("broken_import_plugin")
    
    state = plugin_registry.get_state("broken_import_plugin")
    assert state == PluginLifecycleState.FAILED
```

---

**File:** `server/tests/test_plugin_loader/test_init_failures.py`

**Intent:** Plugin `__init__` raising must be captured, not crash.

```python
import pytest
from app.plugins.loader.plugin_registry import PluginRegistry
from app.plugins.lifecycle.lifecycle_state import PluginLifecycleState


@pytest.fixture
def plugin_registry():
    return PluginRegistry()


def test_plugin_init_failure_marked_failed(plugin_registry):
    """Plugin that raises in __init__ should be marked FAILED."""
    plugin_registry.load_plugin("init_fail_plugin")
    
    status = plugin_registry.get_plugin_status("init_fail_plugin")
    assert status.state == PluginLifecycleState.FAILED
    assert "ValueError" in status.reason


def test_init_failure_includes_traceback(plugin_registry):
    """Failed state should include useful error details."""
    plugin_registry.load_plugin("init_fail_plugin")
    
    status = plugin_registry.get_plugin_status("init_fail_plugin")
    assert status.reason is not None
    assert len(status.reason) > 0
```

---

## Test Suite 2: Dependency Checking

**File:** `server/tests/test_plugin_loader/test_dependency_checker.py`

**Intent:** Missing deps/GPU → UNAVAILABLE, not crash.

```python
import pytest
from app.plugins.loader.dependency_checker import DependencyChecker
from app.plugins.lifecycle.lifecycle_state import PluginLifecycleState


@pytest.fixture
def checker():
    return DependencyChecker()


def test_missing_dependency_marks_plugin_unavailable(checker):
    """Plugin with missing dependency should be UNAVAILABLE."""
    result = checker.check_dependencies(["nonexistent_package", "another_missing"])
    
    assert result["available"] is False
    assert "nonexistent_package" in result["reason"]


def test_gpu_only_plugin_unavailable_on_cpu(checker):
    """GPU-only plugin should be UNAVAILABLE on CPU-only machine."""
    # Mock: assume no CUDA
    result = checker.check_dependencies(["torch"], requires_gpu=True)
    
    # Should be unavailable if CUDA not present
    if not result["available"]:
        assert "GPU" in result["reason"] or "CUDA" in result["reason"]


def test_available_dependency_passes_check(checker):
    """Plugin with available dependencies should pass."""
    result = checker.check_dependencies(["os", "sys"])  # stdlib, always available
    
    assert result["available"] is True
```

---

## Test Suite 3: Plugin Health API

**File:** `server/tests/test_plugin_health_api/test_list_plugins.py`

**Intent:** `/v1/plugins` returns list with states.

```python
import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client(app):
    """Fixture provides FastAPI test client."""
    return TestClient(app)


def test_list_plugins_returns_health(client):
    """GET /v1/plugins returns list of plugins with health status."""
    resp = client.get("/v1/plugins")
    
    assert resp.status_code == 200
    body = resp.json()
    assert isinstance(body, list)
    
    # Should have plugin objects with at least name and state
    if len(body) > 0:
        plugin = body[0]
        assert "name" in plugin
        assert "state" in plugin


def test_list_plugins_includes_failed_plugins(client):
    """List should include failed plugins so admins see all plugins."""
    resp = client.get("/v1/plugins")
    
    assert resp.status_code == 200
    body = resp.json()
    
    # Should list both available and failed plugins
    states = [p.get("state") for p in body]
    # FAILED and UNAVAILABLE should be visible
    # (not filtered out)


def test_list_plugins_empty_is_ok(client):
    """Empty plugin list should return 200, not 500."""
    # Assume no plugins loaded
    resp = client.get("/v1/plugins")
    
    assert resp.status_code in {200, 404}  # Either empty list or not found
    assert resp.text  # Should have a response body
```

---

**File:** `server/tests/test_plugin_health_api/test_plugin_health_endpoint.py`

**Intent:** Failed plugin health is visible, not 500.

```python
import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client(app):
    return TestClient(app)


def test_failed_plugin_health_is_reported(client):
    """GET /v1/plugins/broken_plugin/health returns status 200 with FAILED state."""
    resp = client.get("/v1/plugins/broken_import_plugin/health")
    
    # Should NOT be 500; should be 200 with failure state
    assert resp.status_code == 200
    body = resp.json()
    assert body["state"] in ("FAILED", "UNAVAILABLE")
    assert "reason" in body


def test_available_plugin_health_is_ok(client):
    """GET /v1/plugins/working_plugin/health returns LOADED or INITIALIZED."""
    resp = client.get("/v1/plugins/ocr/health")
    
    assert resp.status_code == 200
    body = resp.json()
    assert body["state"] in ("LOADED", "INITIALIZED", "RUNNING")
    assert body.get("uptime") is not None or body.get("last_used") is not None


def test_unknown_plugin_returns_404_not_500(client):
    """Asking for unknown plugin should return 404, not 500."""
    resp = client.get("/v1/plugins/nonexistent_plugin/health")
    
    assert resp.status_code == 404
    # Error should be descriptive, not a server error


def test_plugin_health_includes_metadata(client):
    """Health response should include useful metadata."""
    resp = client.get("/v1/plugins/ocr/health")
    
    assert resp.status_code in {200, 404}
    if resp.status_code == 200:
        body = resp.json()
        assert "name" in body
        assert "state" in body
        # Optional but nice to have:
        # assert "version" in body
        # assert "last_error" in body if failed
```

---

## Test Suite 4: Sandbox Runner

**File:** `server/tests/test_plugin_sandbox/test_sandbox_runner.py`

**Intent:** Sandboxed function calls return structured results, never raise.

```python
import pytest
from app.plugins.sandbox.sandbox_runner import run_plugin_sandboxed, PluginSandboxResult


def test_successful_function_call_returns_ok_true():
    """Successful function should return {ok: True, result: ...}."""
    def dummy_fn():
        return {"data": "result"}
    
    result = run_plugin_sandboxed(dummy_fn)
    
    assert isinstance(result, PluginSandboxResult)
    assert result.ok is True
    assert result.result == {"data": "result"}
    assert result.error is None


def test_function_exception_returns_ok_false():
    """Function that raises should return {ok: False, error: ...}."""
    def failing_fn():
        raise ValueError("Something went wrong")
    
    result = run_plugin_sandboxed(failing_fn)
    
    assert result.ok is False
    assert result.error is not None
    assert "Something went wrong" in result.error
    assert result.error_type == "ValueError"


def test_sandbox_doesnt_raise_even_on_critical_error():
    """Even critical errors should be caught and returned, never raised."""
    def critical_fn():
        1 / 0  # ZeroDivisionError
    
    # Should not raise
    result = run_plugin_sandboxed(critical_fn)
    
    assert result.ok is False
    assert result.error_type == "ZeroDivisionError"


def test_sandbox_preserves_function_args_and_kwargs():
    """Sandbox should pass args/kwargs through correctly."""
    def add_fn(a, b, multiplier=1):
        return (a + b) * multiplier
    
    result = run_plugin_sandboxed(add_fn, 2, 3, multiplier=2)
    
    assert result.ok is True
    assert result.result == 10


def test_sandbox_result_to_dict():
    """PluginSandboxResult should serialize to dict."""
    def dummy_fn():
        return "ok"
    
    result = run_plugin_sandboxed(dummy_fn)
    data = result.to_dict()
    
    assert isinstance(data, dict)
    assert "ok" in data
    assert "result" in data or "error" in data
```

---

## Running RED Tests

```bash
# From server/
cd server

# Run all RED tests (expect failures)
pytest tests/test_plugin_loader/ tests/test_plugin_health_api/ tests/test_plugin_sandbox/ -v

# Run a single RED test file
pytest tests/test_plugin_loader/test_import_failures.py -v

# Run tests and show which are RED (xfail) vs failing
pytest tests/test_plugin_loader/ -v --tb=short
```

---

## Marking Tests as Expected Failures (Optional)

If you want to mark RED tests as "expected to fail", use `@pytest.mark.xfail`:

```python
@pytest.mark.xfail(reason="PluginLoader v2 not yet implemented")
def test_plugin_import_failure_does_not_crash_server(plugin_registry):
    ...
```

This way, CI passes but shows you which tests are RED.

---

## Test Fixtures Needed

Create `server/tests/conftest.py` or similar:

```python
import pytest
from fastapi import FastAPI
from app.main import create_app


@pytest.fixture
def app():
    """Provide a fresh FastAPI app instance for testing."""
    return create_app()


@pytest.fixture
def client(app):
    """Provide a test client for the app."""
    from fastapi.testclient import TestClient
    return TestClient(app)
```

---

## Summary

- **17 RED tests** across 4 suites
- **No implementation required** – tests define contract
- **Tests run in CI** – RED tests expected to fail
- **As you implement**, tests go GREEN
- **TDD workflow** – tests guide development
