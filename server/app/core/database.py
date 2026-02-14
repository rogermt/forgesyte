"""DuckDB SQLAlchemy database configuration."""

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

Base = declarative_base()

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


def get_db():
    """Dependency for FastAPI to inject database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
