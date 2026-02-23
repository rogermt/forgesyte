"""TDD tests for v0.9.6 progress column migration."""

from sqlalchemy import text


def test_progress_column_exists(test_engine):
    """RED: Verify progress column will exist after migration."""
    # DuckDB-compatible: query information_schema directly
    with test_engine.connect() as conn:
        result = conn.execute(
            text(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_name = 'jobs' AND column_name = 'progress'"
            )
        )
        row = result.fetchone()
        assert row is not None, "progress column missing from jobs table"


def test_progress_column_is_nullable(test_engine):
    """RED: Verify progress column is nullable for backward compatibility."""
    # DuckDB-compatible: query information_schema directly
    with test_engine.connect() as conn:
        result = conn.execute(
            text(
                "SELECT is_nullable FROM information_schema.columns "
                "WHERE table_name = 'jobs' AND column_name = 'progress'"
            )
        )
        row = result.fetchone()
        assert row is not None, "progress column not found"
        assert row[0] == "YES", "progress column should be nullable"


def test_progress_column_is_integer(test_engine):
    """RED: Verify progress column is Integer type."""
    # DuckDB-compatible: query information_schema directly
    with test_engine.connect() as conn:
        result = conn.execute(
            text(
                "SELECT data_type FROM information_schema.columns "
                "WHERE table_name = 'jobs' AND column_name = 'progress'"
            )
        )
        row = result.fetchone()
        assert row is not None, "progress column not found"
        assert "integer" in row[0].lower(), f"progress should be Integer, got {row[0]}"
