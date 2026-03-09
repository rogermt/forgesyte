"""Add tool_list column for multi-tool job support.

Revision ID: 008
Revises: 007
Create Date: 2026-03-09 00:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

revision = "008"
down_revision = "007"
branch_labels = None
depends_on = None


def _column_exists(table_name: str, column_name: str) -> bool:
    """Check if a column exists in a table using DuckDB's PRAGMA.

    Uses DuckDB-native PRAGMA instead of SQLAlchemy Inspector
    which requires pg_catalog (not available in DuckDB).
    """
    conn = op.get_bind()
    result = conn.execute(sa.text(f"PRAGMA table_info('{table_name}')"))
    columns = [row[1] for row in result.fetchall()]
    return column_name in columns


def upgrade() -> None:
    """Add tool_list column for multi-tool jobs (v0.9.4)."""
    # Guard against duplicate column (DBs bootstrapped via create_all())
    if not _column_exists("jobs", "tool_list"):
        op.add_column(
            "jobs",
            sa.Column("tool_list", sa.String(), nullable=True),
        )


def downgrade() -> None:
    """Remove tool_list column."""
    # Guard against missing column
    if _column_exists("jobs", "tool_list"):
        op.drop_column("jobs", "tool_list")
