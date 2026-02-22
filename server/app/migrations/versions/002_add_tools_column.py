"""add_tools_column

Revision ID: 002
Revises: 001
Create Date: 2026-02-20 00:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade():
    """Add tools column to jobs table."""
    op.add_column(
        "jobs",
        sa.Column("tools", sa.String(), nullable=True),
    )


def downgrade():
    """Remove tools column from jobs table."""
    op.drop_column("jobs", "tools")
