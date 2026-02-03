"""Phase 8 — Test DuckDB metrics schema integrity.

This test verifies that the metrics database schema exists and contains
all required tables as specified in Phase 8.

Reference: .ampcode/04_PHASE_NOTES/Phase_8/PHASE_8_METRICS_SCHEMA_TESTS.md
"""

import pytest
import duckdb
from pathlib import Path


@pytest.fixture
def metrics_db():
    """Create an in-memory DuckDB for testing.
    
    This fixture:
    - Creates a temporary in-memory DuckDB instance
    - Loads the Phase 8 metrics schema
    - Cleans up after test
    """
    # Connect to in-memory database
    conn = duckdb.connect(':memory:')
    
    # Load schema from app directory
    schema_path = Path(__file__).parent.parent.parent / 'app' / 'observability' / 'duckdb' / 'schema.sql'
    
    with open(schema_path, 'r') as f:
        schema = f.read()
    
    # Execute schema SQL
    for statement in schema.split(';'):
        statement = statement.strip()
        if statement:
            conn.execute(statement)
    
    yield conn
    
    # Cleanup
    conn.close()


class TestMetricsSchema:
    """Test suite for Phase 8 metrics schema."""
    
    def test_job_metrics_table_exists(self, metrics_db):
        """Verify job_metrics table exists."""
        result = metrics_db.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_name = 'job_metrics'
        """).fetchall()
        
        assert len(result) == 1, "job_metrics table does not exist"
    
    def test_plugin_metrics_table_exists(self, metrics_db):
        """Verify plugin_metrics table exists."""
        result = metrics_db.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_name = 'plugin_metrics'
        """).fetchall()
        
        assert len(result) == 1, "plugin_metrics table does not exist"
    
    def test_overlay_metrics_table_exists(self, metrics_db):
        """Verify overlay_metrics table exists."""
        result = metrics_db.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_name = 'overlay_metrics'
        """).fetchall()
        
        assert len(result) == 1, "overlay_metrics table does not exist"
    
    def test_device_usage_table_exists(self, metrics_db):
        """Verify device_usage table exists."""
        result = metrics_db.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_name = 'device_usage'
        """).fetchall()
        
        assert len(result) == 1, "device_usage table does not exist"
    
    def test_all_required_tables_exist(self, metrics_db):
        """Verify all Phase 8 required tables exist."""
        required_tables = {
            'job_metrics',
            'plugin_metrics',
            'overlay_metrics',
            'device_usage'
        }
        
        result = metrics_db.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_type = 'BASE TABLE'
        """).fetchall()
        
        existing_tables = {row[0] for row in result}
        
        assert required_tables.issubset(existing_tables), \
            f"Missing tables: {required_tables - existing_tables}"
