"""Pytest configuration for server tests."""


# Register asyncio marker
def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line("markers", "asyncio: mark test as async")
