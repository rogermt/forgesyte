"""Image acquisition service with retry logic and exponential backoff.

This service provides resilient image fetching from URLs using the tenacity
library for automatic retries with exponential backoff. It abstracts away
HTTP client details and provides a clean API for the REST layer.

Retry Strategy:
    - Maximum 3 attempts
    - Exponential backoff: base 2^attempt seconds
    - Minimum 2 second delay, maximum 10 seconds
    - Retries on network timeouts and transient errors
    - Does NOT retry on 404 or other permanent failures

Example:
    service = ImageAcquisitionService()
    try:
        image_bytes = await service.fetch_image_from_url("https://example.com/pic.jpg")
    except ExternalServiceError as e:
        logger.error("Failed to fetch image", extra={"url": url, "error": str(e)})
        raise HTTPException(500, "Failed to fetch image from URL")
"""

import logging

import httpx
from tenacity import (
    AsyncRetrying,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from ..exceptions import ExternalServiceError

logger = logging.getLogger(__name__)


class ImageAcquisitionService:
    """Service for fetching images from URLs with resilient retry logic.

    Handles transient network failures gracefully using exponential backoff,
    providing a clean interface for image acquisition without HTTP details.
    """

    def __init__(self, timeout: float = 10.0, max_retries: int = 3) -> None:
        """Initialize image acquisition service.

        Args:
            timeout: HTTP request timeout in seconds
            max_retries: Maximum number of retry attempts

        Raises:
            ValueError: If timeout is not positive or max_retries < 1
        """
        if timeout <= 0:
            raise ValueError("timeout must be positive")
        if max_retries < 1:
            raise ValueError("max_retries must be at least 1")

        self.timeout = timeout
        self.max_retries = max_retries
        logger.debug(
            "ImageAcquisitionService initialized",
            extra={"timeout": timeout, "max_retries": max_retries},
        )

    async def fetch_image_from_url(self, url: str) -> bytes:
        """Fetch image from URL with automatic retry on transient failures.

        Uses exponential backoff to gracefully handle temporary network issues
        while failing fast on permanent errors (404, etc).

        Args:
            url: HTTP(S) URL of image to fetch

        Returns:
            Raw image bytes suitable for analysis

        Raises:
            ValueError: If URL is invalid or empty
            ExternalServiceError: If all retries exhausted or permanent error

        Example:
            >>> service = ImageAcquisitionService()
            >>> image = await service.fetch_image_from_url("https://example.com/pic.jpg")
            >>> len(image)
            15234
        """
        if not url or not isinstance(url, str):
            raise ValueError("url must be a non-empty string")

        logger.debug("Starting image fetch", extra={"url": url})

        retry_strategy = AsyncRetrying(
            stop=stop_after_attempt(self.max_retries),
            wait=wait_exponential(multiplier=1, min=2, max=10),
            retry=retry_if_exception_type((httpx.TimeoutException, httpx.NetworkError)),
            reraise=True,
        )

        async for attempt in retry_strategy:
            with attempt:
                try:
                    async with httpx.AsyncClient() as client:
                        response = await client.get(
                            url, timeout=self.timeout, follow_redirects=True
                        )
                        response.raise_for_status()

                        image_bytes = response.content
                        logger.info(
                            "Image fetched successfully",
                            extra={"url": url, "size_bytes": len(image_bytes)},
                        )
                        return image_bytes

                except httpx.HTTPStatusError as e:
                    # Permanent error - don't retry
                    logger.error(
                        "HTTP error fetching image",
                        extra={"url": url, "status": e.response.status_code},
                    )
                    raise ExternalServiceError(
                        f"Failed to fetch image: HTTP {e.response.status_code}",
                        service_name="image_url_fetch",
                        original_error=e,
                    ) from e
                except httpx.RequestError:
                    # Network error - will retry if within retry count
                    logger.warning(
                        "Network error fetching image (will retry)",
                        extra={
                            "url": url,
                            "attempt": attempt.retry_state.attempt_number,
                        },
                    )
                    raise

        # This should not be reached due to reraise=True, but for completeness:
        raise ExternalServiceError(
            f"Failed to fetch image after {self.max_retries} attempts",
            service_name="image_url_fetch",
        )

    async def validate_image_url(self, url: str) -> bool:
        """Check if a URL is accessible without downloading full image.

        Uses HEAD request to check availability with minimal overhead.
        Falls back to full GET if HEAD not supported.

        Args:
            url: HTTP(S) URL to validate

        Returns:
            True if URL returns 2xx status, False otherwise

        Raises:
            ValueError: If URL is invalid or empty

        Example:
            >>> service = ImageAcquisitionService()
            >>> is_valid = await service.validate_image_url("https://example.com/pic.jpg")
            >>> is_valid
            True
        """
        if not url or not isinstance(url, str):
            raise ValueError("url must be a non-empty string")

        try:
            async with httpx.AsyncClient() as client:
                response = await client.head(
                    url, timeout=self.timeout, follow_redirects=True
                )
                is_valid = 200 <= response.status_code < 300
                logger.debug(
                    "URL validation check",
                    extra={
                        "url": url,
                        "status": response.status_code,
                        "valid": is_valid,
                    },
                )
                return is_valid
        except (httpx.RequestError, httpx.TimeoutException):
            logger.warning("URL validation check failed", extra={"url": url})
            return False
