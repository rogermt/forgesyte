"""Service layer for ForgeSyte business logic.

Services encapsulate business logic and orchestration, abstracting away
implementation details from API endpoints. Each service depends on Protocols
(not concrete classes), making them testable and loosely coupled.

Services included:
    - ImageAcquisitionService: Fetch images from URLs with retry logic
    - VisionAnalysisService: Orchestrate image analysis across plugins
    - HealthCheckService: Monitor system health and dependencies
    - AnalysisService: Coordinate image analysis request handling
    - JobManagementService: Query and control analysis jobs
    - PluginManagementService: Discover and manage plugins

Example:
    from .image_acquisition import ImageAcquisitionService
    from .analysis_service import AnalysisService

    image_service = ImageAcquisitionService()
    service = AnalysisService(task_processor, image_service)
    result = await service.process_analysis_request(...)
"""

from .analysis_service import AnalysisService
from .health_check import HealthCheckService
from .image_acquisition import ImageAcquisitionService
from .job_management_service import JobManagementService
from .plugin_management_service import PluginManagementService
from .vision_analysis import VisionAnalysisService

__all__ = [
    "ImageAcquisitionService",
    "VisionAnalysisService",
    "HealthCheckService",
    "AnalysisService",
    "JobManagementService",
    "PluginManagementService",
]
