"""Pytest configuration for server tests."""

import pytest

# Set asyncio mode before pytest-asyncio imports
pytest_plugins = ("pytest_asyncio",)


@pytest.fixture(scope="session")
def event_loop_policy():
    """Set asyncio event loop policy."""
    import asyncio

    return asyncio.get_event_loop_policy()


def pytest_configure(config):
    """Register custom markers and configure asyncio."""
    config.addinivalue_line("markers", "asyncio: mark test as async")
    config.option.asyncio_mode = "auto"
