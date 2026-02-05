"""TEST-CHANGE: Startup audit test for Phase 11 plugin registry consistency.

Verifies:
- Audit detects registry divergence (discovered ≠ registered)
- Audit detects missing plugins (discovered but not in registry)
- Audit passes when registry is consistent
- Audit fails hard in strict mode
"""

import pytest

from app.plugins.loader.plugin_registry import get_registry
from app.plugins.loader.startup_audit import run_startup_audit


class TestStartupAudit:
    """Tests for Phase 11 startup audit."""

    def setup_method(self) -> None:
        """Clear registry before each test."""
        # Note: We need to reset the singleton between tests
        # This is a test-only operation
        from app.plugins.loader.plugin_registry import PluginRegistry

        PluginRegistry._instance = None

    def test_audit_passes_with_empty_registry(self) -> None:
        """Audit should pass when no plugins discovered and registry empty."""
        run_startup_audit([])  # Should not raise

    def test_audit_fails_when_plugins_discovered_but_registry_empty(
        self, monkeypatch
    ) -> None:
        """Audit should fail when plugins discovered but registry is empty."""
        # Set strict mode to test failure
        monkeypatch.setenv("PHASE11_STRICT_AUDIT", "1")

        # Don't register the plugin - just claim it was discovered
        with pytest.raises(RuntimeError, match="registry empty"):
            run_startup_audit(["test_plugin"])

    def test_audit_passes_when_discovered_plugin_registered(self) -> None:
        """Audit should pass when discovered plugins are all registered."""
        registry = get_registry()
        registry.register("test_plugin_1", "Test Plugin 1", "1.0")

        # Audit should pass (no exception)
        run_startup_audit(["test_plugin_1"])

    def test_audit_detects_missing_plugins(self, monkeypatch) -> None:
        """Audit should detect plugins discovered but not in registry."""
        # Set strict mode to test failure
        monkeypatch.setenv("PHASE11_STRICT_AUDIT", "1")

        registry = get_registry()
        registry.register("ocr", "OCR Plugin", "1.0")

        # Discover two plugins but only register one
        with pytest.raises(RuntimeError, match="Missing from registry"):
            run_startup_audit(["ocr", "unknown_plugin"])

    def test_audit_strict_mode_enforces_consistency(self, monkeypatch) -> None:
        """In strict mode, audit should fail hard on divergence."""
        # Set strict mode
        monkeypatch.setenv("PHASE11_STRICT_AUDIT", "1")

        # Don't register anything
        with pytest.raises(RuntimeError, match="INVARIANT VIOLATED"):
            run_startup_audit(["test_plugin"])

    def test_audit_logs_registry_state(self, caplog) -> None:
        """Audit should log registry state."""
        registry = get_registry()
        registry.register("test_plugin", "Test", "1.0")

        # Capture logs
        with caplog.at_level("INFO"):
            run_startup_audit(["test_plugin"])

        # Check that audit logged registry contents
        assert "Startup Audit" in caplog.text or "audit" in caplog.text.lower()

    def test_audit_verifies_lifecycle_state_exists(self) -> None:
        """Audit should verify all plugins have lifecycle state."""
        registry = get_registry()
        registry.register("test_plugin", "Test", "1.0")

        # Should pass because register() sets lifecycle state
        run_startup_audit(["test_plugin"])

        # Verify the plugin actually has a state
        status = registry.get_status("test_plugin")
        assert status is not None
        assert status.state is not None
