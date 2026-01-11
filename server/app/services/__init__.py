"""Service layer for ForgeSyte business logic.

Services encapsulate business logic and orchestration, abstracting away
implementation details from API endpoints. Each service depends on Protocols
(not concrete classes), making them testable and loosely coupled.

Services included:
    - ImageAcquisitionService: Fetch images from URLs with retry logic
    - VisionAnalysisService: Orchestrate image analysis across plugins
    - HealthCheckService: Monitor system health and dependencies

Example:
    from .image_acquisition import ImageAcquisitionService

    service = ImageAcquisitionService()
    image_bytes = await service.fetch_image_from_url("https://example.com/image.jpg")
"""

from .health_check import HealthCheckService
from .image_acquisition import ImageAcquisitionService
from .vision_analysis import VisionAnalysisService

__all__ = [
    "ImageAcquisitionService",
    "VisionAnalysisService",
    "HealthCheckService",
]
