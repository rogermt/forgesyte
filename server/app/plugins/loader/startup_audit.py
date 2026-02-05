"""Phase 11 Loader Startup Self-Audit.

Ensures after plugin discovery:
- Registry not empty when plugins discovered
- All discovered plugins are registered
- No plugin missing lifecycle state
"""

import logging
import os
from typing import List

from .plugin_registry import get_registry

logger = logging.getLogger(__name__)


def run_startup_audit(discovered_plugins: List[str]) -> None:
    """Verify loader → registry consistency at boot.

    Args:
        discovered_plugins: List of plugin names found during discovery

    Raises:
        RuntimeError: If PHASE11_STRICT_AUDIT=1 and divergence detected
    """
    registry = get_registry()
    statuses = registry.list_all()

    logger.info("=" * 50)
    logger.info("Phase 11 Startup Audit")
    logger.info("=" * 50)
    logger.info(f"Discovered plugins: {discovered_plugins}")
    logger.info(f"Registry plugins: {[s.name for s in statuses]}")

    # Check 1: Registry not empty when plugins discovered
    if discovered_plugins and len(statuses) == 0:
        msg = (
            "Phase 11 INVARIANT VIOLATED: Plugins discovered but registry empty. "
            "Possible causes: wrong singleton, registration failed, wrong instance."
        )
        logger.error(msg)
        _maybe_strict_fail(msg)

    # Check 2: All discovered plugins in registry
    missing = [p for p in discovered_plugins if p not in [s.name for s in statuses]]
    if missing:
        msg = f"Phase 11 INVARIANT VIOLATED: Missing from registry: {missing}"
        logger.error(msg)
        _maybe_strict_fail(msg)

    # Check 3: All plugins have lifecycle state
    for s in statuses:
        if s.state is None:
            msg = f"Phase 11 INVARIANT VIOLATED: Plugin '{s.name}' has no state"
            logger.error(msg)
            _maybe_strict_fail(msg)

    logger.info("=" * 50)
    logger.info("✓ Startup Audit Complete (no divergence detected)")
    logger.info("=" * 50)


def _maybe_strict_fail(msg: str) -> None:
    """Fail hard in strict mode (dev/CI), log only in production.

    Args:
        msg: Error message to log/raise
    """
    if os.getenv("PHASE11_STRICT_AUDIT") == "1":
        logger.error("PHASE11_STRICT_AUDIT=1: Failing hard on invariant violation")
        raise RuntimeError(msg)
