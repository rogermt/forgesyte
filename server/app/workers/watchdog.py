"""Worker watchdog - auto-restart worker if it crashes."""

import logging
import subprocess
import sys
import time

logger = logging.getLogger(__name__)


def start_worker() -> subprocess.Popen:
    """Start video worker process."""
    proc = subprocess.Popen(
        [sys.executable, "server/app/workers/run_video_worker.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return proc


def run_watchdog() -> None:
    """
    Main watchdog loop - starts worker and auto-restarts if it crashes.

    Runs as: python server/app/workers/watchdog.py
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    logger.info("👀 Watchdog: starting worker supervisor")

    while True:
        proc = start_worker()
        logger.info(f"👀 Watchdog: worker started with PID {proc.pid}")

        # Wait for worker to exit
        proc.wait()

        logger.warning(
            "⚠️ Watchdog: worker exited unexpectedly. Restarting in 2 seconds…"
        )
        time.sleep(2)


if __name__ == "__main__":
    try:
        run_watchdog()
    except KeyboardInterrupt:
        logger.info("⛔ Watchdog stopped by user")
        sys.exit(0)
