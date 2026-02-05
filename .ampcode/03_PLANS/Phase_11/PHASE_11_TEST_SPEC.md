# Phase 11 Test Specification (Helper Document)

This file specifies the 40+ tests for Phase 11. NOT for approval - just for builder reference.

---

## Test Suite 1: Import Failures (3 tests)

### test_import_error_marks_plugin_failed.py

```python
def test_import_error_marks_plugin_failed(plugin_registry):
    """ImportError should mark plugin as FAILED."""
    # Simulate loading a plugin with ImportError
    result = plugin_registry.load_plugin("broken_import_plugin")
    
    # Verify
    status = plugin_registry.get_status("broken_import_plugin")
    assert status.state == State.FAILED
    assert "ImportError" in status.reason
```

### test_import_failure_doesnt_crash_server.py

```python
def test_import_failure_doesnt_crash_server(plugin_registry):
    """Import failure should NOT crash the server."""
    # This should NOT raise
    result = plugin_registry.load_plugin("bad_plugin")
    
    # Server should still be running
    assert True  # If we got here, server didn't crash
```

### test_failed_plugin_not_in_available_list.py

```python
def test_failed_plugin_not_in_available_list(plugin_registry):
    """Failed plugins should NOT appear in available list."""
    plugin_registry.load_plugin("broken_plugin")
    
    available = plugin_registry.list_available()
    
    assert "broken_plugin" not in available
```

---

## Test Suite 2: Init Failures (2 tests)

### test_init_error_marks_plugin_failed.py

```python
def test_init_error_marks_plugin_failed(plugin_registry):
    """Init error should mark plugin as FAILED."""
    plugin_registry.load_plugin("bad_init_plugin")
    
    status = plugin_registry.get_status("bad_init_plugin")
    assert status.state == State.FAILED
    assert "ValueError" in status.reason or "RuntimeError" in status.reason
```

### test_init_failure_includes_useful_message.py

```python
def test_init_failure_includes_useful_message(plugin_registry):
    """Init failure reason should be actionable."""
    plugin_registry.load_plugin("bad_init_plugin")
    
    status = plugin_registry.get_status("bad_init_plugin")
    
    # Reason should include what went wrong AND how to fix
    assert status.reason is not None
    assert len(status.reason) > 10  # Not just "Error"
    assert "install" in status.reason.lower() or "pip" in status.reason.lower() or "missing" in status.reason.lower()
```

---

## Test Suite 3: Dependency Checking (6 tests)

### test_missing_gpu_marks_unavailable.py

```python
def test_missing_gpu_marks_unavailable(dependency_checker):
    """Missing GPU should mark plugin UNAVAILABLE."""
    result = dependency_checker.check_gpu()
    
    assert result["available"] is False
    assert "GPU" in result["reason"] or "CUDA" in result["reason"]
```

### test_torch_check_alone.py

```python
def test_torch_check_alone(dependency_checker):
    """torch.cuda.is_available() should work."""
    result = dependency_checker.check_package("torch")
    
    # torch may or may not be available, but check should work
    assert "available" in result
```

### test_nvidia_smi_check.py

```python
def test_nvidia_smi_check(dependency_checker):
    """nvidia-smi check should work."""
    result = dependency_checker.check_nvidia_smi()
    
    # Should return True or False, not error
    assert "available" in result
```

### test_dual_gpu_check.py

```python
def test_dual_gpu_check(dependency_checker):
    """Both torch AND nvidia-smi should be checked."""
    result = dependency_checker.check_gpu_dual()
    
    # Both must be True for GPU to be available
    assert "torch_ok" in result
    assert "nvidia_ok" in result
    assert result["available"] == (result["torch_ok"] and result["nvidia_ok"])
```

### test_model_file_exists.py

```python
def test_model_file_exists(dependency_checker):
    """Existing model file should pass."""
    # Create a temp file
    import tempfile
    import os
    
    with tempfile.NamedTemporaryFile(delete=False) as f:
        f.write(b"fake model data")
        path = f.name
    
    try:
        result = dependency_checker.check_model_file(path)
        assert result["available"] is True
    finally:
        os.unlink(path)
```

### test_model_file_reads_bytes.py

```python
def test_model_file_reads_bytes(dependency_checker):
    """Model check should read first 16 bytes to detect corruption."""
    import tempfile
    import os
    
    # Create truncated file (less than 16 bytes)
    with tempfile.NamedTemporaryFile(delete=False) as f:
        f.write(b"short")
        path = f.name
    
    try:
        result = dependency_checker.check_model_file(path)
        assert result["available"] is False
        assert "truncated" in result["reason"].lower() or "corrupt" in result["reason"].lower()
    finally:
        os.unlink(path)
```

---

## Test Suite 4: Health API (8 tests)

### test_list_plugins_returns_200.py

```python
def test_list_plugins_returns_200(client):
    """GET /v1/plugins should return 200."""
    resp = client.get("/v1/plugins")
    assert resp.status_code == 200
```

### test_list_plugins_returns_list.py

```python
def test_list_plugins_returns_list(client):
    """GET /v1/plugins should return a list."""
    resp = client.get("/v1/plugins")
    body = resp.json()
    assert isinstance(body, list)
```

### test_list_plugins_includes_all_states.py

```python
def test_list_plugins_includes_all_states(client):
    """List should include LOADED, FAILED, UNAVAILABLE plugins."""
    resp = client.get("/v1/plugins")
    body = resp.json()
    
    # Should list all plugins regardless of state
    states = [p["state"] for p in body]
    
    assert "LOADED" in states
    # May or may not have FAILED/UNAVAILABLE depending on test setup
```

### test_plugin_health_returns_200.py

```python
def test_plugin_health_returns_200(client, loaded_plugin):
    """GET /v1/plugins/{name}/health should return 200."""
    resp = client.get(f"/v1/plugins/{loaded_plugin}/health")
    assert resp.status_code == 200
```

### test_plugin_health_shows_state.py

```python
def test_plugin_health_shows_state(client, loaded_plugin):
    """Health response should include state."""
    resp = client.get(f"/v1/plugins/{loaded_plugin}/health")
    body = resp.json()
    
    assert "state" in body
    assert body["state"] in ["LOADED", "INITIALIZED", "RUNNING"]
```

### test_failed_plugin_health_returns_200.py

```python
def test_failed_plugin_health_returns_200(client, failed_plugin):
    """Failed plugin health should return 200 (not 500)."""
    resp = client.get(f"/v1/plugins/{failed_plugin}/health")
    
    # Should return 200 even for failed plugins
    assert resp.status_code == 200
    body = resp.json()
    assert body["state"] == "FAILED"
    assert body["reason"] is not None
```

### test_unknown_plugin_returns_404.py

```python
def test_unknown_plugin_returns_404(client):
    """Unknown plugin should return 404 (not 500)."""
    resp = client.get("/v1/plugins/nonexistent_plugin/health")
    assert resp.status_code == 404
```

### test_health_never_returns_500.py

```python
def test_health_never_returns_500(client):
    """Health API should never return 500."""
    # Test with various inputs
    resp1 = client.get("/v1/plugins")
    resp2 = client.get("/v1/plugins/unknown/health")
    resp3 = client.get("/v1/plugins/also_unknown/health")
    
    # All should be 200 or 404
    for resp in [resp1, resp2, resp3]:
        assert resp.status_code != 500
```

---

## Test Suite 5: Sandbox Runner (6 tests)

### test_sandbox_returns_ok_true.py

```python
def test_sandbox_returns_ok_true():
    """Successful function should return ok=True."""
    def good_fn():
        return {"data": "result"}
    
    result = run_plugin_sandboxed(good_fn)
    
    assert result.ok is True
    assert result.result == {"data": "result"}
```

### test_sandbox_returns_ok_false_on_error.py

```python
def test_sandbox_returns_ok_false_on_error():
    """Failing function should return ok=False."""
    def bad_fn():
        raise ValueError("test error")
    
    result = run_plugin_sandboxed(bad_fn)
    
    assert result.ok is False
    assert result.error == "test error"
    assert result.error_type == "ValueError"
```

### test_sandbox_never_raises.py

```python
def test_sandbox_never_raises():
    """Sandbox should NEVER raise to caller."""
    def critical_fn():
        1 / 0
    
    # Should not raise
    result = run_plugin_sandboxed(critical_fn)
    assert result.ok is False
```

### test_sandbox_preserves_args.py

```python
def test_sandbox_preserves_args():
    """Sandbox should pass args correctly."""
    def fn_with_args(a, b, multiplier=1):
        return (a + b) * multiplier
    
    result = run_plugin_sandboxed(fn_with_args, 2, 3, multiplier=2)
    
    assert result.ok is True
    assert result.result == 10
```

### test_sandbox_result_to_dict.py

```python
def test_sandbox_result_to_dict():
    """Result should be serializable to dict."""
    def fn():
        return "ok"
    
    result = run_plugin_sandboxed(fn)
    data = result.to_dict()
    
    assert isinstance(data, dict)
    assert data["ok"] is True
```

### test_sandbox_catches_all_exceptions.py

```python
def test_sandbox_catches_all_exceptions():
    """Sandbox should catch all exception types."""
    exceptions = [
        ValueError("test"),
        RuntimeError("test"),
        KeyError("test"),
        TypeError("test"),
        Exception("generic"),
    ]
    
    for exc in exceptions:
        def fn():
            raise exc
        
        result = run_plugin_sandboxed(fn)
        assert result.ok is False
        assert result.error_type == exc.__class__.__name__
```

---

## Test Suite 6: ToolRunner Integration (4 tests)

### test_tool_runner_uses_sandbox.py

```python
def test_tool_runner_uses_sandbox(tool_runner, plugin_registry):
    """ToolRunner should use sandbox for plugin calls."""
    # Mock plugin that raises
    mock_plugin = Mock()
    mock_plugin.run.side_effect = RuntimeError("Plugin error")
    
    # Should not raise - should catch in sandbox
    result = tool_runner.run(mock_plugin, {})
    
    assert result["ok"] is False
    assert "Plugin error" in result["error"]
```

### test_tool_runner_marks_failed.py

```python
def test_tool_runner_marks_failed(tool_runner, plugin_registry):
    """ToolRunner should mark plugin FAILED on error."""
    mock_plugin = Mock()
    mock_plugin.run.side_effect = ValueError("Bad input")
    
    tool_runner.run(mock_plugin, {})
    
    status = plugin_registry.get_status(mock_plugin.name)
    assert status.state == State.FAILED
```

### test_tool_runner_records_success.py

```python
def test_tool_runner_records_success(tool_runner, plugin_registry):
    """ToolRunner should record successful executions."""
    mock_plugin = Mock()
    mock_plugin.run.return_value = {"result": "success"}
    
    tool_runner.run(mock_plugin, {})
    
    status = plugin_registry.get_status(mock_plugin.name)
    assert status.success_count >= 1
```

### test_tool_runner_never_crashes_server.py

```python
def test_tool_runner_never_crashes_server(tool_runner):
    """ToolRunner should never crash server on any plugin error."""
    # Test with various exception types
    exceptions = [
        RuntimeError("Test"),
        ValueError("Test"),
        KeyError("Test"),
        MemoryError("Test"),
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

## Test Suite 7: VideoTracker Stability (4 tests)

### test_videotracker_missing_gpu_marked_unavailable.py

```python
def test_videotracker_missing_gpu_marked_unavailable(plugin_registry):
    """VideoTracker without GPU should be UNAVAILABLE."""
    plugin_registry.register("forgesyte-yolo-tracker")
    plugin_registry.mark_unavailable(
        "forgesyte-yolo-tracker",
        "CUDA GPU not available"
    )
    
    status = plugin_registry.get_status("forgesyte-yolo-tracker")
    assert status.state == State.UNAVAILABLE
    assert "GPU" in status.reason
```

### test_videotracker_missing_models_marked_unavailable.py

```python
def test_videotracker_missing_models_marked_unavailable(plugin_registry):
    """VideoTracker missing models should be UNAVAILABLE."""
    plugin_registry.register("forgesyte-yolo-tracker")
    plugin_registry.mark_unavailable(
        "forgesyte-yolo-tracker",
        "Model file not found: models/player-detection.pt"
    )
    
    status = plugin_registry.get_status("forgesyte-yolo-tracker")
    assert status.state == State.UNAVAILABLE
```

### test_videotracker_tool_error_sandboxed.py

```python
def test_videotracker_tool_error_sandboxed():
    """VideoTracker tool error should be caught by sandbox."""
    def failing_tool():
        raise RuntimeError("CUDA out of memory")
    
    result = run_plugin_sandboxed(failing_tool)
    
    assert result.ok is False
    assert "CUDA" in result.error or "memory" in result.error.lower()
```

### test_videotracker_health_api_shows_unavailable.py

```python
def test_videotracker_health_api_shows_unavailable(client, app):
    """Health API should show VideoTracker UNAVAILABLE without GPU."""
    # Setup: mark videotracker unavailable
    registry = get_registry()
    registry.register("forgesyte-yolo-tracker")
    registry.mark_unavailable("forgesyte-yolo-tracker", "GPU required")
    
    resp = client.get("/v1/plugins/forgesyte-yolo-tracker/health")
    
    assert resp.status_code == 200
    body = resp.json()
    assert body["state"] == "UNAVAILABLE"
```

---

## Test Suite 8: Metrics (3 tests)

### test_success_count_tracked.py

```python
def test_success_count_tracked(plugin_registry):
    """Success count should be tracked."""
    plugin_registry.register("test_plugin")
    plugin_registry.record_success("test_plugin")
    plugin_registry.record_success("test_plugin")
    
    status = plugin_registry.get_status("test_plugin")
    assert status.success_count == 2
```

### test_error_count_tracked.py

```python
def test_error_count_tracked(plugin_registry):
    """Error count should be tracked."""
    plugin_registry.register("test_plugin")
    plugin_registry.record_error("test_plugin")
    
    status = plugin_registry.get_status("test_plugin")
    assert status.error_count == 1
```

### test_uptime_seconds_calculated.py

```python
def test_uptime_seconds_calculated(plugin_registry):
    """Uptime should be calculated from loaded_at."""
    plugin_registry.register("test_plugin")
    
    status = plugin_registry.get_status("test_plugin")
    
    assert status.uptime_seconds is not None
    assert status.uptime_seconds >= 0
```

---

## Test Suite 9: Timeout/Memory Guards (4 tests)

### test_timeout_enforced.py

```python
def test_timeout_enforced():
    """Timeout should be enforced."""
    def slow_fn():
        import time
        time.sleep(10)  # 10 seconds
    
    # Run with 1 second timeout
    result = run_with_timeout(slow_fn, timeout_seconds=1)
    
    assert result.ok is False
    assert "timeout" in result.error.lower()
```

### test_timeout_preserves_fast_plugins.py

```python
def test_timeout_preserves_fast_plugins():
    """Fast plugins should complete before timeout."""
    def fast_fn():
        return "done"
    
    result = run_with_timeout(fast_fn, timeout_seconds=60)
    
    assert result.ok is True
    assert result.result == "done"
```

### test_memory_limit_enforced.py

```python
def test_memory_limit_enforced():
    """Memory limit should be enforced."""
    def big_memory_fn():
        import numpy as np
        # Allocate 2GB
        return np.zeros((1024, 1024, 1024))
    
    # Run with 512MB limit
    result = run_with_memory_limit(big_memory_fn, memory_mb=512)
    
    assert result.ok is False
    assert "memory" in result.error.lower() or "limit" in result.error.lower()
```

### test_memory_preserves_small_plugins.py

```python
def test_memory_preserves_small_plugins():
    """Small plugins should work within memory limit."""
    def small_fn():
        return {"data": "small"}
    
    result = run_with_memory_limit(small_fn, memory_mb=1024)
    
    assert result.ok is True
```

---

## Summary

| Suite | Tests | Location |
|-------|-------|----------|
| Import Failures | 3 | test_plugin_loader/ |
| Init Failures | 2 | test_plugin_loader/ |
| Dependency Checking | 6 | test_plugin_loader/ |
| Health API | 8 | test_plugin_health_api/ |
| Sandbox Runner | 6 | test_plugin_sandbox/ |
| ToolRunner Integration | 4 | test_tool_runner/ |
| VideoTracker Stability | 4 | test_videotracker_stability/ |
| Metrics | 3 | test_plugin_metrics/ |
| Timeout/Memory Guards | 4 | test_plugin_sandbox/ |

**Total: 40 tests**

---

## Fixture Requirements

```python
@pytest.fixture
def plugin_registry():
    """Fresh registry for each test."""
    from app.plugins.loader.plugin_registry import PluginRegistry
    return PluginRegistry()


@pytest.fixture
def dependency_checker():
    """Fresh dependency checker for each test."""
    from app.plugins.loader.dependency_checker import DependencyChecker
    return DependencyChecker()


@pytest.fixture
def client(app):
    """FastAPI test client."""
    from fastapi.testclient import TestClient
    return TestClient(app)


@pytest.fixture
def app():
    """Fresh FastAPI app."""
    from app.main import create_app
    return create_app()


@pytest.fixture
def loaded_plugin(plugin_registry):
    """Register and return a loaded plugin."""
    plugin_registry.register("test_plugin")
    return "test_plugin"


@pytest.fixture
def failed_plugin(plugin_registry):
    """Register and return a failed plugin."""
    plugin_registry.register("failed_plugin")
    plugin_registry.mark_failed("failed_plugin", "Test error")
    return "failed_plugin"
```

---

Reference this file when implementing tests.
