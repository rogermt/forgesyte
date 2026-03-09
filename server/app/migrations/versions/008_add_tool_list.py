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


def upgrade():
    """Add tool_list column for multi-tool jobs (v0.9.4)."""
    op.add_column(
        "jobs",
        sa.Column("tool_list", sa.String(), nullable=True),
    )


def downgrade():
    """Remove tool_list column."""
    op.drop_column("jobs", "tool_list")
