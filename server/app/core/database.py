"""DuckDB SQLAlchemy database configuration."""

from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

Base = declarative_base()

# Ensure data directory exists
data_dir = Path("data")
data_dir.mkdir(exist_ok=True)

# File-based DuckDB for application runtime
engine = create_engine(
    "duckdb:///data/foregsyte.duckdb",
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
