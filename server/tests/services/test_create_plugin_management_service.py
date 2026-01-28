"""Test: ensure plugin management service uses canonical PluginRegistry."""

from app.main import create_plugin_management_service
from app.plugin_loader import PluginRegistry
from app.services.plugin_management_service import PluginManagementService


def test_create_plugin_management_service_uses_pluginregistry() -> None:
    """
    Ensure the factory returns a PluginManagementService wired to a real
    PluginRegistry instance (not PluginManager or any other alias).
    """
    service = create_plugin_management_service()

    # 1. Correct type
    assert isinstance(service, PluginManagementService)

    # 2. Registry is a concrete PluginRegistry
    registry = service.registry
    assert isinstance(registry, PluginRegistry)

    # 3. Ensure no legacy PluginManager class is involved
    assert "PluginManager" not in registry.__class__.__name__

    # 4. Ensure registry implements all required methods
    required_methods = [
        "get",
        "list",
        "load_plugins",
        "register",
        "reload_plugin",
        "reload_all",
    ]

    for method in required_methods:
        assert hasattr(registry, method), f"Missing method: {method}"
        assert callable(getattr(registry, method)), f"{method} must be callable"


def test_create_plugin_management_service_idempotent() -> None:
    """
    Ensure the factory is deterministic and creates independent instances.
    """
    service1 = create_plugin_management_service()
    service2 = create_plugin_management_service()

    # Different instances
    assert service1 is not service2
    assert service1.registry is not service2.registry

    # But same canonical type
    assert isinstance(service1.registry, PluginRegistry)
    assert isinstance(service2.registry, PluginRegistry)
