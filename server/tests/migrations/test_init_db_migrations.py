"""TDD tests for init_db migration handling (Issue #293).

These tests verify that the Job model has all expected columns,
which would fail if migrations were not applied to an existing database.

The actual migration issue (Issue #293) is that on production systems,
running init_db() with just create_all() doesn't apply new migrations
to existing tables. This is tested indirectly by verifying all columns
exist after table creation.

NOTE: v0.15.1 dropped tool/tool_list columns from jobs table.
Tools are now stored in job_tools table.
"""

from sqlalchemy import text


def test_jobs_table_has_all_expected_columns(test_engine):
    """Verify jobs table has all expected columns after init.

    This test would FAIL if a migration was missing from the model
    definition (Base.metadata.create_all uses the model, not migrations).

    The original Issue #293 occurred when:
    1. Old database had jobs table without ray_future_id
    2. New code added ray_future_id to Job model
    3. create_all() skipped existing tables, didn't add new column
    4. Query for ray_future_id raised 'column does not exist'

    With proper migration handling, all columns should exist.
    """
    # v0.15.1: tool and tool_list columns removed, stored in job_tools table
    # v0.15.x: summary added for pre-computed video summary (Discussion #354)
    expected_columns = [
        "job_id",
        "status",
        "plugin_id",
        "input_path",
        "output_path",
        "job_type",
        "error_message",
        "created_at",
        "updated_at",
        "progress",  # Added in migration 006
        "ray_future_id",  # Added in migration 007
        "summary",  # Added in migration 012 (Discussion #354)
    ]

    with test_engine.connect() as conn:
        result = conn.execute(
            text(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_name = 'jobs'"
            )
        )
        existing_columns = {row[0] for row in result.fetchall()}

    for col in expected_columns:
        assert col in existing_columns, (
            f"Column '{col}' missing from jobs table. "
            f"This indicates a migration issue (Issue #293). "
            f"Existing: {existing_columns}"
        )


def test_ray_future_id_query_succeeds(test_engine):
    """Verify querying ray_future_id does not raise.

    This captures the original error from Issue #293:
    'Binder Error: Table "jobs" does not have a column named "ray_future_id"'
    """
    # This query should NOT raise - column should exist
    with test_engine.connect() as conn:
        result = conn.execute(
            text("SELECT ray_future_id FROM jobs WHERE status = 'pending' LIMIT 1")
        )
        # Query succeeds even if no rows returned
        assert result.fetchone() is None  # Empty table, no rows


def test_jobs_table_column_count(test_engine):
    """Verify jobs table has expected number of columns."""
    with test_engine.connect() as conn:
        result = conn.execute(
            text(
                "SELECT COUNT(*) FROM information_schema.columns "
                "WHERE table_name = 'jobs'"
            )
        )
        count = result.fetchone()[0]

    # v0.15.x: Expected 12 columns (summary added in migration 012)
    # See test_jobs_table_has_all_expected_columns for list
    assert count == 12, (
        f"Expected 12 columns in jobs table, got {count}. "
        f"This may indicate missing migrations (Issue #293)."
    )


def test_job_model_matches_table_schema(test_engine):
    """Verify Job model definition matches actual table schema.

    This test catches the case where the model has a column
    but the migration wasn't created/applied.
    """
    from app.models.job import Job

    # Get columns from model
    model_columns = set()
    for col in Job.__table__.columns:
        model_columns.add(col.name)

    # Get columns from actual table
    with test_engine.connect() as conn:
        result = conn.execute(
            text(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_name = 'jobs'"
            )
        )
        table_columns = {row[0] for row in result.fetchall()}

    # Model should have at least as many columns as table
    # (table might have fewer if migrations not applied)
    missing_in_table = model_columns - table_columns
    assert not missing_in_table, (
        f"Model has columns missing from table: {missing_in_table}. "
        f"This indicates migrations were not applied (Issue #293)."
    )
