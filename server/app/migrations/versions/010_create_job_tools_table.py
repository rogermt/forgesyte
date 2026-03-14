"""Create job_tools table for normalized tool storage.

Revision ID: 010
Revises: 009 (which was reverted)
Create Date: 2026-03-14

This migration:
1. Creates job_tools table with id, job_id, tool_id columns
2. Backfills existing data from jobs.tool (single-tool jobs)
3. Backfills existing data from jobs.tool_list (multi-tool jobs)
"""

import json
import uuid

import sqlalchemy as sa
from alembic import op

revision = "010"
down_revision = "008"
branch_labels = None
depends_on = None


def _table_exists(table_name: str) -> bool:
    """Check if a table exists using DuckDB's information_schema."""
    conn = op.get_bind()
    result = conn.execute(
        sa.text(
            f"SELECT table_name FROM information_schema.tables "
            f"WHERE table_name = '{table_name}'"
        )
    )
    return result.fetchone() is not None


def _column_exists(table_name: str, column_name: str) -> bool:
    """Check if a column exists in a table using DuckDB's PRAGMA."""
    conn = op.get_bind()
    result = conn.execute(sa.text(f"PRAGMA table_info('{table_name}')"))
    columns = [row[1] for row in result.fetchall()]
    return column_name in columns


def upgrade() -> None:
    """Create job_tools table and backfill existing data."""
    # Skip if table already exists
    if _table_exists("job_tools"):
        return

    # Create job_tools table
    op.create_table(
        "job_tools",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "job_id", sa.String(36), sa.ForeignKey("jobs.job_id"), nullable=False
        ),
        sa.Column("tool_id", sa.String(), nullable=False),
        sa.Column("tool_order", sa.Integer(), nullable=False, server_default="0"),
    )

    # Backfill from single-tool jobs (jobs.tool IS NOT NULL AND jobs.tool_list IS NULL)
    conn = op.get_bind()

    # Backfill single-tool jobs
    single_tool_jobs = conn.execute(
        sa.text(
            "SELECT job_id, tool FROM jobs WHERE tool IS NOT NULL AND (tool_list IS NULL OR tool_list = 'null')"
        )
    ).fetchall()

    for job_id, tool in single_tool_jobs:
        conn.execute(
            sa.text(
                "INSERT INTO job_tools (id, job_id, tool_id, tool_order) VALUES (:id, :job_id, :tool_id, :tool_order)"
            ),
            {
                "id": str(uuid.uuid4()),
                "job_id": str(job_id),
                "tool_id": tool,
                "tool_order": 0,
            },
        )

    # Backfill from multi-tool jobs (jobs.tool_list IS NOT NULL)
    if _column_exists("jobs", "tool_list"):
        multi_tool_jobs = conn.execute(
            sa.text(
                "SELECT job_id, tool_list FROM jobs WHERE tool_list IS NOT NULL AND tool_list != 'null'"
            )
        ).fetchall()

        for job_id, tool_list_json in multi_tool_jobs:
            try:
                tools = json.loads(tool_list_json)
                for order, tool in enumerate(tools):
                    conn.execute(
                        sa.text(
                            "INSERT INTO job_tools (id, job_id, tool_id, tool_order) VALUES (:id, :job_id, :tool_id, :tool_order)"
                        ),
                        {
                            "id": str(uuid.uuid4()),
                            "job_id": str(job_id),
                            "tool_id": tool,
                            "tool_order": order,
                        },
                    )
            except (json.JSONDecodeError, TypeError):
                # Skip malformed JSON
                pass


def downgrade() -> None:
    """Drop job_tools table."""
    if _table_exists("job_tools"):
        op.drop_table("job_tools")
