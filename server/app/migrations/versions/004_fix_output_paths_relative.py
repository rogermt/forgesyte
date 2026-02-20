"""Fix output paths to be relative.

Converts absolute or semi-absolute paths stored in job.output_path
to relative paths only.

Revision ID: 004
Revises: 003
Create Date: 2026-02-20 00:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

revision = "004"
down_revision = "003"
branch_labels = None
depends_on = None


def upgrade():
    """Convert absolute output paths to relative paths."""
    conn = op.get_bind()

    # Fetch all jobs with output_path
    result = conn.execute(sa.text("SELECT job_id, output_path FROM jobs"))
    rows = result.fetchall()

    updated_count = 0

    for job_id, output_path in rows:
        if not output_path:
            continue

        # Check if path is absolute or contains video_jobs (semi-absolute)
        needs_update = False
        relative_path = output_path

        if output_path.startswith("/"):
            # Absolute path - extract relative part after "video_jobs/"
            if "video_jobs/" in output_path:
                relative_path = output_path.split("video_jobs/")[-1]
                needs_update = True
        elif "video_jobs/" in output_path:
            # Semi-absolute path contains the full prefix - extract relative part
            relative_path = output_path.split("video_jobs/")[-1]
            needs_update = True

        if needs_update:
            conn.execute(
                sa.text(
                    "UPDATE jobs SET output_path = :rel WHERE job_id = :id"
                ),
                {"rel": relative_path, "id": job_id},
            )
            updated_count += 1

    if updated_count > 0:
        op.execute("UPDATE jobs SET updated_at = datetime('now') WHERE output_path IS NOT NULL")


def downgrade():
    """No-op: cannot restore absolute paths."""
    pass
