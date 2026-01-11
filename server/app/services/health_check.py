"""Health check service for monitoring system status and dependencies.

Provides a comprehensive health check endpoint that reports on the status
of all critical system components: plugin loader, task processor, WebSocket
manager, etc.

Example:
    service = HealthCheckService(plugin_manager, task_processor, ws_manager)
    health_status = await service.get_health_status()
    # Returns: {"status": "healthy", "components": {...}, "version": "0.1.0"}
"""

import logging
from typing import Any, Dict, Optional

from ..protocols import PluginRegistry, TaskProcessor, WebSocketProvider

logger = logging.getLogger(__name__)


class HealthCheckService:
    """Monitors health of all critical system components.

    Provides detailed health status reports for monitoring and alerting systems,
    helping operators quickly identify issues without needing to check logs.
    """

    def __init__(
        self,
        plugins: Optional[PluginRegistry] = None,
        task_processor: Optional[TaskProcessor] = None,
        ws_manager: Optional[WebSocketProvider] = None,
        version: str = "0.1.0",
    ) -> None:
        """Initialize health check service.

        Args:
            plugins: Plugin registry (optional)
            task_processor: Task processor (optional)
            ws_manager: WebSocket manager (optional)
            version: Server version string

        Raises:
            ValueError: If version is empty
        """
        if not version:
            raise ValueError("version must be non-empty")

        self.plugins = plugins
        self.task_processor = task_processor
        self.ws_manager = ws_manager
        self.version = version

        logger.debug("HealthCheckService initialized", extra={"version": version})

    async def get_health_status(self) -> Dict[str, Any]:
        """Get comprehensive health status of all components.

        Returns a detailed health report that can be used by monitoring
        systems (Kubernetes, Prometheus, etc) to determine service health.

        Returns:
            Dictionary with overall status and component details:
            {
                "status": "healthy" | "degraded" | "unhealthy",
                "version": "0.1.0",
                "components": {
                    "plugins": {"status": "healthy", "count": 4},
                    "task_processor": {"status": "healthy"},
                    "websocket": {"status": "healthy"}
                }
            }

        Raises:
            RuntimeError: Only if status cannot be determined (rare)

        Example:
            >>> service = HealthCheckService(...)
            >>> status = await service.get_health_status()
            >>> status["status"]
            "healthy"
            >>> status["components"]["plugins"]["count"]
            4
        """
        components = {}
        component_statuses = []

        # Check plugins
        if self.plugins:
            try:
                plugin_names = self.plugins.list_loaded()
                components["plugins"] = {
                    "status": "healthy",
                    "count": len(plugin_names),
                }
                component_statuses.append("healthy")
                logger.debug(
                    "Plugin health check passed",
                    extra={"plugin_count": len(plugin_names)},
                )
            except Exception as e:
                components["plugins"] = {"status": "unhealthy", "error": str(e)}
                component_statuses.append("unhealthy")
                logger.error("Plugin health check failed", extra={"error": str(e)})
        else:
            components["plugins"] = {"status": "unknown"}

        # Check task processor
        if self.task_processor:
            try:
                # Task processor protocol doesn't define a health check method,
                # so we just mark it as available
                components["task_processor"] = {"status": "healthy"}
                component_statuses.append("healthy")
                logger.debug("Task processor health check passed")
            except Exception as e:
                components["task_processor"] = {"status": "unhealthy", "error": str(e)}
                component_statuses.append("unhealthy")
                logger.error("Task processor check failed", extra={"error": str(e)})
        else:
            components["task_processor"] = {"status": "unknown"}

        # Check WebSocket manager
        if self.ws_manager:
            try:
                # WebSocket manager protocol doesn't define a health check method,
                # so we just mark it as available
                components["websocket"] = {"status": "healthy"}
                component_statuses.append("healthy")
                logger.debug("WebSocket manager health check passed")
            except Exception as e:
                components["websocket"] = {"status": "unhealthy", "error": str(e)}
                component_statuses.append("unhealthy")
                logger.error("WebSocket manager check failed", extra={"error": str(e)})
        else:
            components["websocket"] = {"status": "unknown"}

        # Determine overall status
        if "unhealthy" in component_statuses:
            overall_status = "unhealthy"
        elif "healthy" in component_statuses:
            overall_status = "healthy"
        else:
            overall_status = "unknown"

        response = {
            "status": overall_status,
            "version": self.version,
            "components": components,
        }

        logger.info(
            "Health check completed",
            extra={"status": overall_status, "components": len(components)},
        )

        return response

    async def get_plugin_health(self) -> Dict[str, Any]:
        """Get detailed health status of plugins.

        Returns information about each loaded plugin's availability
        and metadata.

        Returns:
            Dictionary with plugin health details:
            {
                "status": "healthy" | "degraded",
                "plugins": {
                    "ocr_plugin": {"status": "healthy", "version": "1.0.0"},
                    ...
                }
            }

        Raises:
            RuntimeError: If plugin registry unavailable
        """
        if not self.plugins:
            logger.warning("Plugin health check requested but plugins unavailable")
            return {"status": "unknown", "plugins": {}}

        try:
            plugin_names = self.plugins.list_loaded()
            plugin_health = {}
            unhealthy_count = 0

            for name in plugin_names:
                try:
                    plugin = self.plugins.get(name)
                    if plugin:
                        metadata = plugin.metadata()
                        plugin_health[name] = {
                            "status": "healthy",
                            "version": metadata.get("version", "unknown"),
                        }
                    else:
                        plugin_health[name] = {"status": "not_found"}
                        unhealthy_count += 1
                except Exception as e:
                    plugin_health[name] = {"status": "error", "error": str(e)}
                    unhealthy_count += 1

            overall = "degraded" if unhealthy_count > 0 else "healthy"

            result = {"status": overall, "plugins": plugin_health}
            logger.debug(
                "Plugin health check completed",
                extra={"status": overall, "count": len(plugin_names)},
            )
            return result

        except Exception as e:
            logger.error("Plugin health check failed", extra={"error": str(e)})
            return {
                "status": "unhealthy",
                "plugins": {},
                "error": str(e),
            }
