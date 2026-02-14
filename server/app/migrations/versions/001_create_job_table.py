"""create_job_table

Revision ID: 001
Revises:
Create Date: 2026-02-14 20:00:00.000000

"""

from alembic import op
import sqlalchemy as sa
from duckdb_engine import UUID


revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    """Create jobs table."""
    op.create_table(
        "jobs",
        sa.Column("job_id", UUID, primary_key=True, nullable=False),
        sa.Column(
            "status",
            sa.Enum("pending", "running", "completed", "failed", name="job_status_enum"),
            nullable=False,
        ),
        sa.Column("pipeline_id", sa.String(), nullable=False),
        sa.Column("input_path", sa.String(), nullable=False),
        sa.Column("output_path", sa.String(), nullable=True),
        sa.Column("error_message", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )


def downgrade():
    """Drop jobs table."""
    op.drop_table("jobs")
    op.execute("DROP TYPE job_status_enum")
