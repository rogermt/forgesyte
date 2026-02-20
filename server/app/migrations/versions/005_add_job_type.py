"""Add job_type column to Job model for v0.9.2 unified job system.

Adds job_type column to distinguish between image and video jobs.
Backfills existing jobs as "video" since only video jobs existed before v0.9.2.

Revision ID: 005
Revises: 004
Create Date: 2026-02-20 00:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

revision = "005"
down_revision = "004"
branch_labels = None
depends_on = None


def upgrade():
    """Add job_type column and backfill existing jobs."""
    # Add job_type column as nullable first
    op.add_column("jobs", sa.Column("job_type", sa.String(), nullable=True))

    # Backfill existing jobs as "video" (only video jobs existed before v0.9.2)
    op.execute("UPDATE jobs SET job_type='video' WHERE job_type IS NULL")

    # Make column non-nullable
    op.alter_column("jobs", "job_type", nullable=False)


def downgrade():
    """Remove job_type column."""
    op.drop_column("jobs", "job_type")
