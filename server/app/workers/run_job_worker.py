"""Startup script for JobWorker - processes video jobs from queue.

Run as:
  python -m server.app.workers.run_job_worker

Or:
  python server/app/workers/run_job_worker.py
"""

import logging
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from server.app.workers.worker import JobWorker

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


def main():
    """Start the JobWorker."""
    try:
        logger.info("🚀 Starting JobWorker (Phase 16)...")

        # Initialize worker with defaults:
        # - queue: InMemoryQueueService
        # - session_factory: SessionLocal
        # - storage: provided by services
        # - pipeline_service: provided by services
        worker = JobWorker()

        logger.info("✅ JobWorker initialized")
        logger.info("👷 Running worker loop - waiting for jobs...")

        # Run worker forever until Ctrl+C
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
