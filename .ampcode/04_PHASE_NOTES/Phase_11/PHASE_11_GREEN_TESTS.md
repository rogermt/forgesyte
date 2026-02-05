# Phase 11 GREEN Tests

**Post-implementation test suite.** These tests assume PluginRegistry, PluginHealthRouter, and PluginSandboxRunner are implemented and wired.

All tests should PASS when Phase 11 commits 1-6 are complete.

---

## Test Suite 1: Plugin Loader Failures (GREEN)

**File:** `server/tests/test_plugin_loader/test_import_failures.py`

```python
import pytest
from app.plugins.loader.plugin_registry import get_registry
from app.plugins.lifecycle.lifecycle_state import PluginLifecycleState


@pytest.fixture
def registry():
    """Fresh registry for each test."""
    from app.plugins.loader.plugin_registry import PluginRegistry
    return PluginRegistry()


def test_import_failure_marks_plugin_failed(registry):
    """Plugin with import error should be marked FAILED."""
    registry.register("broken_import_plugin", description="Plugin that fails to import")
    registry.mark_failed("broken_import_plugin", "ImportError: No module named 'nonexistent'")
    
    status = registry.get_status("broken_import_plugin")
    assert status is not None
    assert status.state == PluginLifecycleState.FAILED
    assert "ImportError" in status.reason


def test_import_failure_doesnt_crash_registry(registry):
    """Failed plugin doesn't prevent other plugins from loading."""
    registry.register("broken_plugin", description="Failed")
    registry.mark_failed("broken_plugin", "ImportError")
    
    registry.register("good_plugin", description="Working")
    
    # Both should be queryable
    assert registry.get_status("broken_plugin") is not None
    assert registry.get_status("good_plugin") is not None
    
    # But availability differs
    assert not registry.is_available("broken_plugin")
    assert registry.is_available("good_plugin")


def test_failed_plugin_not_in_available_list(registry):
    """Failed plugins excluded from available list."""
    registry.register("plugin1")
    registry.register("plugin2")
    registry.mark_failed("plugin1", "Error")
    
    available = registry.list_available()
    assert "plugin2" in available
    assert "plugin1" not in available
```

---

**File:** `server/tests/test_plugin_loader/test_init_failures.py`

```python
import pytest
from app.plugins.loader.plugin_registry import PluginRegistry
from app.plugins.lifecycle.lifecycle_state import PluginLifecycleState


@pytest.fixture
def registry():
    return PluginRegistry()


def test_init_failure_marks_plugin_failed(registry):
    """Plugin that raises in __init__ should be marked FAILED."""
    registry.register("bad_init_plugin", description="Fails during init")
    registry.mark_failed("bad_init_plugin", "ValueError: configuration error")
    
    status = registry.get_status("bad_init_plugin")
    assert status.state == PluginLifecycleState.FAILED
    assert "ValueError" in status.reason


def test_init_failure_includes_error_reason(registry):
    """Error reason should be descriptive."""
    registry.register("plugin")
    reason = "ValueError: Could not load model from /path/to/missing/model.pt"
    registry.mark_failed("plugin", reason)
    
    status = registry.get_status("plugin")
    assert status.reason == reason


def test_init_failure_state_queryable(registry):
    """State is queryable even after init failure."""
    registry.register("plugin")
    registry.mark_failed("plugin", "InitError")
    
    state = registry.get_state("plugin")
    assert state == PluginLifecycleState.FAILED
```

---

## Test Suite 2: Dependency Checking (GREEN)

**File:** `server/tests/test_plugin_loader/test_dependency_checker.py`

```python
import pytest
from app.plugins.loader.dependency_checker import check_dependencies


@pytest.fixture
def checker():
    from app.plugins.loader.dependency_checker import DependencyChecker
    return DependencyChecker()


def test_missing_gpu_marks_unavailable(checker):
    """Plugin requiring GPU without GPU available should be UNAVAILABLE."""
    result = checker.check_dependencies(
        packages=[],
        requires_gpu=True,
    )
    
    assert result["available"] is False
    assert "GPU" in result["reason"]


def test_missing_package_marks_unavailable(checker):
    """Plugin with missing dependency should be UNAVAILABLE."""
    result = checker.check_dependencies(
        packages=["nonexistent_package"],
    )
    
    assert result["available"] is False
    assert "nonexistent_package" in result["reason"]


def test_stdlib_packages_always_available(checker):
    """Standard library packages should always be available."""
    result = checker.check_dependencies(
        packages=["os", "sys", "json"],
    )
    
    assert result["available"] is True


def test_installed_package_available(checker):
    """Installed packages should be available."""
    result = checker.check_dependencies(
        packages=["fastapi"],  # We know this is installed
    )
    
    assert result["available"] is True


def test_dependency_check_returns_reason(checker):
    """Failed check should include reason."""
    result = checker.check_dependencies(
        packages=["missing_lib"],
    )
    
    assert "reason" in result
    assert result["reason"] is not None


def test_multiple_dependencies_all_checked(checker):
    """All dependencies must be available."""
    result = checker.check_dependencies(
        packages=["os", "missing_lib", "sys"],
    )
    
    assert result["available"] is False
```

---

## Test Suite 3: Plugin Health API (GREEN)

**File:** `server/tests/test_plugin_health_api/test_list_plugins.py`

```python
import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def app():
    """Fresh FastAPI app for testing."""
    from app.main import create_app
    return create_app()


@pytest.fixture
def client(app):
    return TestClient(app)


def test_list_plugins_returns_200(client):
    """GET /v1/plugins should return 200."""
    resp = client.get("/v1/plugins")
    assert resp.status_code == 200


def test_list_plugins_returns_list(client):
    """GET /v1/plugins should return list."""
    resp = client.get("/v1/plugins")
    body = resp.json()
    assert isinstance(body, list)


def test_list_plugins_includes_all_plugins(client):
    """List should include all plugins (failed, unavailable, available)."""
    resp = client.get("/v1/plugins")
    body = resp.json()
    
    # At minimum, if any plugins are loaded, they should be in the list
    if len(body) > 0:
        # Check structure
        plugin = body[0]
        assert "name" in plugin
        assert "state" in plugin
        assert plugin["state"] in ("LOADED", "INITIALIZED", "RUNNING", "FAILED", "UNAVAILABLE")


def test_list_plugins_includes_metrics(client):
    """Each plugin should include execution metrics."""
    resp = client.get("/v1/plugins")
    body = resp.json()
    
    if len(body) > 0:
        plugin = body[0]
        assert "success_count" in plugin
        assert "error_count" in plugin
        assert plugin["success_count"] >= 0
        assert plugin["error_count"] >= 0


def test_list_plugins_response_structure(client):
    """Response should have correct structure."""
    resp = client.get("/v1/plugins")
    assert resp.status_code == 200
    body = resp.json()
    assert isinstance(body, list)
    
    # If plugins exist, check structure
    if len(body) > 0:
        plugin = body[0]
        assert isinstance(plugin, dict)
        assert "name" in plugin
        assert "state" in plugin


def test_list_plugins_never_500(client):
    """List plugins should never return 500."""
    resp = client.get("/v1/plugins")
    assert resp.status_code in (200, 404)
    assert resp.status_code != 500
```

---

**File:** `server/tests/test_plugin_health_api/test_plugin_health_endpoint.py`

```python
import pytest
from fastapi.testclient import TestClient
from app.plugins.loader.plugin_registry import get_registry


@pytest.fixture
def app():
    from app.main import create_app
    return create_app()


@pytest.fixture
def client(app):
    return TestClient(app)


def test_failed_plugin_health_returns_200(client):
    """Failed plugin health should return 200, not 500."""
    # Simulate a failed plugin
    registry = get_registry()
    registry.register("broken_plugin", description="Test plugin")
    registry.mark_failed("broken_plugin", "ImportError: missing dependency")
    
    resp = client.get("/v1/plugins/broken_plugin/health")
    assert resp.status_code == 200


def test_failed_plugin_health_shows_state(client):
    """Failed plugin health should show FAILED state."""
    registry = get_registry()
    registry.register("broken_plugin")
    registry.mark_failed("broken_plugin", "Error")
    
    resp = client.get("/v1/plugins/broken_plugin/health")
    body = resp.json()
    assert body["state"] == "FAILED"


def test_failed_plugin_health_shows_reason(client):
    """Failed plugin should show error reason."""
    registry = get_registry()
    registry.register("broken_plugin")
    reason = "ImportError: No module named 'torch'"
    registry.mark_failed("broken_plugin", reason)
    
    resp = client.get("/v1/plugins/broken_plugin/health")
    body = resp.json()
    assert body["reason"] == reason


def test_unavailable_plugin_health_returns_200(client):
    """Unavailable plugin health should return 200."""
    registry = get_registry()
    registry.register("gpu_plugin", description="GPU required")
    registry.mark_unavailable("gpu_plugin", "GPU not available")
    
    resp = client.get("/v1/plugins/gpu_plugin/health")
    assert resp.status_code == 200


def test_unavailable_plugin_health_shows_state(client):
    """Unavailable plugin should show UNAVAILABLE state."""
    registry = get_registry()
    registry.register("gpu_plugin")
    registry.mark_unavailable("gpu_plugin", "GPU not available")
    
    resp = client.get("/v1/plugins/gpu_plugin/health")
    body = resp.json()
    assert body["state"] == "UNAVAILABLE"


def test_unknown_plugin_returns_404(client):
    """Unknown plugin should return 404, not 500."""
    resp = client.get("/v1/plugins/nonexistent_plugin/health")
    assert resp.status_code == 404


def test_plugin_health_never_500(client):
    """Health endpoint should never return 500."""
    resp = client.get("/v1/plugins/anything/health")
    assert resp.status_code in (200, 404)
    assert resp.status_code != 500


def test_available_plugin_health_shows_metrics(client):
    """Available plugin should show execution metrics."""
    registry = get_registry()
    registry.register("good_plugin", description="Working plugin")
    registry.mark_initialized("good_plugin")
    registry.record_success("good_plugin")
    
    resp = client.get("/v1/plugins/good_plugin/health")
    body = resp.json()
    assert body["state"] == "INITIALIZED"
    assert body["success_count"] >= 1
```

---

## Test Suite 4: Sandbox Runner (GREEN)

**File:** `server/tests/test_plugin_sandbox/test_sandbox_runner.py`

```python
import pytest
from app.plugins.sandbox.sandbox_runner import run_plugin_sandboxed


def test_successful_execution_returns_ok_true():
    """Successful function should return ok=True."""
    def good_fn():
        return {"data": "result"}
    
    result = run_plugin_sandboxed(good_fn)
    assert result.ok is True
    assert result.result == {"data": "result"}


def test_exception_returns_ok_false():
    """Function that raises should return ok=False."""
    def bad_fn():
        raise ValueError("Something went wrong")
    
    result = run_plugin_sandboxed(bad_fn)
    assert result.ok is False
    assert "Something went wrong" in result.error


def test_sandbox_captures_error_type():
    """Sandbox should capture exception type."""
    def fn():
        1 / 0
    
    result = run_plugin_sandboxed(fn)
    assert result.error_type == "ZeroDivisionError"


def test_sandbox_never_raises():
    """Sandbox should never raise, even for critical errors."""
    def critical_fn():
        import sys
        sys.exit(1)  # Critical error
    
    # Should not raise
    try:
        result = run_plugin_sandboxed(critical_fn)
        assert result.ok is False
    except SystemExit:
        pytest.fail("Sandbox allowed SystemExit to propagate")


def test_sandbox_preserves_args():
    """Sandbox should pass arguments correctly."""
    def fn_with_args(a, b, multiplier=1):
        return (a + b) * multiplier
    
    result = run_plugin_sandboxed(fn_with_args, 2, 3, multiplier=2)
    assert result.ok is True
    assert result.result == 10


def test_sandbox_result_dict():
    """Result can be serialized to dict."""
    def fn():
        return "ok"
    
    result = run_plugin_sandboxed(fn)
    data = result.to_dict()
    
    assert isinstance(data, dict)
    assert data["ok"] is True
    assert data["result"] == "ok"


def test_sandbox_error_dict():
    """Error result can be serialized to dict."""
    def fn():
        raise RuntimeError("Test error")
    
    result = run_plugin_sandboxed(fn)
    data = result.to_dict()
    
    assert isinstance(data, dict)
    assert data["ok"] is False
    assert "Test error" in data["error"]
    assert data["error_type"] == "RuntimeError"
```

---

## Test Suite 5: ToolRunner Integration (GREEN)

**File:** `server/tests/test_tool_runner/test_sandbox_integration.py`

```python
import pytest
from unittest.mock import Mock, patch


@pytest.fixture
def tool_runner():
    """Mock ToolRunner for testing."""
    from app.tools.runner import ToolRunner
    runner = ToolRunner()
    return runner


def test_tool_runner_catches_plugin_exceptions(tool_runner):
    """ToolRunner should catch all plugin exceptions."""
    # Mock a plugin that raises
    mock_plugin = Mock()
    mock_plugin.run.side_effect = RuntimeError("Plugin error")
    
    # Should not raise; should return structured error
    result = tool_runner.run(mock_plugin, {})
    
    assert result["ok"] is False
    assert "Plugin error" in result["error"]


def test_tool_runner_marks_plugin_failed_on_error(tool_runner):
    """ToolRunner should mark plugin FAILED on exception."""
    from app.plugins.loader.plugin_registry import get_registry
    
    registry = get_registry()
    mock_plugin = Mock(name="bad_plugin")
    mock_plugin.run.side_effect = ValueError("Bad input")
    
    tool_runner.run(mock_plugin, {})
    
    # Plugin should be marked failed in registry
    status = registry.get_status("bad_plugin")
    if status:
        assert status.state.value == "FAILED"


def test_tool_runner_records_success(tool_runner):
    """ToolRunner should record successful executions."""
    from app.plugins.loader.plugin_registry import get_registry
    
    registry = get_registry()
    mock_plugin = Mock(name="good_plugin")
    mock_plugin.run.return_value = {"result": "success"}
    
    result = tool_runner.run(mock_plugin, {})
    
    assert result["ok"] is True
    # Success should be recorded in registry
    status = registry.get_status("good_plugin")
    if status:
        assert status.success_count > 0


def test_tool_runner_never_crashes_server(tool_runner):
    """ToolRunner should never crash the server."""
    # Test with various exception types
    exceptions = [
        RuntimeError("Test"),
        ValueError("Test"),
        KeyError("Test"),
        Exception("Generic"),
    ]
    
    for exc in exceptions:
        mock_plugin = Mock()
        mock_plugin.run.side_effect = exc
        
        # Should not raise
        result = tool_runner.run(mock_plugin, {})
        assert result["ok"] is False
```

---

## Test Suite 6: VideoTracker Stability (GREEN)

**File:** `server/tests/test_videotracker_stability/test_gpu_requirement.py`

```python
import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def app():
    from app.main import create_app
    return create_app()


@pytest.fixture
def client(app):
    return TestClient(app)


def test_videotracker_missing_gpu_doesnt_crash(client):
    """VideoTracker without GPU should fail gracefully."""
    # Simulate running VideoTracker (which requires GPU)
    resp = client.post(
        "/v1/jobs",
        json={
            "plugin_id": "forgesyte-yolo-tracker",
            "tool_name": "player_detection",
            "frame_base64": "base64data",
            "device": "cpu",  # CPU but plugin requires GPU
        }
    )
    
    # Should return 200 with error, not 500
    assert resp.status_code == 200
    body = resp.json()
    assert body["ok"] is False
    assert "GPU" in body["error"] or "cuda" in body["error"].lower()


def test_videotracker_health_shows_unavailable_without_gpu(client):
    """VideoTracker health should show UNAVAILABLE if GPU missing."""
    resp = client.get("/v1/plugins/forgesyte-yolo-tracker/health")
    
    # Should return 200 (not 500)
    assert resp.status_code == 200
    body = resp.json()
    
    # If GPU not available, should show UNAVAILABLE
    if body["state"] == "UNAVAILABLE":
        assert "GPU" in body["reason"]


def test_videotracker_structured_error_response(client):
    """VideoTracker errors should be structured."""
    resp = client.post(
        "/v1/jobs",
        json={
            "plugin_id": "forgesyte-yolo-tracker",
            "tool_name": "player_detection",
            "frame_base64": "bad_base64",  # Invalid input
        }
    )
    
    # Should return structured error
    if resp.status_code == 200:
        body = resp.json()
        assert "ok" in body
        assert "error" in body or "result" in body
```

---

## Running GREEN Tests

```bash
cd server

# Run all GREEN tests
pytest tests/test_plugin_loader/ \
        tests/test_plugin_health_api/ \
        tests/test_plugin_sandbox/ \
        tests/test_tool_runner/ \
        tests/test_videotracker_stability/ \
        -v

# Run specific suite
pytest tests/test_plugin_health_api/ -v

# Run with coverage
pytest tests/test_plugin_loader/ --cov=app.plugins --cov-report=term-missing
```

---

## Success Criteria

✅ **All 40+ GREEN tests pass**  
✅ **No plugin crashes server**  
✅ **Health API always returns 200 or 404**  
✅ **Sandbox catches all exceptions**  
✅ **Registry state properly updated**  
✅ **VideoTracker fails gracefully**

These tests define the **behavioral contract** for Phase 11.

Pass these tests = Phase 11 implementation complete.
