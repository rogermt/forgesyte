TDD Implementation Plan for v0.9.2: Unified Job Orchestrator Architecture
Based on the OVERVIEW.md decisions, here's the complete implementation plan:

Architecture Decisions (from OVERVIEW.md)
Question	Decision
1. Tool structure mismatch	Use manifest.json only
2. Worker pipeline	Replace VideoPipelineService with plugin.run_tool() via plugin_service
3. Storage instantiation	Keep direct instantiation, unify BASE_DIR
4. Job ID type	Keep UUID
5. Canonicalize inputs	In get_plugin_manifest()
6. JobStatus	Keep pending, no queued
7. Tool execution	Use plugin_service.run_plugin_tool()
8. Image validation	Validate PNG/JPEG magic bytes
9. Storage paths	Unified data/jobs/{image
10. Worker startup	Keep thread in 0.9.2, separate process in 1.0.0
Commit Structure (15 Commits)
Phase 1: Database Schema Changes (Commits 1-3)
Commit 1: Add job_type column to Job model
Create migration 005_add_job_type.py
Add job_type column (enum: "image", "video")
Update Job model to include job_type field
Write tests for migration
File: app/models/job.py

Python
class Job(Base):
    # ... existing fields ...
    job_type = Column(String, nullable=False)  # "image" or "video"
Migration: versions/005_add_job_type.py

Python
revision = "005_add_job_type"
down_revision = "004_fix_output_paths_relative"

def upgrade():
    op.add_column("jobs", sa.Column("job_type", sa.String(), nullable=True))
    op.execute("UPDATE jobs SET job_type='video' WHERE job_type IS NULL")
    op.alter_column("jobs", "job_type", nullable=False)

def downgrade():
    op.drop_column("jobs", "job_type")
Commit 2: Canonicalize plugin manifest inputs
Update PluginManagementService.get_plugin_manifest() to canonicalize inputs
Support both input_types and inputs for backward compatibility
Ensure all tools have inputs: List[str]
File: app/services/plugin_management_service.py

Python
def get_plugin_manifest(self, plugin_id: str) -> Optional[Dict[str, Any]]:
    # ... existing code ...
    
    # Canonicalize inputs
    for tool in manifest.get("tools", []):
        if "inputs" not in tool or not tool["inputs"]:
            if "input_types" in tool and tool["input_types"]:
                tool["inputs"] = tool["input_types"]
            else:
                tool["inputs"] = []
    
    return manifest
Commit 3: Enhance worker to handle both image and video jobs
Update JobWorker._execute_pipeline() to check job_type
Add image processing branch using plugin_service.run_plugin_tool()
Keep existing video processing branch
Add tool validation based on inputs from manifest
Update storage paths to use unified data/jobs structure
File: app/workers/worker.py

Python
def _execute_pipeline(self, job: Job, db: Session) -> bool:
    # Get plugin manifest
    manifest = self.plugin_service.get_plugin_manifest(job.plugin_id)
    tool_def = next((t for t in manifest.get("tools", []) if t.get("id") == job.tool), None)
    
    if not tool_def:
        job.status = JobStatus.failed
        job.error_message = f"Unknown tool: {job.tool}"
        db.commit()
        return False
    
    # Validate tool supports job_type
    if job.job_type == "video":
        if not any(i in tool_def.get("inputs", []) for i in ("video", "video_path")):
            job.status = JobStatus.failed
            job.error_message = "Tool does not support video input"
            db.commit()
            return False
    elif job.job_type == "image":
        if not any(i in tool_def.get("inputs", []) for i in ("image_bytes", "image_base64")):
            job.status = JobStatus.failed
            job.error_message = "Tool does not support image input"
            db.commit()
            return False
    
    try:
        # Branch by job_type
        if job.job_type == "video":
            video_path = self.storage.load_file(job.input_path)
            args = {"video_path": str(video_path)}
        elif job.job_type == "image":
            image_path = self.storage.load_file(job.input_path)
            with open(image_path, "rb") as f:
                image_bytes = f.read()
            args = {"image_bytes": image_bytes}
        else:
            job.status = JobStatus.failed
            job.error_message = f"Unknown job_type: {job.job_type}"
            db.commit()
            return False
        
        # Execute tool via plugin_service (includes sandbox and error handling)
        result = self.plugin_service.run_plugin_tool(job.plugin_id, job.tool, args)
        
        # Save results
        output_rel = f"{job.job_type}/output/{job.job_id}.json"
        self.storage.save_file(
            BytesIO(json.dumps({"results": result}).encode("utf-8")),
            output_rel,
        )
        
        job.output_path = output_rel
        job.status = JobStatus.completed
        job.error_message = None
        db.commit()
        return True
        
    except Exception as exc:
        job.status = JobStatus.failed
        job.error_message = str(exc)
        db.commit()
        return False
Phase 2: New Image Submit Endpoint (Commits 4-6)
Commit 4: Create /v1/image/submit endpoint
New endpoint in app/api_routes/routes/image_submit.py
Accept file, plugin_id, tool parameters
Validate plugin manifest for image support
Create Job with job_type="image"
Save image to storage with magic byte validation
Return job_id
File: app/api_routes/routes/image_submit.py

Python
from fastapi import APIRouter, Depends, File, UploadFile, HTTPException
from sqlalchemy.orm import Session
from io import BytesIO
import uuid

from app.core.database import get_db
from app.models.job import Job, JobStatus
from app.services.storage.local_storage import LocalStorageService
from app.services.plugin_management_service import PluginManagementService

router = APIRouter()
storage = LocalStorageService(base_dir="data/jobs")
plugin_service = PluginManagementService(plugin_dirs=["forgesyte-plugins"])


def validate_image_magic_bytes(data: bytes):
    """Validate PNG or JPEG magic bytes."""
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return
    if data.startswith(b"\xFF\xD8\xFF"):
        return
    raise HTTPException(400, "Invalid image file (expected PNG or JPEG)")


@router.post("/v1/image/submit")
async def submit_image_job(
    plugin_id: str,
    tool: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """Submit an image file for processing."""
    # Validate plugin + tool
    manifest = plugin_service.get_plugin_manifest(plugin_id)
    tool_def = next((t for t in manifest.get("tools", []) if t.get("id") == tool), None)
    if not tool_def:
        raise HTTPException(400, "Unknown tool")
    
    if not any(i in tool_def.get("inputs", []) for i in ("image_bytes", "image_base64")):
        raise HTTPException(400, "Tool does not support image input")
    
    # Validate and read file
    contents = await file.read()
    validate_image_magic_bytes(contents)
    
    # Save input image (relative path)
    job_id = str(uuid.uuid4())
    input_rel_path = f"image/input/{job_id}_{file.filename}"
    storage.save_file(BytesIO(contents), input_rel_path)
    
    # Create job
    job = Job(
        job_id=job_id,
        status=JobStatus.pending,
        plugin_id=plugin_id,
        tool=tool,
        input_path=input_rel_path,
        job_type="image",
    )
    db.add(job)
    db.commit()
    
    return {"job_id": job_id, "status": job.status}
Commit 5: Update LocalStorageService for unified paths
Change BASE_DIR from data/video_jobs to data/jobs
Ensure all paths are relative
File: app/services/storage/local_storage.py

Python
# Change from:
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent / "data" / "video_jobs"

# To:
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent / "data" / "jobs"
Commit 6: Update video submit endpoint for unified storage
Update video_submit.py to use video/input/ and video/output/ paths
Ensure consistency with image paths
File: app/api_routes/routes/video_submit.py

Python
# Change input path from:
input_path = f"{job_id}.mp4"

# To:
input_path = f"video/input/{job_id}.mp4"
Phase 3: Unified Job Endpoint (Commits 7-9)
Commit 7: Create unified /v1/jobs/{id} endpoint
New endpoint that returns status and results for both image and video
Replace /v1/video/status/{id} and /v1/video/results/{id}
Return consistent response format
File: app/api_routes/routes/jobs.py

Python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import json

from app.core.database import get_db
from app.models.job import Job, JobStatus
from app.schemas.job import JobResultsResponse
from app.services.storage.local_storage import LocalStorageService

router = APIRouter()
storage = LocalStorageService(base_dir="data/jobs")


@router.get("/v1/jobs/{job_id}", response_model=JobResultsResponse)
async def get_job(job_id: str, db: Session = Depends(get_db)):
    """Get job status and results (unified for image and video)."""
    job = db.query(Job).filter(Job.job_id == job_id).first()
    if not job:
        raise HTTPException(404, "Job not found")
    
    if job.status != JobStatus.completed:
        return JobResultsResponse(
            job_id=job.job_id,
            results=None,
            created_at=job.created_at,
            updated_at=job.updated_at,
        )
    
    try:
        file_path = storage.load_file(job.output_path)
        with open(file_path, "r") as f:
            results = json.load(f)
    except FileNotFoundError:
        raise HTTPException(404, "Results file not found")
    
    return JobResultsResponse(
        job_id=job.job_id,
        results=results,
        created_at=job.created_at,
        updated_at=job.updated_at,
    )
Commit 8: Register unified jobs router in main.py
Add jobs router to FastAPI app
File: app/main.py

Python
from .api_routes.routes.jobs import router as jobs_router

# In create_app():
app.include_router(jobs_router, prefix=settings.api_prefix)
Commit 9: Deprecate old video endpoints
Mark /v1/video/status/{id} and /v1/video/results/{id} as deprecated
Add deprecation warnings
File: app/api_routes/routes/job_status.py

Python
@router.get("/v1/video/status/{job_id}", response_model=JobStatusResponse, deprecated=True)
async def get_job_status(
    job_id: UUID, db: Session = Depends(get_db)
) -> JobStatusResponse:
    """DEPRECATED: Use /v1/jobs/{job_id} instead."""
    # ... existing implementation ...
File: app/api_routes/routes/job_results.py

Python
@router.get("/v1/video/results/{job_id}", response_model=JobResultsResponse, deprecated=True)
async def get_job_results(
    job_id: UUID, db: Session = Depends(get_db)
) -> JobResultsResponse:
    """DEPRECATED: Use /v1/jobs/{job_id} instead."""
    # ... existing implementation ...
Phase 4: Cleanup and Migration (Commits 10-12)
Commit 10: Remove TaskProcessor
Remove app/tasks.py (TaskProcessor class)
Remove init_task_processor() from main.py
Remove all imports
File: app/main.py

Python
# Remove:
from .tasks import init_task_processor, job_store

# In lifespan():
processor = init_task_processor(plugin_manager)
Commit 11: Remove JobManagementService
Remove app/services/job_management_service.py
Remove from main.py and all imports
Update app/services/__init__.py
File: app/main.py

Python
# Remove:
from .services import JobManagementService

# In lifespan():
app.state.job_service = JobManagementService(job_store, processor)
Commit 12: Deprecate legacy /jobs/ endpoints
Mark old job endpoints in api.py as deprecated
Add TODO comments for v1.0.0 removal
File: app/api.py

Python
# Add deprecation to all /jobs/ endpoints:
@router.get("/jobs/{job_id}", response_model=JobResponse, deprecated=True)
async def get_job_status_legacy(
    # ...
):
    """DEPRECATED: Use /v1/jobs/{job_id} instead. TODO: Remove in v1.0.0"""
    # ...
Phase 5: Frontend Updates (Commits 13-14)
Commit 13: Update frontend to use unified endpoint
Update apiClient.getJob() to use /v1/jobs/{id}
Update VideoUpload component to use unified endpoint
Update JobStatus component to handle unified response
File: web-ui/src/api/client.ts

TypeScript
// Replace:
async getVideoJobStatus(jobId: string): Promise<{...}>
async getVideoJobResults(jobId: string): Promise<{...}>

// With:
async getJob(jobId: string): Promise<{
  job_id: string;
  results: any;
  created_at: string;
  updated_at: string;
}> {
  const result = await this.fetch(`/jobs/${jobId}`);
  return result as {...};
}
File: web-ui/src/components/VideoUpload.tsx

TypeScript
// Replace polling logic:
const status = await apiClient.getVideoJobStatus(jobId);
const results = await apiClient.getVideoJobResults(jobId);

// With:
const job = await apiClient.getJob(jobId);
Commit 14: Add tool filtering to frontend
Filter tools by input_type (image vs video)
Show only image tools in image upload mode
Show only video tools in video upload mode
File: web-ui/src/components/ToolSelector.tsx

TypeScript
// Filter tools by input type
const filteredTools = tools.filter(tool =>
  mode === "video"
    ? tool.inputs.includes("video") || tool.inputs.includes("video_path")
    : tool.inputs.includes("image_bytes") || tool.inputs.includes("image_base64")
);
Phase 6: Testing and Validation (Commit 15)
Commit 15: Add E2E test for unified job system
Test OCR image job via /v1/image/submit
Test YOLO video job via /v1/video/submit
Test both use /v1/jobs/{id} for status and results
Verify JSON output format
File: tests/test_e2e_unified_jobs.py

Python
def test_e2e_ocr_image_and_yolo_video(client, tmp_path, storage, plugin_service):
    # 1) Submit OCR image job
    img_path = tmp_path / "test.png"
    img_path.write_bytes(b"\x89PNG\r\n\x1a\n....")
    
    with img_path.open("rb") as f:
        resp = client.post(
            "/v1/image/submit?plugin_id=ocr&tool=extract_text",
            files={"file": ("test.png", f, "image/png")},
        )
    assert resp.status_code == 200
    image_job_id = resp.json()["job_id"]
    
    # 2) Submit YOLO video job
    video_path = tmp_path / "test.mp4"
    video_path.write_bytes(b"ftyp....")
    
    with video_path.open("rb") as f:
        resp = client.post(
            "/v1/video/submit?plugin_id=yolo&tool=detect_objects",
            files={"file": ("test.mp4", f, "video/mp4")},
        )
    assert resp.status_code == 200
    video_job_id = resp.json()["job_id"]
    
    # 3) Run worker to process both jobs
    run_worker_once(storage, plugin_service)
    
    # 4) Fetch results via unified /v1/jobs/{id}
    resp = client.get(f"/v1/jobs/{image_job_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["job_id"] == image_job_id
    assert data["results"] is not None
    
    resp = client.get(f"/v1/jobs/{video_job_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["job_id"] == video_job_id
    assert data["results"] is not None
Summary
This TDD plan implements v0.9.2 with 15 commits:

Key Changes:

Add job_type to Job model
Canonicalize plugin manifest inputs
Enhance worker to handle both image and video
Create /v1/image/submit endpoint
Unify storage paths to data/jobs/{image|video}/...
Create unified /v1/jobs/{id} endpoint
Remove legacy systems (TaskProcessor, JobManagementService)
Deprecate old endpoints
Update frontend to use new unified system
User Stories Satisfied:

✓ Upload image, select plugin tool, get JSON response (via /v1/image/submit + /v1/jobs/{id})
✓ Upload video, select plugin tool, get JSON response (via /v1/video/submit + /v1/jobs/{id})
All decisions are based on the OVERVIEW.md answers. Ready to implement!
