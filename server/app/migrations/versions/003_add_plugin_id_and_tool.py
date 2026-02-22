"""add_plugin_id_and_tool

Revision ID: 003
Revises: 002
Create Date: 2026-02-20 00:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

revision = "003"
down_revision = "002"
branch_labels = None
depends_on = None


def upgrade():
    """Add plugin_id and tool columns, drop pipeline_id and tools."""
    # Add new columns as nullable first
    op.add_column("jobs", sa.Column("plugin_id", sa.String(), nullable=True))
    op.add_column("jobs", sa.Column("tool", sa.String(), nullable=True))

    # Delete old jobs (no backward compat needed for v0.9.1)
    op.execute("DELETE FROM jobs")

    # Drop old columns
    with op.batch_alter_table("jobs") as batch_op:
        batch_op.drop_column("pipeline_id")
        batch_op.drop_column("tools")

    # Make new columns NOT NULL
    op.alter_column("jobs", "plugin_id", nullable=False)
    op.alter_column("jobs", "tool", nullable=False)


def downgrade():
    """Revert to pipeline_id and tools columns."""
    # Add old columns back
    with op.batch_alter_table("jobs") as batch_op:
        batch_op.add_column(sa.Column("pipeline_id", sa.String(), nullable=False))
        batch_op.add_column(sa.Column("tools", sa.String(), nullable=True))

    # Drop new columns
    op.drop_column("jobs", "plugin_id")
    op.drop_column("jobs", "tool")
