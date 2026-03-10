#!/usr/bin/env python3
"""Manual schema fix for DuckDB databases.

DuckDB does not support Alembic migrations - must be done manually.
This script ensures all expected columns exist in the jobs table.

Usage:
    python scripts/fix_schema.py [db_path]

    If db_path is not provided, defaults to data/foregsyte.duckdb
"""

import os
import sys

import duckdb

DEFAULT_DB_PATH = "data/foregsyte.duckdb"

# All expected columns for jobs table (migrations 001-008)
EXPECTED_COLUMNS = {
    "job_id": "UUID",
    "status": "VARCHAR",
    "plugin_id": "VARCHAR",
    "tool": "VARCHAR",
    "tool_list": "VARCHAR",  # Migration 002 (v0.9.4)
    "input_path": "VARCHAR",
    "output_path": "VARCHAR",
    "job_type": "VARCHAR",
    "error_message": "VARCHAR",
    "created_at": "TIMESTAMP",
    "updated_at": "TIMESTAMP",
    "progress": "INTEGER",  # Migration 006 (v0.9.6)
    "ray_future_id": "VARCHAR",  # Migration 007 (v0.12.0)
}

# Columns that were added via migrations (may be missing in old DBs)
MIGRATION_COLUMNS = {
    "tool_list": "VARCHAR",
    "progress": "INTEGER",
    "ray_future_id": "VARCHAR",
}


def ensure_columns_exist(db_path: str):
    """Add missing columns to jobs table."""
    if not os.path.exists(db_path):
        print(f"Database file not found: {db_path}")
        return False

    print(f"Checking database: {db_path}")
    con = duckdb.connect(db_path)

    # Check existing columns
    cols = con.execute("PRAGMA table_info('jobs')").fetchall()
    col_names = {c[1] for c in cols}
    print(f"Existing columns: {sorted(col_names)}")

    added = []
    for col_name, col_type in MIGRATION_COLUMNS.items():
        if col_name not in col_names:
            print(f"Adding column '{col_name}' ({col_type})...")
            con.execute(f"ALTER TABLE jobs ADD COLUMN {col_name} {col_type};")
            added.append(col_name)

    if added:
        print(f"Added columns: {added}")
    else:
        print("All migration columns already exist. No action taken.")

    con.close()
    return True


if __name__ == "__main__":
    db_path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_DB_PATH
    ensure_columns_exist(db_path)
