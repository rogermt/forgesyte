# Phase 16 Worker Lifecycle

**Date**: 2026-02-13
**Phase**: 16 - Asynchronous Job Queue + Persistent Job State + Worker Process

---

## Overview

The worker process is a long-running daemon that processes video jobs asynchronously. It pulls jobs from the queue, processes them using Phase 15's VideoFilePipelineService, and stores results in the database.

---

## Worker Startup

### Initialization

```python
def main():
    # Initialize database connection
    db = DatabaseConnection()
    
    # Initialize queue connection
    queue = JobQueue()
    
    # Initialize pipeline service
    dag_service = DagPipelineService(registry, plugin_manager)
    video_service = VideoFilePipelineService(dag_service)
    
    # Start worker loop
    worker = Worker(db, queue, video_service)
    worker.run()
```

### Dependencies

- **Database**: Job metadata storage
- **Queue**: Job_id references
- **Pipeline Service**: Phase 15 VideoFilePipelineService
- **Plugin Manager**: Plugin registry

---

## Worker Loop

### Main Loop

```python
def run(self):
    while True:
        try:
            # Pull job from queue
            job_id = self.queue.dequeue()
            if not job_id:
                time.sleep(1)
                continue
            
            # Process job
            self.process_job(job_id)
            
        except Exception as e:
            logger.error(f"Worker error: {e}")
            time.sleep(5)
```

### Process Job

```python
def process_job(self, job_id: str):
    # Load job metadata
    job = self.db.get_job(job_id)
    if not job:
        logger.error(f"Job not found: {job_id}")
        return
    
    # Update status to running
    self.db.update_status(job_id, "running")
    
    try:
        # Download MP4 from object store
        mp4_path = self.object_store.download(job.input_path)
        
        # Process video
        results = self.video_service.run_on_file(
            mp4_path=mp4_path,
            pipeline_id=job.pipeline_id,
            frame_stride=job.frame_stride,
            max_frames=job.max_frames
        )
        
        # Store results in database
        self.db.store_results(job_id, results)
        
        # Update status to completed
        self.db.update_status(job_id, "completed")
        
    except Exception as e:
        # Update status to failed
        self.db.update_status(job_id, "failed", str(e))
```

---

## State Transitions

### Job Lifecycle

```
pending → running → completed
    ↓
  failed
```

### Transition Triggers

**pending → running**:
- Worker pulls job from queue
- Worker calls `db.update_status(job_id, "running")`

**running → completed**:
- Worker successfully processes job
- Worker calls `db.update_status(job_id, "completed")`

**running → failed**:
- Worker encounters exception
- Worker calls `db.update_status(job_id, "failed", error_message)`

**pending → failed**:
- Not directly triggered
- Can happen if queue repeatedly fails to deliver job

---

## Error Handling

### Transient Errors

```python
def process_job(self, job_id: str):
    retry_count = 0
    max_retries = 3
    
    while retry_count < max_retries:
        try:
            # Try to process job
            results = self.video_service.run_on_file(...)
            self.db.store_results(job_id, results)
            self.db.update_status(job_id, "completed")
            return
            
        except TransientError as e:
            retry_count += 1
            logger.warning(f"Transient error (attempt {retry_count}/{max_retries}): {e}")
            time.sleep(2 ** retry_count)
    
    # Mark as failed after max retries
    self.db.update_status(job_id, "failed", f"Max retries exceeded: {e}")
```

### Permanent Errors

```python
def process_job(self, job_id: str):
    try:
        # Process job
        results = self.video_service.run_on_file(...)
        self.db.store_results(job_id, results)
        self.db.update_status(job_id, "completed")
        
    except PermanentError as e:
        # Mark as failed immediately
        self.db.update_status(job_id, "failed", str(e))
```

### Worker Crash Recovery

If worker crashes:
- Job stays in `running` status
- Next worker that picks up job_id can recover
- Worker should check if job is already being processed
- Worker should implement idempotency

---

## Idempotency

### Check Job Status Before Processing

```python
def process_job(self, job_id: str):
    # Load job metadata
    job = self.db.get_job(job_id)
    
    # Check if job is already being processed
    if job.status == "running":
        # Check if worker is still alive
        if self.is_worker_alive(job.worker_id):
            logger.info(f"Job {job_id} already being processed by worker {job.worker_id}")
            return
    
    # Update status to running
    self.db.update_status(job_id, "running")
    self.db.set_worker_id(job_id, self.worker_id)
    
    # Process job...
```

---

## Logging

### Structured Logging

```python
logger.info(f"Processing job {job_id}")
logger.info(f"Job {job_id} status: {status}")
logger.error(f"Job {job_id} failed: {error_message}")
```

### Log Levels

- **INFO**: Normal operation (job started, job completed)
- **WARNING**: Transient errors, retries
- **ERROR**: Permanent errors, failures

---

## Resource Cleanup

### Connection Management

```python
def shutdown(self):
    # Close database connection
    self.db.close()
    
    # Close queue connection
    self.queue.close()
    
    # Cancel pending operations
    logger.info("Worker shutting down")
```

### Signal Handling

```python
import signal

def main():
    worker = Worker(db, queue, video_service)
    
    # Handle shutdown signals
    def signal_handler(signum, frame):
        logger.info(f"Received signal {signum}, shutting down...")
        worker.shutdown()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    worker.run()
```

---

## Performance Considerations

### Queue Polling Interval

```python
POLL_INTERVAL = 1  # seconds
```

**Trade-off**:
- Short interval = faster job pickup but higher CPU usage
- Long interval = slower job pickup but lower CPU usage
- 1 second is a good default

### Job Processing Time

Job processing time depends on:
- Video length
- Frame count
- Pipeline complexity
- Hardware performance

**No timeout** in Phase 16 (future phase)

### Database Connection Pooling

```python
# Use connection pool for better performance
pool = ConnectionPool(minsize=1, maxsize=10)
```

---

## Monitoring

### Worker Health

```python
def health_check(self):
    return {
        "worker_id": self.worker_id,
        "status": "running",
        "jobs_processed": self.jobs_processed,
        "jobs_failed": self.jobs_failed,
        "uptime_seconds": time.time() - self.start_time
    }
```

### Job Metrics

```python
def get_job_metrics(self, job_id: str):
    job = self.db.get_job(job_id)
    return {
        "job_id": job_id,
        "status": job.status,
        "processing_time_seconds": job.updated_at - job.created_at,
        "frame_count": len(job.results),
        "error_message": job.error_message
    }
```

---

## See Also

- `PHASE_16_OVERVIEW.md` - Feature overview
- `PHASE_16_ARCHITECTURE.md` - System architecture
- `PHASE_16_SCOPE.md` - What's in/out of scope
- `PHASE_16_DEFINITION_OF_DONE.md` - Completion criteria
- `PHASE_16_ENDPOINTS.md` - API specification
- `PHASE_16_TEST_STRATEGY.md` - Testing procedures
- `PHASE_16_GOVERNANCE_RULES.md` - Governance rules