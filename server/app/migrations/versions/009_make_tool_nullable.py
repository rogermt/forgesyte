"""Make tool column nullable for multi-tool jobs.

Revision ID: 009
Revises: 008
Create Date: 2026-03-13 00:00:00.000000

Issue: Multi-tool jobs set tool=None and use tool_list instead.
The tool column was set to NOT NULL in migration 003, but v0.9.4
requires it to be nullable for multi-tool jobs.
"""

from alembic import op

revision = "009"
down_revision = "008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Make tool column nullable for multi-tool jobs."""
    op.alter_column("jobs", "tool", nullable=True)


def downgrade() -> None:
    """Revert tool column to NOT NULL."""
    # Warning: This will fail if there are existing jobs with tool=None
    op.alter_column("jobs", "tool", nullable=False)
