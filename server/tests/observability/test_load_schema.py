"""TEST-CHANGE: Tests for load_schema.py - DuckDB schema initialization."""

import tempfile
import pytest
import duckdb
from pathlib import Path

from app.observability.duckdb.load_schema import load_schema


def test_load_schema_creates_tables():
    """Verify load_schema creates all 4 required tables."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        schema_path = Path(__file__).parent.parent.parent / "app" / "observability" / "duckdb" / "schema.sql"
        
        # Load schema
        load_schema(str(db_path), str(schema_path))
        
        # Verify tables exist
        conn = duckdb.connect(str(db_path))
        tables = conn.execute(
            "SELECT table_name FROM information_schema.tables WHERE table_schema='main'"
        ).fetchall()
        table_names = [t[0] for t in tables]
        
        assert "job_metrics" in table_names
        assert "plugin_metrics" in table_names
        assert "overlay_metrics" in table_names
        assert "device_usage" in table_names
        conn.close()


def test_load_schema_idempotent():
    """Verify load_schema is idempotent - safe to call multiple times."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        schema_path = Path(__file__).parent.parent.parent / "app" / "observability" / "duckdb" / "schema.sql"
        
        # Load schema twice
        load_schema(str(db_path), str(schema_path))
        load_schema(str(db_path), str(schema_path))  # Should not error
        
        # Verify tables still exist
        conn = duckdb.connect(str(db_path))
        tables = conn.execute(
            "SELECT table_name FROM information_schema.tables WHERE table_schema='main'"
        ).fetchall()
        assert len(tables) == 4
        conn.close()


def test_load_schema_preserves_existing_data():
    """Verify load_schema doesn't drop data on re-run (UPSERT safety)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        schema_path = Path(__file__).parent.parent.parent / "app" / "observability" / "duckdb" / "schema.sql"
        
        # First load
        load_schema(str(db_path), str(schema_path))
        
        # Insert test data
        conn = duckdb.connect(str(db_path))
        import uuid
        conn.execute(
            """
            INSERT INTO job_metrics (id, job_id, plugin, device, status, created_at)
            VALUES (?, 'job-1', 'ocr', 'cpu', 'queued', CURRENT_TIMESTAMP)
            """,
            [uuid.uuid4()]
        )
        initial_count = conn.execute("SELECT COUNT(*) FROM job_metrics").fetchone()[0]
        conn.close()
        
        # Second load (should not drop table)
        load_schema(str(db_path), str(schema_path))
        
        # Verify data preserved
        conn = duckdb.connect(str(db_path))
        final_count = conn.execute("SELECT COUNT(*) FROM job_metrics").fetchone()[0]
        assert final_count == initial_count
        conn.close()
