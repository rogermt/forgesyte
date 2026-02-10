"""Analysis service for coordinating image analysis requests.

This service orchestrates the flow of image analysis requests:
1. Acquires images from multiple sources (file upload, URL, base64)
2. Validates image data and options
3. Submits tasks to the task processor
4. Returns job tracking information

The service depends on TaskProcessor and ImageAcquisitionService protocols
rather than concrete implementations, making it testable and extensible.

Example:
    from .analysis_service import AnalysisService
    from .image_acquisition import ImageAcquisitionService
    from ..tasks import task_processor

    service = AnalysisService(task_processor, ImageAcquisitionService())
    result = await service.process_analysis_request(
        file_bytes=None,
        image_url="https://example.com/image.jpg",
        body_bytes=None,
        plugin="ocr",
        options={}
    )
"""

import base64
import logging
from typing import Any, Dict, Optional

from ..exceptions import ExternalServiceError
from ..protocols import TaskProcessor
from .image_acquisition import ImageAcquisitionService

logger = logging.getLogger(__name__)


class AnalysisService:
    """Service for coordinating image analysis request handling.

    Responsible for:
    - Acquiring images from multiple sources
    - Validating input data
    - Delegating task submission to TaskProcessor
    - Returning structured results

    Depends on Protocols for flexibility:
    - TaskProcessor: Abstracts job submission
    - ImageAcquisitionService: Provides resilient image fetching
    """

    def __init__(
        self, processor: TaskProcessor, acquirer: ImageAcquisitionService
    ) -> None:
        """Initialize analysis service with dependencies.

        Args:
            processor: Task processor implementing TaskProcessor protocol
            acquirer: Image acquisition service for fetching remote images

        Raises:
            TypeError: If processor doesn't have required methods
        """
        self.processor = processor
        self.acquirer = acquirer
        logger.debug("AnalysisService initialized")

    async def process_analysis_request(
        self,
        file_bytes: Optional[bytes],
        image_url: Optional[str],
        body_bytes: Optional[bytes],
        plugin: str,
        options: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Process an image analysis request from multiple possible sources.

        Phase 12 governance: Device is NOT resolved here. It's passed through
        in options (if present) and the plugin/models.yaml are responsible for
        final resolution.

        Orchestrates the complete flow:
        1. Determine image source (file, URL, or base64 body)
        2. Acquire image bytes using appropriate method
        3. Validate options JSON
        4. Submit job to task processor
        5. Return job tracking information

        Args:
            file_bytes: Raw bytes from uploaded file (optional)
            image_url: URL to fetch image from (optional)
            body_bytes: Raw request body containing base64 image (optional)
            plugin: Name of plugin to execute
            options: Dict of plugin-specific options (already parsed, may contain device)

        Returns:
            Dictionary with:
                - job_id: Unique job identifier
                - status: Job status (queued, processing, completed, error)
                - plugin: Plugin name used
                - image_size: Size of image in bytes

        Raises:
            ValueError: If no valid image source provided
            ValueError: If image data is invalid
            ExternalServiceError: If remote image fetch fails after retries
        """
        # 1. Acquire image from appropriate source (pass options for JSON base64)
        image_bytes = await self._acquire_image(
            file_bytes, image_url, body_bytes, options
        )

        if not image_bytes:
            logger.error("No image data acquired from any source")
            raise ValueError("No valid image provided")

        # 2. Submit job to task processor (device is in options if provided)
        try:
            job_id = await self.processor.submit_job(
                image_bytes=image_bytes,
                plugin_name=plugin,
                options=options,
            )

            logger.info(
                "Analysis job submitted",
                extra={
                    "job_id": job_id,
                    "plugin": plugin,
                    "image_size": len(image_bytes),
                    "device": options.get("device"),
                },
            )

            return {
                "job_id": job_id,
                "status": "queued",
                "plugin": plugin,
                "image_size": len(image_bytes),
            }

        except Exception:
            logger.exception(
                "Failed to submit analysis job",
                extra={
                    "plugin": plugin,
                    "image_size": len(image_bytes),
                    "device": options.get("device"),
                },
            )
            raise

    async def _acquire_image(
        self,
        file_bytes: Optional[bytes],
        image_url: Optional[str],
        body_bytes: Optional[bytes],
        options: Dict[str, Any],
    ) -> Optional[bytes]:
        """Acquire image bytes from the first available source.

        Tries sources in order:
        1. File upload (file_bytes)
        2. Remote URL (image_url)
        3. Base64 in JSON options (options["image"] or options["frame"])
        4. Base64 in request body (body_bytes)

        Args:
            file_bytes: Raw bytes from file upload
            image_url: URL to fetch image from
            body_bytes: Request body containing base64 data
            options: Plugin options dict potentially containing base64 image fields

        Returns:
            Image bytes if successfully acquired, None otherwise

        Raises:
            ValueError: If base64 decoding fails
            ExternalServiceError: If URL fetch fails
        """
        # Source 1: File upload (most direct)
        if file_bytes:
            logger.debug("Using uploaded file as image source")
            return file_bytes

        # Source 2: Remote URL (with retry logic)
        if image_url:
            logger.debug("Fetching image from URL", extra={"url": image_url})
            try:
                return await self.acquirer.fetch_image_from_url(image_url)
            except ExternalServiceError as e:
                logger.error(
                    "Failed to fetch image from URL",
                    extra={"url": image_url, "error": str(e)},
                )
                raise

        # Source 3: Base64 in JSON options (most common for /v1/analyze)
        if isinstance(options.get("image"), str):
            logger.debug("Decoding base64 from JSON field 'image'")
            try:
                return base64.b64decode(options["image"])
            except Exception as e:
                logger.error("Invalid base64 in options['image']: %s", e)

        if isinstance(options.get("frame"), str):
            logger.debug("Decoding base64 from JSON field 'frame'")
            try:
                return base64.b64decode(options["frame"])
            except Exception as e:
                logger.error("Invalid base64 in options['frame']: %s", e)

        # Source 4: Base64 in request body
        if body_bytes:
            logger.debug("Decoding base64 from request body")
            try:
                return base64.b64decode(body_bytes)
            except Exception as e:
                logger.error(
                    "Invalid base64 encoding in request body",
                    extra={"error": str(e)},
                )
                raise ValueError("Invalid base64 encoding") from e

        logger.warning("No image source provided (file, URL, or body)")
        return None
