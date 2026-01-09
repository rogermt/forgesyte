"""Background task management and job processing."""

import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, Optional, Any, Callable
from datetime import datetime
import logging
import uuid
import time

from .models import JobStatus, JobResponse
from .plugin_loader import PluginManager

logger = logging.getLogger(__name__)


class JobStore:
    """In-memory job storage (replace with Redis for production)."""
    
    def __init__(self, max_jobs: int = 1000):
        self._jobs: Dict[str, dict] = {}
        self._max_jobs = max_jobs
        self._lock = asyncio.Lock()
    
    async def create(self, job_id: str, plugin: str) -> dict:
        """Create a new job entry."""
        async with self._lock:
            # Cleanup old jobs if at capacity
            if len(self._jobs) >= self._max_jobs:
                await self._cleanup_old_jobs()
            
            job = {
                "job_id": job_id,
                "status": JobStatus.QUEUED,
                "result": None,
                "error": None,
                "created_at": datetime.utcnow(),
                "completed_at": None,
                "plugin": plugin,
                "progress": 0.0
            }
            self._jobs[job_id] = job
            return job
    
    async def update(self, job_id: str, **kwargs) -> Optional[dict]:
        """Update a job's status."""
        async with self._lock:
            if job_id in self._jobs:
                self._jobs[job_id].update(kwargs)
                return self._jobs[job_id]
            return None
    
    async def get(self, job_id: str) -> Optional[dict]:
        """Get a job by ID."""
        return self._jobs.get(job_id)
    
    async def list_jobs(
        self,
        status: JobStatus = None,
        plugin: str = None,
        limit: int = 50
    ) -> list:
        """List jobs with optional filtering."""
        jobs = list(self._jobs.values())
        
        if status:
            jobs = [j for j in jobs if j["status"] == status]
        if plugin:
            jobs = [j for j in jobs if j["plugin"] == plugin]
        
        # Sort by created_at descending
        jobs.sort(key=lambda j: j["created_at"], reverse=True)
        return jobs[:limit]
    
    async def _cleanup_old_jobs(self):
        """Remove oldest completed jobs."""
        completed = [
            (k, v) for k, v in self._jobs.items()
            if v["status"] in (JobStatus.DONE, JobStatus.ERROR)
        ]
        completed.sort(key=lambda x: x[1]["created_at"])
        
        # Remove oldest 20%
        remove_count = max(1, len(completed) // 5)
        for job_id, _ in completed[:remove_count]:
            del self._jobs[job_id]


class TaskProcessor:
    """Handles async task processing."""
    
    def __init__(
        self,
        plugin_manager: PluginManager,
        job_store: JobStore,
        max_workers: int = 4
    ):
        self.plugin_manager = plugin_manager
        self.job_store = job_store
        self._executor = ThreadPoolExecutor(max_workers=max_workers)
        self._callbacks: Dict[str, Callable] = {}
    
    async def submit_job(
        self,
        image_bytes: bytes,
        plugin_name: str,
        options: dict = None,
        callback: Callable = None
    ) -> str:
        """Submit a new analysis job."""
        job_id = str(uuid.uuid4())
        
        await self.job_store.create(job_id, plugin_name)
        
        if callback:
            self._callbacks[job_id] = callback
        
        # Run in thread pool
        asyncio.create_task(
            self._process_job(job_id, image_bytes, plugin_name, options or {})
        )
        
        return job_id
    
    async def _process_job(
        self,
        job_id: str,
        image_bytes: bytes,
        plugin_name: str,
        options: dict
    ):
        """Process a job asynchronously."""
        await self.job_store.update(job_id, status=JobStatus.RUNNING, progress=0.1)
        
        plugin = self.plugin_manager.get(plugin_name)
        if not plugin:
            await self.job_store.update(
                job_id,
                status=JobStatus.ERROR,
                error=f"Plugin '{plugin_name}' not found"
            )
            await self._notify_callback(job_id)
            return
        
        try:
            start_time = time.time()
            
            # Run analysis
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                self._executor,
                plugin.analyze,
                image_bytes,
                options
            )
            
            processing_time = (time.time() - start_time) * 1000
            
            await self.job_store.update(
                job_id,
                status=JobStatus.DONE,
                result={
                    **result,
                    "processing_time_ms": processing_time
                },
                completed_at=datetime.utcnow(),
                progress=1.0
            )
            
        except Exception as e:
            logger.error(f"Job {job_id} failed: {e}")
            await self.job_store.update(
                job_id,
                status=JobStatus.ERROR,
                error=str(e),
                completed_at=datetime.utcnow()
            )
        
        await self._notify_callback(job_id)
    
    async def _notify_callback(self, job_id: str):
        """Notify callback if registered."""
        if job_id in self._callbacks:
            callback = self._callbacks.pop(job_id)
            job = await self.job_store.get(job_id)
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(job)
                else:
                    callback(job)
            except Exception as e:
                logger.error(f"Callback failed for job {job_id}: {e}")
    
    async def get_job(self, job_id: str) -> Optional[dict]:
        """Get job status."""
        return await self.job_store.get(job_id)
    
    async def cancel_job(self, job_id: str) -> bool:
        """Cancel a running job (best effort)."""
        job = await self.job_store.get(job_id)
        if job and job["status"] == JobStatus.QUEUED:
            await self.job_store.update(
                job_id,
                status=JobStatus.ERROR,
                error="Cancelled by user"
            )
            return True
        return False


# Global instances
job_store = JobStore()
task_processor: Optional[TaskProcessor] = None


def init_task_processor(plugin_manager: PluginManager):
    """Initialize the global task processor."""
    global task_processor
    task_processor = TaskProcessor(plugin_manager, job_store)
    return task_processor