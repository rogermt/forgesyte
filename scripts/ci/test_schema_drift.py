"""TEST-CHANGE: CI guardrail - detect schema drift between governance spec and runtime.

Compares .ampcode governance spec against actual runtime schema.
Fails if drift detected (prevents accidental schema changes).
"""

import sys
from pathlib import Path


def normalize_schema(sql: str) -> str:
    """Normalize SQL for comparison (ignore whitespace, comments)."""
    lines = []
    for line in sql.split("\n"):
        # Remove leading/trailing whitespace
        line = line.strip()
        # Skip empty lines and comments
        if line and not line.startswith("--"):
            lines.append(line)
    return " ".join(lines).lower()


def test_schema_drift() -> bool:
    """
    Verify runtime schema matches governance spec.

    Returns:
        True if schemas match, False if drift detected.
    """
    # Paths - resolve from project root
    script_dir = Path(__file__).resolve()
    project_root = script_dir.parent.parent.parent
    
    governance_spec = (
        project_root
        / ".ampcode"
        / "04_PHASE_NOTES"
        / "Phase_8"
        / "PHASE_8_METRICS_SCHEMA.sql"
    )
    runtime_spec = (
        project_root
        / "server"
        / "app"
        / "observability"
        / "duckdb"
        / "schema.sql"
    )

    # Verify both files exist
    if not governance_spec.exists():
        print(f"ERROR: Governance spec not found: {governance_spec}")
        return False

    if not runtime_spec.exists():
        print(f"ERROR: Runtime spec not found: {runtime_spec}")
        return False

    # Read both
    governance_sql = governance_spec.read_text()
    runtime_sql = runtime_spec.read_text()

    # Normalize and compare
    governance_norm = normalize_schema(governance_sql)
    runtime_norm = normalize_schema(runtime_sql)

    if governance_norm == runtime_norm:
        print("✓ Schema drift check PASSED: governance spec matches runtime")
        return True
    else:
        print("✗ Schema drift check FAILED: governance spec does not match runtime")
        print(f"\nGovernance spec: {governance_spec}")
        print(f"Runtime spec: {runtime_spec}")
        print("\nThey must be identical. Update one to match the other.")
        return False


if __name__ == "__main__":
    success = test_schema_drift()
    sys.exit(0 if success else 1)
