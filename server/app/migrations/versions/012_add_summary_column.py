"""Add summary column for pre-computed video summary.

Revision ID: 012
Revises: 011
Create Date: 2026-03-20

Discussion #354: Pre-compute summary during worker finalization
to avoid loading full artifacts on /v1/jobs hot path.

The summary column stores JSON-encoded summary data:
{
    "frame_count": 100,
    "detection_count": 500,
    "classes": ["player", "ball"]
}
"""

import sqlalchemy as sa
from alembic import op

revision = "012"
down_revision = "011"
branch_labels = None
depends_on = None


def _column_exists(table_name: str, column_name: str) -> bool:
    """Check if a column exists in a table using DuckDB's PRAGMA."""
    conn = op.get_bind()
    result = conn.execute(sa.text(f"PRAGMA table_info('{table_name}')"))
    columns = [row[1] for row in result.fetchall()]
    return column_name in columns


def upgrade() -> None:
    """Add summary column to jobs table."""
    # Add column if it doesn't exist (idempotent)
    if not _column_exists("jobs", "summary"):
        op.add_column(
            "jobs",
            sa.Column("summary", sa.String(), nullable=True),
        )


def downgrade() -> None:
    """Remove summary column from jobs table."""
    if _column_exists("jobs", "summary"):
        op.drop_column("jobs", "summary")
