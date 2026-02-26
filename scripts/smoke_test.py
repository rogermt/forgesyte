#!/usr/bin/env python3
"""Phase 16 Smoke Test for Job-Based Pipeline.

Tests the full lifecycle of job processing:
1. Submit a job (POST /v1/video/submit)
2. Check job status (GET /v1/video/status/{job_id})
3. Retrieve results (GET /v1/video/results/{job_id})

Exit Codes:
- 0: All tests passed
- 1: Test failed
"""

import asyncio
import os
import sys
from pathlib import Path
from tempfile import NamedTemporaryFile

import httpx

# Test configuration
BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")
JOB_PROCESSING_SMOKE_TEST = os.getenv("JOB_PROCESSING_SMOKE_TEST", "0") == "1"

# Test fixture: a simple video file (1 second, minimal)
TEST_VIDEO_DATA = (
    b"\x00\x00\x00\x18ftypmp42\x00\x00\x00\x00mp42isom\x00\x00\x00\x08wide"
    b"\x00\x00\x00\x6cmdat\x00\x00\x00\x64test video data for phase 16 smoke test"
)


async def test_job_submission() -> str | None:
    """Test job submission endpoint.

    Returns job_id on success, None on failure.
    """
    async with httpx.AsyncClient(timeout=30) as client:
        # Create a temporary video file
        with NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
            tmp.write(TEST_VIDEO_DATA)
            tmp_path = tmp.name

        try:
            # Submit job
            with open(tmp_path, "rb") as f:
                response = await client.post(
                    f"{BASE_URL}/v1/video/submit",
                    files={"file": ("test.mp4", f, "video/mp4")},
                    params={
                        "plugin_id": "yolo-tracker",
                        "tool": "player_detection",
                    },
                    follow_redirects=True,
                )

            print(f"[SUBMIT] Status: {response.status_code}")

            if response.status_code not in (200, 201):
                print(f"[SUBMIT] ERROR: Expected 200/201, got {response.status_code}")
                print(f"[SUBMIT] Response: {response.text}")
                return None

            data = response.json()
            job_id = data.get("job_id")

            if not job_id:
                print(f"[SUBMIT] ERROR: No job_id in response: {data}")
                return None

            print(f"[SUBMIT] SUCCESS: job_id={job_id}")
            return job_id

        finally:
            # Clean up temp file
            Path(tmp_path).unlink(missing_ok=True)


async def test_job_status(job_id: str) -> bool:
    """Test job status endpoint.

    Returns True if status is valid.
    """
    async with httpx.AsyncClient(timeout=30) as client:
        # Give the job a moment to process
        await asyncio.sleep(1)

        response = await client.get(
            f"{BASE_URL}/v1/video/status/{job_id}",
            follow_redirects=True,
        )

        print(f"[STATUS] Status code: {response.status_code}")

        if response.status_code != 200:
            print(f"[STATUS] ERROR: Expected 200, got {response.status_code}")
            print(f"[STATUS] Response: {response.text}")
            return False

        data = response.json()

        # Verify required fields
        required_fields = ["job_id", "status", "progress"]  # v0.9.6: Added progress
        for field in required_fields:
            if field not in data:
                print(f"[STATUS] ERROR: Missing field '{field}' in response: {data}")
                return False

        status = data.get("status")
        if status not in ["pending", "running", "completed", "failed"]:
            print(f"[STATUS] ERROR: Invalid status '{status}'")
            return False

        # v0.9.6: Verify progress field is valid if present
        progress = data.get("progress")
        if progress is not None:
            if not isinstance(progress, (int, float)):
                print(
                    f"[STATUS] ERROR: Progress should be number, got {type(progress)}"
                )
                return False
            if not (0 <= progress <= 100):
                print(f"[STATUS] ERROR: Progress should be 0-100, got {progress}")
                return False

        print(f"[STATUS] SUCCESS: status={status}, progress={progress}")
        return True


async def test_job_results(job_id: str) -> bool:
    """Test job results endpoint.

    Returns True if results are valid or job is still processing.
    """
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.get(
            f"{BASE_URL}/v1/video/results/{job_id}",
            follow_redirects=True,
        )

        print(f"[RESULTS] Status code: {response.status_code}")

        if response.status_code == 404:
            # Job is still processing or failed - this is okay for smoke test
            print("[RESULTS] Job still processing (404 is expected)")
            return True

        if response.status_code != 200:
            print(f"[RESULTS] ERROR: Expected 200 or 404, got {response.status_code}")
            print(f"[RESULTS] Response: {response.text}")
            return False

        data = response.json()

        # Verify required fields
        required_fields = ["job_id", "results"]
        for field in required_fields:
            if field not in data:
                print(f"[RESULTS] ERROR: Missing field '{field}' in response: {data}")
                return False

        print(f"[RESULTS] SUCCESS: Retrieved {len(data.get('results', []))} results")
        return True


async def main():
    """Run job processing smoke test suite."""
    print("=" * 70)
    print("Job Processing Pipeline Smoke Test")
    print("=" * 70)

    # Skip if not running job processing smoke test
    if not JOB_PROCESSING_SMOKE_TEST:
        print("SKIPPED: JOB_PROCESSING_SMOKE_TEST env var not set")
        return 0

    try:
        # Test 1: Job Submission
        print("\n[TEST 1] Job Submission")
        job_id = await test_job_submission()

        if not job_id:
            print("✗ Job submission FAILED")
            return 1

        print("✓ Job submission PASSED")

        # Test 2: Job Status
        print("\n[TEST 2] Job Status")
        if not await test_job_status(job_id):
            print("✗ Job status FAILED")
            return 1

        print("✓ Job status PASSED")

        # Test 3: Job Results
        print("\n[TEST 3] Job Results")
        if not await test_job_results(job_id):
            print("✗ Job results FAILED")
            return 1

        print("✓ Job results PASSED")

        # All tests passed
        print("\n" + "=" * 70)
        print("✓ All smoke tests PASSED")
        print("=" * 70)
        return 0

    except Exception as e:
        print(f"\n✗ Smoke test ERROR: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
