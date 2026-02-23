"""Add progress column to jobs table for v0.9.6 video progress tracking.

Adds integer progress column (0-100) to track video processing progress.
Column is nullable for backward compatibility with pre-v0.9.6 jobs.

Revision ID: 006
Revises: 005
Create Date: 2026-02-23 00:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

revision = "006"
down_revision = "005"
branch_labels = None
depends_on = None


def upgrade():
    """Add progress column as nullable for backward compatibility."""
    op.add_column(
        "jobs",
        sa.Column("progress", sa.Integer(), nullable=True),
    )

    # Create index for efficient progress lookups
    op.create_index("ix_jobs_progress", "jobs", ["progress"])


def downgrade():
    """Remove progress column."""
    op.drop_index("ix_jobs_progress", table_name="jobs")
    op.drop_column("jobs", "progress")
