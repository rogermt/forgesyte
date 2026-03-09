"""DuckDB SQLAlchemy database configuration."""

import logging
import os
from pathlib import Path
from typing import Any

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

logger = logging.getLogger(__name__)

Base: Any = declarative_base()

# Ensure data directory exists (for file-based DB)
data_dir = Path("data")
data_dir.mkdir(exist_ok=True)

# DB URL configurable via environment (tests use in-memory, prod uses file)
DATABASE_URL = os.getenv("FORGESYTE_DATABASE_URL", "duckdb:///data/foregsyte.duckdb")

engine = create_engine(
    DATABASE_URL,
    future=True,
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

    # Check if we should try Alembic migrations
    # Skip if running in test mode (tests use isolated databases)
    in_test_mode = os.getenv("FORGESYTE_DATABASE_URL", "").startswith(
        "duckdb:///:memory:"
    )

    if not in_test_mode:
        try:
            from alembic import command
            from alembic.config import Config

            # Get alembic config (relative to server directory)
            alembic_cfg = Config("alembic.ini")

            # Run all pending migrations
            logger.info("Running Alembic migrations...")
            command.upgrade(alembic_cfg, "head")
            logger.info("Database migrations completed successfully")
            return
        except FileNotFoundError:
            logger.warning("alembic.ini not found, falling back to create_all()")
        except Exception as e:
            logger.warning(
                f"Alembic migrations failed: {e}, falling back to create_all()"
            )

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
