"""Tests for QueueService implementations."""

import pytest

from app.services.queue.memory_queue import InMemoryQueueService


@pytest.mark.unit
def test_enqueue_dequeue():
    """Test basic enqueue and dequeue."""
    queue = InMemoryQueueService()
    job_id = "test-job-123"

    queue.enqueue(job_id)
    result = queue.dequeue()

    assert result == job_id


@pytest.mark.unit
def test_dequeue_empty_returns_none():
    """Test dequeue on empty queue returns None."""
    queue = InMemoryQueueService()

    result = queue.dequeue()

    assert result is None


@pytest.mark.unit
def test_fifo_ordering():
    """Test that queue maintains FIFO ordering."""
    queue = InMemoryQueueService()
    job_ids = ["job-1", "job-2", "job-3"]

    for job_id in job_ids:
        queue.enqueue(job_id)

    results = [queue.dequeue() for _ in range(len(job_ids))]

    assert results == job_ids


@pytest.mark.unit
def test_size():
    """Test queue size tracking."""
    queue = InMemoryQueueService()

    assert queue.size() == 0

    queue.enqueue("job-1")
    assert queue.size() == 1

    queue.enqueue("job-2")
    assert queue.size() == 2

    queue.dequeue()
    assert queue.size() == 1

    queue.dequeue()
    assert queue.size() == 0


@pytest.mark.unit
def test_multiple_dequeues_after_empty():
    """Test multiple dequeues after queue is empty."""
    queue = InMemoryQueueService()
    queue.enqueue("job-1")
    queue.dequeue()

    # Multiple dequeues should return None
    assert queue.dequeue() is None
    assert queue.dequeue() is None
    assert queue.size() == 0


@pytest.mark.unit
def test_uuid_string_payload():
    """Test that UUID strings work as payloads."""
    import uuid

    queue = InMemoryQueueService()
    job_id = str(uuid.uuid4())

    queue.enqueue(job_id)
    result = queue.dequeue()

    assert result == job_id
    assert len(result) == 36  # UUID4 string length
