"""TDD tests for v0.12.0 ray_future_id column migration (Issue #270)."""

from sqlalchemy import text


def test_ray_future_id_column_exists(test_engine):
    """Verify ray_future_id column exists after migration."""
    with test_engine.connect() as conn:
        result = conn.execute(
            text(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_name = 'jobs' AND column_name = 'ray_future_id'"
            )
        )
        row = result.fetchone()
        assert row is not None, "ray_future_id column missing from jobs table"


def test_ray_future_id_column_is_nullable(test_engine):
    """Verify ray_future_id column is nullable for backward compatibility."""
    with test_engine.connect() as conn:
        result = conn.execute(
            text(
                "SELECT is_nullable FROM information_schema.columns "
                "WHERE table_name = 'jobs' AND column_name = 'ray_future_id'"
            )
        )
        row = result.fetchone()
        assert row is not None, "ray_future_id column not found"
        assert row[0] == "YES", "ray_future_id column should be nullable"


def test_ray_future_id_column_is_string(test_engine):
    """Verify ray_future_id column is String type."""
    with test_engine.connect() as conn:
        result = conn.execute(
            text(
                "SELECT data_type FROM information_schema.columns "
                "WHERE table_name = 'jobs' AND column_name = 'ray_future_id'"
            )
        )
        row = result.fetchone()
        assert row is not None, "ray_future_id column not found"
        # DuckDB reports VARCHAR for String columns
        assert (
            "varchar" in row[0].lower() or "string" in row[0].lower()
        ), f"ray_future_id should be String/VARCHAR, got {row[0]}"
