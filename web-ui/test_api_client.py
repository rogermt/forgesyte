"""
Test suite for WU-11: Update API client endpoints.

Ensures api/client.ts properly:
- Uses environment variables for configuration
- Implements proper error handling
- Has well-typed response interfaces
- Supports plugin listing, job management, analysis
"""

from pathlib import Path

# Get web-ui directory
WEB_UI_DIR = Path(__file__).parent


def test_api_client_exists():
    """Verify api/client.ts exists and is readable."""
    api_path = WEB_UI_DIR / "src" / "api" / "client.ts"
    assert api_path.exists(), "api/client.ts not found"
    with open(api_path, "r") as f:
        content = f.read()
    assert len(content) > 0, "api/client.ts is empty"


def test_api_client_has_base_url():
    """Verify API client defines a base URL."""
    api_path = WEB_UI_DIR / "src" / "api" / "client.ts"
    with open(api_path, "r") as f:
        content = f.read()
    assert "API_BASE" in content, "Missing API_BASE constant"
    assert "/v1" in content, "API_BASE should reference /v1 endpoint"


def test_api_client_has_interfaces():
    """Verify all required interfaces are defined."""
    api_path = WEB_UI_DIR / "src" / "api" / "client.ts"
    with open(api_path, "r") as f:
        content = f.read()

    required_interfaces = ["Plugin", "Job", "AnalysisResult"]
    for interface in required_interfaces:
        assert f"interface {interface}" in content, f"Missing interface {interface}"


def test_plugin_interface_has_required_fields():
    """Verify Plugin interface has all necessary fields."""
    api_path = WEB_UI_DIR / "src" / "api" / "client.ts"
    with open(api_path, "r") as f:
        content = f.read()

    required_fields = ["name", "description", "version", "inputs", "outputs"]
    for field in required_fields:
        assert field in content, f"Plugin interface missing {field} field"


def test_job_interface_has_status_field():
    """Verify Job interface has status field with proper union type."""
    api_path = WEB_UI_DIR / "src" / "api" / "client.ts"
    with open(api_path, "r") as f:
        content = f.read()

    assert "status:" in content, "Job interface missing status field"
    # Should have string union for job status states
    assert (
        "pending" in content or "processing" in content
    ), "Job status should include pending/processing states"


def test_api_client_class_exists():
    """Verify ForgeSyteAPIClient class is defined."""
    api_path = WEB_UI_DIR / "src" / "api" / "client.ts"
    with open(api_path, "r") as f:
        content = f.read()
    assert "class ForgeSyteAPIClient" in content, "Missing ForgeSyteAPIClient class"


def test_api_client_has_plugin_methods():
    """Verify API client has plugin-related methods."""
    api_path = WEB_UI_DIR / "src" / "api" / "client.ts"
    with open(api_path, "r") as f:
        content = f.read()
    assert "getPlugins" in content, "Missing getPlugins method"


def test_api_client_has_job_methods():
    """Verify API client has job management methods."""
    api_path = WEB_UI_DIR / "src" / "api" / "client.ts"
    with open(api_path, "r") as f:
        content = f.read()

    required_methods = ["getJob", "listJobs", "cancelJob"]
    for method in required_methods:
        assert method in content, f"Missing {method} method"


def test_api_client_has_analysis_method():
    """Verify API client has analysis/image methods."""
    api_path = WEB_UI_DIR / "src" / "api" / "client.ts"
    with open(api_path, "r") as f:
        content = f.read()
    assert (
        "analyzeImage" in content or "analyze" in content
    ), "Missing image analysis method"


def test_api_client_has_error_handling():
    """Verify API client implements error handling."""
    api_path = WEB_UI_DIR / "src" / "api" / "client.ts"
    with open(api_path, "r") as f:
        content = f.read()

    # Should check response.ok or similar
    assert (
        "response.ok" in content or "throw" in content
    ), "Missing error handling in API methods"


def test_api_client_supports_authentication():
    """Verify API client supports API key authentication."""
    api_path = WEB_UI_DIR / "src" / "api" / "client.ts"
    with open(api_path, "r") as f:
        content = f.read()

    # Should have apiKey parameter or header support
    assert (
        "apiKey" in content or "API-Key" in content or "X-API-Key" in content
    ), "Missing API key authentication support"


def test_api_client_exported():
    """Verify API client is properly exported."""
    api_path = WEB_UI_DIR / "src" / "api" / "client.ts"
    with open(api_path, "r") as f:
        content = f.read()

    assert "export" in content, "API client not exported"
    assert "apiClient" in content, "Default export missing"


def test_api_client_typesafety():
    """Verify API methods have proper return type annotations."""
    api_path = WEB_UI_DIR / "src" / "api" / "client.ts"
    with open(api_path, "r") as f:
        content = f.read()

    # Should have Promise<Type> return types
    assert "Promise<" in content, "Methods should return Promise types"
    assert "async" in content, "Methods should be async"


def test_api_fetch_helper_exists():
    """Verify private fetch helper method exists."""
    api_path = WEB_UI_DIR / "src" / "api" / "client.ts"
    with open(api_path, "r") as f:
        content = f.read()

    assert "fetch" in content.lower(), "Missing fetch helper method"
    # Should be private
    assert "private" in content, "Should have private methods"
