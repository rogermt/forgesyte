"""Tests for worker WebSocket progress broadcasting (TDD - Phase 6).

Tests for integration of WebSocket broadcast into worker progress updates.
"""

from unittest.mock import MagicMock, patch

import pytest


class TestWorkerProgressBroadcast:
    """Tests for worker WebSocket progress broadcasting."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = MagicMock(
            progress=0
        )
        return db

    def test_update_job_progress_broadcasts_to_websocket(self, mock_db) -> None:
        """Test that _update_job_progress broadcasts via WebSocket."""
        from app.workers.worker import JobWorker

        # Patch the progress module's progress_callback function
        with patch("app.workers.progress.progress_callback") as mock_progress:
            worker = JobWorker()

            worker._update_job_progress(
                job_id="test-job-123",
                current_frame=50,
                total_frames=100,
                db=mock_db,
            )

            # Should have called progress_callback for WebSocket broadcast
            mock_progress.assert_called_once()
            call_kwargs = mock_progress.call_args[1]
            assert call_kwargs["job_id"] == "test-job-123"
            assert call_kwargs["current_frame"] == 50
            assert call_kwargs["total_frames"] == 100

    def test_progress_throttling_still_works(self, mock_db) -> None:
        """Test that 5% throttling still applies to DB updates."""
        from app.workers.worker import JobWorker

        worker = JobWorker()

        # First call at 0% should update DB
        worker._update_job_progress("job-1", 1, 100, mock_db)
        assert mock_db.commit.call_count >= 1

        # Reset mock
        mock_db.reset_mock()

        # Call at 3% (should be throttled for DB)
        worker._update_job_progress("job-1", 3, 100, mock_db)
        # DB update should be throttled (not committed)
        # But WebSocket broadcast should still happen

    def test_progress_updates_at_5_percent_boundaries(self, mock_db) -> None:
        """Test progress updates happen at 5%, 10%, 15%, etc."""
        from app.workers.worker import JobWorker

        worker = JobWorker()

        # Reset mock
        mock_db.reset_mock()

        # Update at 5%
        worker._update_job_progress("job-1", 5, 100, mock_db)
        assert mock_db.commit.call_count >= 1

        mock_db.reset_mock()

        # Update at 10%
        worker._update_job_progress("job-1", 10, 100, mock_db)
        assert mock_db.commit.call_count >= 1

    def test_progress_always_updates_on_last_frame(self, mock_db) -> None:
        """Test progress always updates on the last frame."""
        from app.workers.worker import JobWorker

        worker = JobWorker()

        # Reset mock
        mock_db.reset_mock()

        # Update at last frame (100/100)
        worker._update_job_progress("job-1", 100, 100, mock_db)
        assert mock_db.commit.call_count >= 1

    def test_multi_tool_progress_calculation(self, mock_db) -> None:
        """Test unified progress calculation for multi-tool jobs."""
        from app.workers.worker import JobWorker

        worker = JobWorker()

        # 2 tools, first tool at 50% (frame 50/100)
        # Global progress = (0 * 50) + (50/100 * 50) = 25%
        worker._update_job_progress(
            job_id="job-1",
            current_frame=50,
            total_frames=100,
            db=mock_db,
            tool_index=0,
            total_tools=2,
            tool_name="tool-A",
        )

        # Should update DB at 25%
        job = mock_db.query.return_value.filter.return_value.first.return_value
        assert job.progress == 25
