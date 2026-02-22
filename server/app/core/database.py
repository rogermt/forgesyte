"""DuckDB SQLAlchemy database configuration."""

import os
from pathlib import Path
from typing import Any

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

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
    """Initialize database schema - create tables if they don't exist."""
    try:
        # Import models to register them with Base
        from ..models.job import Job  # noqa: F401

        # Create all tables defined in models
        Base.metadata.create_all(bind=engine)
    except Exception as e:
        raise RuntimeError(f"Could not initialize database schema: {e}") from e


def get_db():
    """Dependency for FastAPI to inject database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
