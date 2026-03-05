"""Tests for storage factory validation and state management.

Covers:
- Issue #244: Invalid backend validation
- Issue #245: Reset helper for test isolation
"""

from unittest.mock import patch

import pytest

from app.services.storage.factory import _logged_backends, get_storage_service
from app.settings import AppSettings


class TestBackendValidation:
    """Tests for invalid backend validation (Issue #244)."""

    def test_invalid_backend_raises_value_error(self):
        """Test that invalid backend values raise ValueError."""
        settings = AppSettings(storage_backend="S33")  # typo

        with pytest.raises(ValueError) as exc_info:
            get_storage_service(settings)

        assert "Unsupported storage backend" in str(exc_info.value)
        assert "S33" in str(exc_info.value)

    def test_invalid_backend_with_whitespace_raises_value_error(self):
        """Test that invalid backend with whitespace raises ValueError."""
        settings = AppSettings(storage_backend="  invalid_backend  ")

        with pytest.raises(ValueError) as exc_info:
            get_storage_service(settings)

        assert "Unsupported storage backend" in str(exc_info.value)

    def test_valid_local_backend_accepted(self):
        """Test that 'local' backend works correctly."""
        _logged_backends.clear()
        settings = AppSettings(storage_backend="local")
        storage = get_storage_service(settings)
        assert storage is not None

    def test_valid_s3_backend_accepted(self):
        """Test that 's3' backend works correctly."""
        _logged_backends.clear()
        settings = AppSettings(
            storage_backend="s3",
            s3_bucket_name="test-bucket",
            s3_access_key="test-key",
            s3_secret_key="test-secret",
        )
        with patch("app.services.storage.factory.S3StorageService") as mock_s3_class:
            mock_s3_class.return_value = mock_s3_class
            storage = get_storage_service(settings)
            assert storage is not None
            mock_s3_class.assert_called_once()

    def test_valid_backend_case_insensitive(self):
        """Test that valid backends work with different cases."""
        _logged_backends.clear()
        for backend in ["LOCAL", "Local"]:
            settings = AppSettings(storage_backend=backend)
            storage = get_storage_service(settings)
            assert storage is not None

        # Test S3 backends separately with mock
        for backend in ["S3", "s3"]:
            settings = AppSettings(
                storage_backend=backend,
                s3_bucket_name="test-bucket",
                s3_access_key="test-key",
                s3_secret_key="test-secret",
            )
            with patch(
                "app.services.storage.factory.S3StorageService"
            ) as mock_s3_class:
                mock_s3_class.return_value = mock_s3_class
                storage = get_storage_service(settings)
                assert storage is not None


class TestResetStorageFactoryState:
    """Tests for reset helper function (Issue #245)."""

    def test_reset_storage_factory_state_exists(self):
        """Test that reset_storage_factory_state function exists."""
        from app.services.storage.factory import reset_storage_factory_state

        assert callable(reset_storage_factory_state)

    def test_reset_storage_factory_state_clears_cache(self):
        """Test that reset helper clears the _logged_backends cache."""
        from app.services.storage.factory import reset_storage_factory_state

        # Add some entries
        _logged_backends.add("local")
        _logged_backends.add("s3")
        assert len(_logged_backends) == 2

        # Reset
        reset_storage_factory_state()

        # Verify cleared
        assert len(_logged_backends) == 0

    def test_reset_storage_factory_state_idempotent(self):
        """Test that reset helper can be called multiple times safely."""
        from app.services.storage.factory import reset_storage_factory_state

        # Reset on empty cache
        _logged_backends.clear()
        reset_storage_factory_state()
        assert len(_logged_backends) == 0

        # Add entries, reset twice
        _logged_backends.add("local")
        reset_storage_factory_state()
        reset_storage_factory_state()
        assert len(_logged_backends) == 0
