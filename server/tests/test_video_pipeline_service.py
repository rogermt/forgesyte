"""Tests for VideoPipelineService.

Phase 13 - Multi-Tool Linear Pipelines
"""

from app.services.video_pipeline_service import VideoPipelineService


def test_import():
    """Test service can be imported."""
    assert VideoPipelineService is not None


def test_instantiation():
    """Test service can be instantiated."""
    from tests.helpers import FakeRegistry

    registry = FakeRegistry(plugin=None)
    service = VideoPipelineService(plugins=registry)
    assert service is not None


def test_run_pipeline_method_exists():
    """Test run_pipeline method exists."""
    from tests.helpers import FakeRegistry

    registry = FakeRegistry(plugin=None)
    service = VideoPipelineService(plugins=registry)
    assert hasattr(service, "run_pipeline")
    assert callable(service.run_pipeline)


def test_validate_method_exists():
    """Test _validate method exists."""
    from tests.helpers import FakeRegistry

    registry = FakeRegistry(plugin=None)
    service = VideoPipelineService(plugins=registry)
    assert hasattr(service, "_validate")
    assert callable(service._validate)
