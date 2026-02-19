"""Startup script for video worker process.

Run as: python server/app/workers/run_video_worker.py
"""

import asyncio
import logging
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


async def main():
    """Start the video worker loop."""
    try:
        logger.info("🚀 Starting video worker process...")

        from server.app.workers.video_worker import worker_loop

        logger.info("✅ Worker module imported successfully")

        # Run worker loop (blocks forever)
        await worker_loop()

    except Exception as e:
        logger.error(f"❌ Worker failed to start: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("⛔ Worker stopped by user")
        sys.exit(0)
