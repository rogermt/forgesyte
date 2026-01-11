"""Tests for ImageAcquisitionService."""

import os
import sys
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

# Add the server directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from app.exceptions import ExternalServiceError
from app.services.image_acquisition import ImageAcquisitionService


class TestImageAcquisitionService:
    """Test ImageAcquisitionService functionality."""

    @pytest.fixture
    def service(self):
        return ImageAcquisitionService(timeout=1.0, max_retries=2)

    def test_init_validates_params(self):
        """Test initialization validates parameters."""
        with pytest.raises(ValueError):
            ImageAcquisitionService(timeout=-1)
        with pytest.raises(ValueError):
            ImageAcquisitionService(max_retries=0)

    @pytest.mark.asyncio
    async def test_fetch_image_success(self, service):
        """Test successful image fetch."""
        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = MagicMock()
            mock_client_cls.return_value.__aenter__.return_value = mock_client

            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.content = b"image_data"
            mock_client.get = AsyncMock(return_value=mock_response)

            data = await service.fetch_image_from_url("http://example.com/image.png")
            assert data == b"image_data"

    @pytest.mark.asyncio
    async def test_fetch_image_invalid_url(self, service):
        """Test fetch with invalid URL."""
        with pytest.raises(ValueError):
            await service.fetch_image_from_url("")

    @pytest.mark.asyncio
    async def test_fetch_image_http_error(self, service):
        """Test fetch handles HTTP errors (404, etc)."""
        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = MagicMock()
            mock_client_cls.return_value.__aenter__.return_value = mock_client

            mock_response = MagicMock()
            mock_response.status_code = 404
            mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
                "Not Found", request=MagicMock(), response=mock_response
            )
            mock_client.get = AsyncMock(return_value=mock_response)

            with pytest.raises(ExternalServiceError) as exc:
                await service.fetch_image_from_url("http://example.com/missing.png")
            assert "HTTP 404" in str(exc.value)

    @pytest.mark.asyncio
    async def test_fetch_image_retry_on_network_error(self, service):
        """Test fetch retries on network errors."""
        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = MagicMock()
            mock_client_cls.return_value.__aenter__.return_value = mock_client

            # Fail all attempts
            mock_client.get = AsyncMock(
                side_effect=httpx.NetworkError("Connection failed")
            )

            # Should raise retry error or network error depending on tenacity config
            # Since reraise=True, it should raise the original exception (NetworkError)
            with pytest.raises(httpx.NetworkError):
                await service.fetch_image_from_url("http://example.com/retry.png")

            # Should have tried max_retries times
            assert mock_client.get.call_count == service.max_retries

    @pytest.mark.asyncio
    async def test_validate_image_url_success(self, service):
        """Test validate URL success."""
        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = MagicMock()
            mock_client_cls.return_value.__aenter__.return_value = mock_client

            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_client.head = AsyncMock(return_value=mock_response)

            is_valid = await service.validate_image_url("http://example.com/image.png")
            assert is_valid is True

    @pytest.mark.asyncio
    async def test_validate_image_url_failure(self, service):
        """Test validate URL failure."""
        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = MagicMock()
            mock_client_cls.return_value.__aenter__.return_value = mock_client

            mock_response = MagicMock()
            mock_response.status_code = 404
            mock_client.head = AsyncMock(return_value=mock_response)

            is_valid = await service.validate_image_url(
                "http://example.com/missing.png"
            )
            assert is_valid is False

    @pytest.mark.asyncio
    async def test_validate_image_url_exception(self, service):
        """Test validate URL handles exceptions."""
        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = MagicMock()
            mock_client_cls.return_value.__aenter__.return_value = mock_client

            mock_client.head = AsyncMock(side_effect=httpx.RequestError("Failed"))

            is_valid = await service.validate_image_url("http://example.com/error.png")
            assert is_valid is False
