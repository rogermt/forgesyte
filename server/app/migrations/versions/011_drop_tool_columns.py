"""Drop tool and tool_list columns from jobs table.

Revision ID: 011
Revises: 010
Create Date: 2026-03-14

These columns are replaced by the job_tools table (migration 010).
- tool: Single tool ID (replaced by job_tools table)
- tool_list: JSON-encoded list of tools (replaced by job_tools table)

v0.15.1: No going back to the old design.
"""

import sqlalchemy as sa
from alembic import op

revision = "011"
down_revision = "010"
branch_labels = None
depends_on = None


def _column_exists(table_name: str, column_name: str) -> bool:
    """Check if a column exists in a table using DuckDB's PRAGMA."""
    conn = op.get_bind()
    result = conn.execute(sa.text(f"PRAGMA table_info('{table_name}')"))
    columns = [row[1] for row in result.fetchall()]
    return column_name in columns


def upgrade() -> None:
    """Drop tool and tool_list columns from jobs table."""
    # Drop columns if they exist (idempotent)
    if _column_exists("jobs", "tool"):
        op.drop_column("jobs", "tool")

    if _column_exists("jobs", "tool_list"):
        op.drop_column("jobs", "tool_list")


def downgrade() -> None:
    """Re-add tool and tool_list columns (not recommended)."""
    # Add tool column back as nullable (data lost)
    op.add_column("jobs", sa.Column("tool", sa.String(), nullable=True))

    # Add tool_list column back as nullable
    op.add_column("jobs", sa.Column("tool_list", sa.String(), nullable=True))
