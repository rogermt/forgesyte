"""Load DuckDB schema from SQL file.

Idempotent schema initialization for Phase 8 metrics database.
Safe for tests + startup.
"""

import duckdb
from pathlib import Path


def load_schema(db_path: str, schema_path: str) -> None:
    """
    Load schema from SQL file into DuckDB.

    Creates tables if they don't exist. Idempotent - safe to call multiple times.

    Args:
        db_path: Path to metrics.db file
        schema_path: Path to schema.sql file

    Raises:
        FileNotFoundError: If schema.sql doesn't exist
    """
    schema_file = Path(schema_path)
    if not schema_file.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")

    # Read schema
    schema_sql = schema_file.read_text()

    # Execute in DuckDB (CREATE TABLE IF NOT EXISTS is idempotent)
    conn = duckdb.connect(db_path)
    try:
        conn.execute(schema_sql)
    finally:
        conn.close()
