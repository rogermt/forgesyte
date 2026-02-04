"""Test Phase 10: Inspector Service.

This test verifies that the InspectorService properly inspects plugin metadata.
"""

from app.plugins.inspector.inspector_service import InspectorService


def test_inspector_service_init():
    """Verify InspectorService initializes with empty plugins."""
    service = InspectorService()
    assert service.plugins == {}
    assert service.list_plugins() == []


def test_inspector_service_register_plugin():
    """Verify InspectorService can register a plugin."""
    service = InspectorService()

    metadata = {
        "name": "test-plugin",
        "version": "1.0.0",
        "capabilities": ["detection", "classification"],
        "latency_budget": 100,
    }

    service.register_plugin("test-plugin", metadata)

    assert "test-plugin" in service.list_plugins()


def test_inspector_service_extract_metadata():
    """Verify InspectorService can extract plugin metadata."""
    service = InspectorService()

    metadata = {
        "name": "test-plugin",
        "version": "1.0.0",
    }

    service.register_plugin("test-plugin", metadata)
    extracted = service.extract_metadata("test-plugin")

    assert extracted is not None
    assert extracted["name"] == "test-plugin"
    assert extracted["version"] == "1.0.0"


def test_inspector_service_extract_nonexistent():
    """Verify InspectorService returns None for non-existent plugin."""
    service = InspectorService()

    result = service.extract_metadata("nonexistent")
    assert result is None


def test_inspector_service_analyze_health():
    """Verify InspectorService can analyze plugin health."""
    service = InspectorService()

    metadata = {
        "name": "test-plugin",
        "capabilities": ["detection"],
        "latency_budget": 100,
    }

    service.register_plugin("test-plugin", metadata)
    health = service.analyze_health("test-plugin")

    assert health["status"] == "healthy"
    assert health["plugin_id"] == "test-plugin"
    assert "detection" in health["capabilities"]


def test_inspector_service_analyze_unknown():
    """Verify InspectorService handles unknown plugin health."""
    service = InspectorService()

    health = service.analyze_health("unknown")

    assert health["status"] == "unknown"
    assert health["plugin_id"] == "unknown"


def test_inspector_service_generate_report():
    """Verify InspectorService can generate a detailed report."""
    service = InspectorService()

    metadata = {
        "name": "test-plugin",
        "version": "1.0.0",
    }

    service.register_plugin("test-plugin", metadata)
    report = service.generate_report("test-plugin")

    assert report["plugin_id"] == "test-plugin"
    assert report["metadata"]["name"] == "test-plugin"
    assert "health" in report
    assert "generated_at" in report


def test_inspector_service_get_all_reports():
    """Verify InspectorService can generate reports for all plugins."""
    service = InspectorService()

    service.register_plugin("plugin-1", {"name": "Plugin 1"})
    service.register_plugin("plugin-2", {"name": "Plugin 2"})

    reports = service.get_all_reports()

    assert "plugin-1" in reports
    assert "plugin-2" in reports
    assert len(reports) == 2
