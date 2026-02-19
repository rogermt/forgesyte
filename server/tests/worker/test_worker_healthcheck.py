"""Health check test for worker - ensures worker can import and startup."""


def test_worker_imports():
    """Verify worker module imports without errors."""
    from server.app.workers import video_worker

    assert hasattr(video_worker, "process_job")


def test_worker_has_job_repo():
    """Verify worker has job repository."""
    from server.app.workers import video_worker

    assert hasattr(video_worker, "job_repo")


def test_worker_has_pipeline_service():
    """Verify worker imports VideoFilePipelineService."""
    from server.app.workers import video_worker

    assert hasattr(video_worker, "VideoFilePipelineService")


def test_worker_loop_importable():
    """Verify worker_loop function exists (for startup script)."""
    from server.app.workers import video_worker

    assert hasattr(video_worker, "worker_loop")
