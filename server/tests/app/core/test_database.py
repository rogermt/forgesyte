"""Tests for database.py - database configuration and session management."""

import os
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.orm import Session

from app.core.database import (
    Base,
    SessionLocal,
    engine,
    get_db,
    get_db_session,
    init_db,
)


@pytest.mark.unit
class TestInitDb:
    """Tests for init_db function."""

    @patch.dict(os.environ, {"FORGESYTE_DATABASE_URL": "duckdb:///:memory:"})
    def test_init_db_in_test_mode_uses_create_all(self) -> None:
        """Test that init_db uses create_all() in test mode (in-memory DB)."""
        with patch.object(Base.metadata, "create_all") as mock_create_all:
            init_db()
            mock_create_all.assert_called_once()

    @patch.dict(os.environ, {"FORGESYTE_DATABASE_URL": "duckdb:///data/test.duckdb"})
    def test_init_db_production_mode_attempts_alembic(self) -> None:
        """Test that init_db attempts Alembic migrations in production mode."""
        with patch("app.core.database.Path") as mock_path:
            # Mock alembic.ini not existing to trigger fallback
            mock_alembic_path = MagicMock()
            mock_alembic_path.exists.return_value = False
            mock_path.return_value.parent.parent.parent.__truediv__ = MagicMock(
                return_value=mock_alembic_path
            )

            with patch.object(Base.metadata, "create_all") as mock_create_all:
                init_db()
                # Should fall back to create_all since alembic.ini doesn't exist
                mock_create_all.assert_called_once()

    @patch.dict(os.environ, {"FORGESYTE_DATABASE_URL": "duckdb:///data/test.duckdb"})
    def test_init_db_fallback_on_alembic_exception(self) -> None:
        """Test that init_db falls back to create_all on Alembic errors."""
        with patch("app.core.database.Path") as mock_path:
            mock_alembic_path = MagicMock()
            mock_alembic_path.exists.return_value = True
            mock_path.return_value.parent.parent.parent.__truediv__ = MagicMock(
                return_value=mock_alembic_path
            )

            # Patch alembic.command.upgrade where it's imported
            with patch("alembic.command.upgrade") as mock_upgrade:
                # Make Alembic upgrade fail
                mock_upgrade.side_effect = Exception("Alembic failed")

                with patch.object(Base.metadata, "create_all") as mock_create_all:
                    init_db()
                    # Should fall back to create_all
                    mock_create_all.assert_called_once()


@pytest.mark.unit
class TestGetDb:
    """Tests for get_db dependency."""

    def test_get_db_yields_session(self) -> None:
        """Test that get_db yields a database session."""
        db_gen = get_db()
        db = next(db_gen)
        assert isinstance(db, Session)

        # Cleanup
        try:
            next(db_gen)
        except StopIteration:
            pass

    def test_get_db_closes_session_after_use(self) -> None:
        """Test that get_db closes the session after use."""
        mock_session = MagicMock(spec=Session)
        mock_session.is_active = True

        with patch("app.core.database.SessionLocal") as mock_session_local:
            mock_session_local.return_value = mock_session

            db_gen = get_db()
            _ = next(db_gen)

            # Exhaust generator (simulates FastAPI dependency cleanup)
            with pytest.raises(StopIteration):
                next(db_gen)

        # Verify close was called on the session
        mock_session.close.assert_called_once()


@pytest.mark.unit
class TestGetDbSession:
    """Tests for get_db_session context manager."""

    def test_get_db_session_yields_session(self) -> None:
        """Test that get_db_session yields a database session."""
        with patch("app.workers.db_utils.track_session_start") as mock_start:
            with patch("app.workers.db_utils.track_session_end") as mock_end:
                with get_db_session() as db:
                    assert isinstance(db, Session)
                    mock_start.assert_called_once()

                mock_end.assert_called_once()

    def test_get_db_session_commits_on_success(self) -> None:
        """Test that get_db_session commits on successful exit."""
        mock_session = MagicMock(spec=Session)

        with patch("app.workers.db_utils.track_session_start"):
            with patch("app.workers.db_utils.track_session_end"):
                with patch("app.core.database.SessionLocal") as mock_session_local:
                    mock_session_local.return_value = mock_session

                    with get_db_session():
                        pass  # No exception

        # Verify commit was called on the session
        mock_session.commit.assert_called_once()

    def test_get_db_session_rollback_on_exception(self) -> None:
        """Test that get_db_session rolls back on exception."""
        mock_session = MagicMock(spec=Session)

        with patch("app.workers.db_utils.track_session_start"):
            with patch("app.workers.db_utils.track_session_end"):
                with patch("app.core.database.SessionLocal") as mock_session_local:
                    mock_session_local.return_value = mock_session

                    with pytest.raises(ValueError):
                        with get_db_session():
                            raise ValueError("Test error")

        # Verify rollback was called on the session
        mock_session.rollback.assert_called_once()

    def test_get_db_session_calls_tracking_functions(self) -> None:
        """Test that get_db_session calls session tracking functions."""
        with patch("app.workers.db_utils.track_session_start") as mock_start:
            with patch("app.workers.db_utils.track_session_end") as mock_end:
                with get_db_session():
                    pass

                mock_start.assert_called_once()
                mock_end.assert_called_once()

    def test_get_db_session_tracking_on_exception(self) -> None:
        """Test that session tracking is called even on exception."""
        with patch("app.workers.db_utils.track_session_start") as mock_start:
            with patch("app.workers.db_utils.track_session_end") as mock_end:
                with pytest.raises(RuntimeError):
                    with get_db_session():
                        raise RuntimeError("Test error")

                # Both tracking functions should still be called
                mock_start.assert_called_once()
                mock_end.assert_called_once()


@pytest.mark.unit
class TestDatabaseEngine:
    """Tests for database engine configuration."""

    def test_engine_has_pool_configuration(self) -> None:
        """Test that engine has pool configuration."""

        assert engine.pool is not None

    def test_base_is_declarative_base(self) -> None:
        """Test that Base is a declarative base."""
        assert hasattr(Base, "metadata")
        assert hasattr(Base, "registry")

    def test_session_local_is_configured(self) -> None:
        """Test that SessionLocal is configured correctly."""
        assert SessionLocal.kw["autoflush"] is False
        assert SessionLocal.kw["autocommit"] is False
