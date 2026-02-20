"""Startup script for JobWorker - processes video jobs.

Run as:
  python -m server.app.workers.run_job_worker
"""

import logging
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from app.core.database import init_db  # noqa: E402
from app.plugin_loader import PluginRegistry  # noqa: E402
from app.services.storage.local_storage import LocalStorageService  # noqa: E402
from app.services.video_pipeline_service import VideoPipelineService  # noqa: E402
from app.workers.worker import JobWorker  # noqa: E402

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


def run_worker_forever(plugin_manager: PluginRegistry):
    """Run the JobWorker loop (used by FastAPI lifespan thread).

    Args:
        plugin_manager: PluginRegistry instance for plugin access
    """
    logger.info("🚀 Starting JobWorker thread...")

    storage = LocalStorageService()
    plugin_service = VideoPipelineService(plugin_manager)

    worker = JobWorker(
        storage=storage,
        plugin_service=plugin_service,
    )

    logger.info("👷 JobWorker thread initialized")
    worker.run_forever()


def main():
    """CLI entrypoint for standalone worker process."""
    try:
        logger.info("🚀 Starting JobWorker (standalone)...")

        init_db()

        plugin_manager = PluginRegistry()
        plugin_manager.load_plugins()

        storage = LocalStorageService()
        pipeline_service = VideoPipelineService(plugin_manager)

        worker = JobWorker(
            storage=storage,
            pipeline_service=pipeline_service,
        )

        logger.info("👷 JobWorker initialized")
        worker.run_forever()

    except Exception as e:
        logger.error(f"❌ JobWorker failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("⛔ JobWorker stopped by user")
        sys.exit(0)
