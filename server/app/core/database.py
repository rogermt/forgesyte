"""DuckDB SQLAlchemy database configuration."""

import logging
import os
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.pool import QueuePool

logger = logging.getLogger(__name__)

Base: Any = declarative_base()

# Ensure data directory exists (for file-based DB)
data_dir = Path("data")
data_dir.mkdir(exist_ok=True)

# DB URL configurable via environment (tests use in-memory, prod uses file)
DATABASE_URL = os.getenv("FORGESYTE_DATABASE_URL", "duckdb:///data/foregsyte.duckdb")

# Issue #357: DB pool configuration
# pool_size=20, max_overflow=40, pool_timeout=60, pool_pre_ping=True
engine = create_engine(
    DATABASE_URL,
    future=True,
    poolclass=QueuePool,
    pool_size=20,
    max_overflow=40,
    pool_timeout=60,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)


def init_db():
    """Initialize database schema - run Alembic migrations.

    Uses Alembic to apply all pending migrations, ensuring the database
    schema is up to date. This handles both new installations and
    upgrades from previous versions.

    Issue #293: Previously used create_all() which doesn't run migrations
    on existing tables, causing missing column errors like ray_future_id.

    For test environments or when Alembic is not configured, falls back
    to create_all() which creates tables from model definitions.
    """
    # Import models to register them with Base
    from ..models.job import Job  # noqa: F401
    from ..models.job_tool import JobTool  # noqa: F401

    # Check if we should try Alembic migrations
    # Skip if running in test mode (tests use isolated databases)
    in_test_mode = os.getenv("FORGESYTE_DATABASE_URL", "").startswith(
        "duckdb:///:memory:"
    )

    if not in_test_mode:
        try:
            # Register DuckDB dialect with SQLAlchemy before Alembic operations
            # This fixes KeyError: 'duckdb' when Alembic tries to run migrations
            import duckdb_engine  # noqa: F401
            from alembic import command
            from alembic.config import Config
            from alembic.ddl import impl
            from alembic.ddl.postgresql import PostgresqlImpl

            # Register DuckDB implementation with Alembic
            # DuckDB is PostgreSQL-compatible, so we use PostgresqlImpl
            impl._impls["duckdb"] = PostgresqlImpl

            # Get alembic config using absolute path (Issue #297)
            # This file is at server/app/core/database.py, alembic.ini is at server/
            alembic_path = Path(__file__).parent.parent.parent / "alembic.ini"

            if not alembic_path.exists():
                logger.warning("alembic.ini not found, falling back to create_all()")
            else:
                alembic_cfg = Config(str(alembic_path))
                # Run all pending migrations
                logger.info("Running Alembic migrations...")
                command.upgrade(alembic_cfg, "head")
                logger.info("Database migrations completed successfully")
                return
        except Exception:
            # Log full traceback for debugging (Issue #300)
            logger.exception("Alembic migrations failed, falling back to create_all()")

    # Fallback: create all tables from model definitions
    # This is used for tests and when Alembic is not configured
    logger.info("Creating database tables from model definitions...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created successfully")


def get_db():
    """Dependency for FastAPI to inject database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_db_session() -> Generator[Any, None, None]:
    """Context manager for DB sessions with session tracking.

    Issue #357: Ensures every DB session is properly tracked and released.
    Uses track_session_start/end from db_utils for leak detection.
    """
    from ..workers.db_utils import track_session_end, track_session_start

    track_session_start()
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        track_session_end()
        db.close()
