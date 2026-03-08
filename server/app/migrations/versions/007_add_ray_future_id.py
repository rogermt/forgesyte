"""Add ray_future_id column for Ray job tracking persistence.

Adds string column to store Ray future/task reference for recovery
after worker restart. Part of Issue #270 - Ray job mapping persistence.

Revision ID: 007
Revises: 006
Create Date: 2026-03-08 00:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

revision = "007"
down_revision = "006"
branch_labels = None
depends_on = None


def upgrade():
    """Add ray_future_id column as nullable."""
    op.add_column(
        "jobs",
        sa.Column("ray_future_id", sa.String(), nullable=True),
    )


def downgrade():
    """Remove ray_future_id column."""
    op.drop_column("jobs", "ray_future_id")
