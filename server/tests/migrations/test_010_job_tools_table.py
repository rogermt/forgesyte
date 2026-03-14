"""TDD tests for job_tools table migration.

Tests verify:
1. job_tools table is created with correct schema
2. JobTool model can be used to associate tools with jobs

NOTE: v0.15.1 dropped tool/tool_list columns from jobs table.
These tests now verify job_tools table exists and can be used directly.
"""

from sqlalchemy import text


def test_job_tools_table_exists(test_engine):
    """RED: Verify job_tools table exists after migration."""
    with test_engine.connect() as conn:
        result = conn.execute(
            text(
                "SELECT table_name FROM information_schema.tables "
                "WHERE table_name = 'job_tools'"
            )
        )
        row = result.fetchone()
        assert row is not None, "job_tools table missing"


def test_job_tools_has_id_column(test_engine):
    """RED: Verify job_tools has id column (UUID primary key)."""
    with test_engine.connect() as conn:
        result = conn.execute(
            text(
                "SELECT column_name, is_nullable FROM information_schema.columns "
                "WHERE table_name = 'job_tools' AND column_name = 'id'"
            )
        )
        row = result.fetchone()
        assert row is not None, "id column missing from job_tools"


def test_job_tools_has_job_id_column(test_engine):
    """RED: Verify job_tools has job_id column (foreign key to jobs)."""
    with test_engine.connect() as conn:
        result = conn.execute(
            text(
                "SELECT column_name, is_nullable FROM information_schema.columns "
                "WHERE table_name = 'job_tools' AND column_name = 'job_id'"
            )
        )
        row = result.fetchone()
        assert row is not None, "job_id column missing from job_tools"
        assert row[1] == "NO", "job_id should be NOT NULL"


def test_job_tools_has_tool_id_column(test_engine):
    """RED: Verify job_tools has tool_id column (TEXT NOT NULL)."""
    with test_engine.connect() as conn:
        result = conn.execute(
            text(
                "SELECT column_name, is_nullable, data_type FROM information_schema.columns "
                "WHERE table_name = 'job_tools' AND column_name = 'tool_id'"
            )
        )
        row = result.fetchone()
        assert row is not None, "tool_id column missing from job_tools"
        assert row[1] == "NO", "tool_id should be NOT NULL"


def test_job_tools_single_tool(test_engine):
    """Verify job_tools can store single tool for a job."""
    from sqlalchemy.orm import sessionmaker

    from app.models.job import Job, JobStatus
    from app.models.job_tool import JobTool

    Session = sessionmaker(bind=test_engine)
    session = Session()

    # Create a job with a single tool
    job = Job(
        plugin_id="test-plugin",
        input_path="test/input.jpg",
        job_type="image",
        status=JobStatus.pending,
    )
    session.add(job)
    session.flush()

    # Add tool to job_tools table (v0.15.1: replaced tool column)
    job_tool = JobTool(
        job_id=job.job_id,
        tool_id="single_tool",
        tool_order=0,
    )
    session.add(job_tool)
    session.commit()

    # Query job_tools for this job's tool
    job_id = str(job.job_id)
    with test_engine.connect() as conn:
        result = conn.execute(
            text("SELECT tool_id FROM job_tools WHERE job_id = :job_id"),
            {"job_id": job_id},
        )
        rows = result.fetchall()

        assert len(rows) == 1
        assert rows[0][0] == "single_tool"

    session.close()


def test_job_tools_multi_tool(test_engine):
    """Verify job_tools can store multiple tools for a job."""
    from sqlalchemy.orm import sessionmaker

    from app.models.job import Job, JobStatus
    from app.models.job_tool import JobTool

    Session = sessionmaker(bind=test_engine)
    session = Session()

    # Create a multi-tool job
    tools = ["tool_a", "tool_b", "tool_c"]
    job = Job(
        plugin_id="test-plugin",
        input_path="test/input.jpg",
        job_type="image_multi",
        status=JobStatus.pending,
    )
    session.add(job)
    session.flush()

    # Add tools to job_tools table (v0.15.1: replaced tool_list column)
    for idx, tool_id in enumerate(tools):
        job_tool = JobTool(
            job_id=job.job_id,
            tool_id=tool_id,
            tool_order=idx,
        )
        session.add(job_tool)
    session.commit()

    job_id = str(job.job_id)

    # Query job_tools for this job's tools
    with test_engine.connect() as conn:
        result = conn.execute(
            text("SELECT tool_id FROM job_tools WHERE job_id = :job_id"),
            {"job_id": job_id},
        )
        rows = result.fetchall()

        assert len(rows) == 3
        tool_ids = [r[0] for r in rows]
        assert set(tool_ids) == set(tools)

    session.close()
