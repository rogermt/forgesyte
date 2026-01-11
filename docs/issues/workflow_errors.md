============================= test session starts ==============================
platform linux -- Python 3.10.19, pytest-9.0.2, pluggy-1.6.0
rootdir: /home/runner/work/forgesyte/forgesyte/server
configfile: pyproject.toml
testpaths: tests
plugins: cov-7.0.0, asyncio-1.3.0, anyio-4.12.1
asyncio: mode=auto, debug=False, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
collected 445 items

tests/api/test_api_endpoints.py .................ssss.................   [  8%]
tests/api/test_jsonrpc.py .........................................      [ 17%]
tests/auth/test_basic_functionality.py ......                            [ 19%]
tests/mcp/test_mcp.py .......................................            [ 27%]
tests/mcp/test_mcp_adapter.py ........................F.........         [ 35%]
tests/mcp/test_mcp_capabilities_update.py ...                            [ 36%]
tests/mcp/test_mcp_endpoints.py .............                            [ 39%]
tests/mcp/test_mcp_gemini_integration.py ...........................     [ 45%]
tests/mcp/test_mcp_http_endpoint.py .................                    [ 48%]
tests/mcp/test_mcp_optimization.py .....................                 [ 53%]
tests/mcp/test_mcp_protocol_methods.py .............                     [ 56%]
tests/mcp/test_mcp_resources.py .......                                  [ 58%]
tests/mcp/test_mcp_tools_call.py ......                                  [ 59%]
tests/mcp/test_mcp_transport.py .................                        [ 63%]
tests/mcp/test_mcp_version_negotiation.py .......                        [ 64%]
tests/plugins/test_plugin_metadata.py .................................. [ 72%]
...................                                                      [ 76%]
tests/tasks/test_tasks.py ..........F..........FFF..........F.F........F [ 87%]
.....                                                                    [ 88%]
tests/test_transformation_verification.py .......                        [ 89%]
tests/websocket/test_websocket_manager.py .............................. [ 96%]
...............
ERROR: Coverage failure: total of 68.53 is less than fail-under=80.00
                                                                         [100%]

=================================== FAILURES ===================================
_____ TestMCPAdapterValidation.test_invalid_metadata_skipped_with_logging ______

self = <mcp.test_mcp_adapter.TestMCPAdapterValidation object at 0x7fa06df83670>
adapter = <app.mcp.adapter.MCPAdapter object at 0x7fa06e26f070>
mock_plugin_manager = <Mock spec='PluginManager' id='140327019540784'>
caplog = <_pytest.logging.LogCaptureFixture object at 0x7fa06d9b17b0>

    def test_invalid_metadata_skipped_with_logging(
        self, adapter, mock_plugin_manager, caplog
    ):
        """Test that invalid metadata is skipped and logged."""
        invalid_metadata = {
            "name": "",  # Empty name - invalid
            "description": "Test",
        }
        mock_plugin_manager.list.return_value = {"invalid": invalid_metadata}
    
        with caplog.at_level(logging.ERROR):
            manifest = adapter.get_manifest()
    
        # Should skip invalid plugin
        assert len(manifest["tools"]) == 0
        # Should log error
        assert "Invalid plugin metadata" in caplog.text
>       assert "invalid" in caplog.text
E       AssertionError: assert 'invalid' in 'ERROR    app.mcp.adapter:adapter.py:287 Invalid plugin metadata\n'
E        +  where 'ERROR    app.mcp.adapter:adapter.py:287 Invalid plugin metadata\n' = <_pytest.logging.LogCaptureFixture object at 0x7fa06d9b17b0>.text

tests/mcp/test_mcp_adapter.py:429: AssertionError
------------------------------ Captured log call -------------------------------
ERROR    app.mcp.adapter:adapter.py:287 Invalid plugin metadata
________________ TestJobStoreUpdate.test_update_multiple_fields ________________

self = <tasks.test_tasks.TestJobStoreUpdate object at 0x7fa06e3f0f40>
job_store = <app.tasks.JobStore object at 0x7fa06d9c9870>

    @pytest.mark.asyncio
    async def test_update_multiple_fields(self, job_store: JobStore) -> None:
        """Test updating multiple fields at once."""
        await job_store.create(
            "job1",
            {
                "job_id": "job1",
                "plugin": "plugin1",
                "status": JobStatus.QUEUED,
                "result": None,
                "error": None,
                "created_at": datetime.utcnow(),
                "completed_at": None,
                "progress": 0.0,
            },
        )
        result = {
            "data": [1, 2, 3],
        }
        completed = datetime.utcnow()
>       await job_store.update(
            "job1",
            status=JobStatus.DONE,
            result=result,
            completed_at=completed,
            progress=1.0,
        )
E       TypeError: JobStore.update() got an unexpected keyword argument 'status'

tests/tasks/test_tasks.py:216: TypeError
________________ TestJobStoreList.test_list_jobs_respects_limit ________________

self = <tasks.test_tasks.TestJobStoreList object at 0x7fa06e3f0400>
job_store = <app.tasks.JobStore object at 0x7fa06e693640>

    @pytest.mark.asyncio
    async def test_list_jobs_respects_limit(self, job_store: JobStore) -> None:
        """Test that list_jobs respects the limit parameter."""
        for i in range(100):
>           await job_store.create(f"job{i}", "plugin1")

tests/tasks/test_tasks.py:567: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

self = <app.tasks.JobStore object at 0x7fa06e693640>, job_id = 'job0'
job_data = 'plugin1'

    async def create(self, job_id: str, job_data: dict[str, Any]) -> None:
        """Create a new job entry.
    
        Args:
            job_id: Unique identifier for the job
            job_data: Job data dictionary with initial state
    
        Raises:
            RuntimeError: If job already exists or storage fails
    
        Notes:
            Automatically cleanup old jobs if at capacity.
        """
        async with self._lock:
            if job_id in self._jobs:
                raise RuntimeError(f"Job {job_id} already exists")
    
            # Cleanup old jobs if at capacity
            if len(self._jobs) >= self._max_jobs:
                await self._cleanup_old_jobs()
    
            self._jobs[job_id] = job_data
            logger.debug(
                "Job created",
>               extra={"job_id": job_id, "plugin": job_data.get("plugin")},
            )
E           AttributeError: 'str' object has no attribute 'get'

app/tasks.py:84: AttributeError
____________ TestJobStoreCleanup.test_cleanup_triggered_at_capacity ____________

self = <tasks.test_tasks.TestJobStoreCleanup object at 0x7fa06e3f0ca0>

    @pytest.mark.asyncio
    async def test_cleanup_triggered_at_capacity(self) -> None:
        """Test that cleanup is triggered when store reaches max capacity."""
        store = JobStore(max_jobs=5)
    
        # Add jobs until cleanup is needed
        for i in range(5):
>           await store.create(f"job{i}", "plugin1")

tests/tasks/test_tasks.py:583: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

self = <app.tasks.JobStore object at 0x7fa06e26e3b0>, job_id = 'job0'
job_data = 'plugin1'

    async def create(self, job_id: str, job_data: dict[str, Any]) -> None:
        """Create a new job entry.
    
        Args:
            job_id: Unique identifier for the job
            job_data: Job data dictionary with initial state
    
        Raises:
            RuntimeError: If job already exists or storage fails
    
        Notes:
            Automatically cleanup old jobs if at capacity.
        """
        async with self._lock:
            if job_id in self._jobs:
                raise RuntimeError(f"Job {job_id} already exists")
    
            # Cleanup old jobs if at capacity
            if len(self._jobs) >= self._max_jobs:
                await self._cleanup_old_jobs()
    
            self._jobs[job_id] = job_data
            logger.debug(
                "Job created",
>               extra={"job_id": job_id, "plugin": job_data.get("plugin")},
            )
E           AttributeError: 'str' object has no attribute 'get'

app/tasks.py:84: AttributeError
___________ TestJobStoreCleanup.test_cleanup_removes_completed_jobs ____________

self = <tasks.test_tasks.TestJobStoreCleanup object at 0x7fa06e3f1480>

    @pytest.mark.asyncio
    async def test_cleanup_removes_completed_jobs(self) -> None:
        """Test that cleanup removes completed jobs first."""
        store = JobStore(max_jobs=3)
    
>       await store.create("job1", "plugin1")

tests/tasks/test_tasks.py:600: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

self = <app.tasks.JobStore object at 0x7fa06e172530>, job_id = 'job1'
job_data = 'plugin1'

    async def create(self, job_id: str, job_data: dict[str, Any]) -> None:
        """Create a new job entry.
    
        Args:
            job_id: Unique identifier for the job
            job_data: Job data dictionary with initial state
    
        Raises:
            RuntimeError: If job already exists or storage fails
    
        Notes:
            Automatically cleanup old jobs if at capacity.
        """
        async with self._lock:
            if job_id in self._jobs:
                raise RuntimeError(f"Job {job_id} already exists")
    
            # Cleanup old jobs if at capacity
            if len(self._jobs) >= self._max_jobs:
                await self._cleanup_old_jobs()
    
            self._jobs[job_id] = job_data
            logger.debug(
                "Job created",
>               extra={"job_id": job_id, "plugin": job_data.get("plugin")},
            )
E           AttributeError: 'str' object has no attribute 'get'

app/tasks.py:84: AttributeError
______________ TestTaskProcessorCancelJob.test_cancel_running_job ______________

self = <tasks.test_tasks.TestTaskProcessorCancelJob object at 0x7fa06dcb25c0>
task_processor = <app.tasks.TaskProcessor object at 0x7fa06dab57e0>

    @pytest.mark.asyncio
    async def test_cancel_running_job(self, task_processor: TaskProcessor) -> None:
        """Test cancelling a running job (can't cancel)."""
        job_id = await task_processor.submit_job(b"image_data", "plugin1")
>       await task_processor.job_store.update(job_id, status=JobStatus.RUNNING)
E       TypeError: JobStore.update() got an unexpected keyword argument 'status'

tests/tasks/test_tasks.py:727: TypeError
------------------------------ Captured log call -------------------------------
WARNING  app.tasks:tasks.py:358 Plugin not found
_____________ TestTaskProcessorCancelJob.test_cancel_completed_job _____________

self = <tasks.test_tasks.TestTaskProcessorCancelJob object at 0x7fa06dcb2a70>
task_processor = <app.tasks.TaskProcessor object at 0x7fa06dff6740>

    @pytest.mark.asyncio
    async def test_cancel_completed_job(self, task_processor: TaskProcessor) -> None:
        """Test cancelling a completed job."""
        job_id = await task_processor.submit_job(b"image_data", "plugin1")
>       await task_processor.job_store.update(job_id, status=JobStatus.DONE)
E       TypeError: JobStore.update() got an unexpected keyword argument 'status'

tests/tasks/test_tasks.py:741: TypeError
------------------------------ Captured log call -------------------------------
WARNING  app.tasks:tasks.py:358 Plugin not found
_____________________ TestEdgeCases.test_empty_image_bytes _____________________

self = <tasks.test_tasks.TestEdgeCases object at 0x7fa06e3f1930>
task_processor = <app.tasks.TaskProcessor object at 0x7fa06d9c82e0>

    @pytest.mark.asyncio
    async def test_empty_image_bytes(self, task_processor: TaskProcessor) -> None:
        """Test submitting empty image bytes."""
>       job_id = await task_processor.submit_job(b"", "plugin1")

tests/tasks/test_tasks.py:913: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

self = <app.tasks.TaskProcessor object at 0x7fa06d9c82e0>, image_bytes = b''
plugin_name = 'plugin1', options = None, callback = None

    async def submit_job(
        self,
        image_bytes: bytes,
        plugin_name: str,
        options: Optional[dict[str, Any]] = None,
        callback: Optional[Callable[[dict[str, Any]], Any]] = None,
    ) -> str:
        """Submit a new image analysis job.
    
        Creates a job record and dispatches it for asynchronous processing
        in the background. Returns immediately with the job_id.
    
        Args:
            image_bytes: Raw image data (PNG, JPEG, etc.)
            plugin_name: Name of the analysis plugin to use
            options: Plugin-specific analysis options (optional)
            callback: Callable invoked when job completes (optional)
    
        Returns:
            Job ID for status tracking and result retrieval
    
        Raises:
            ValueError: If image_bytes is empty or plugin_name is missing
        """
        if not image_bytes:
            logger.warning("Submitted job with empty image data")
>           raise ValueError("image_bytes cannot be empty")
E           ValueError: image_bytes cannot be empty

app/tasks.py:282: ValueError
------------------------------ Captured log call -------------------------------
WARNING  app.tasks:tasks.py:281 Submitted job with empty image data
=============================== warnings summary ===============================
tests/api/test_api_endpoints.py::TestAnalyzeEndpointInputValidation::test_analyze_invalid_json_options
  /home/runner/work/forgesyte/forgesyte/server/.venv/lib/python3.10/site-packages/httpx/_models.py:408: DeprecationWarning: Use 'content=<...>' to upload raw bytes/text content.
    headers, stream = encode_request(

tests/mcp/test_mcp_optimization.py::TestManifestCaching::test_manifest_cache_initially_empty
  tests/mcp/test_mcp_optimization.py:144: PytestWarning: The test <Function test_manifest_cache_initially_empty> is marked with '@pytest.mark.asyncio' but it is not an async function. Please remove the asyncio mark. If the test is not marked explicitly, check for global marks applied via 'pytestmark'.
    def test_manifest_cache_initially_empty(self, adapter: MCPAdapter) -> None:

tests/mcp/test_mcp_optimization.py::TestManifestCaching::test_manifest_cache_stores_manifest
  tests/mcp/test_mcp_optimization.py:149: PytestWarning: The test <Function test_manifest_cache_stores_manifest> is marked with '@pytest.mark.asyncio' but it is not an async function. Please remove the asyncio mark. If the test is not marked explicitly, check for global marks applied via 'pytestmark'.
    def test_manifest_cache_stores_manifest(self, adapter: MCPAdapter) -> None:

tests/mcp/test_mcp_optimization.py::TestManifestCaching::test_manifest_cache_stores_timestamp
  tests/mcp/test_mcp_optimization.py:157: PytestWarning: The test <Function test_manifest_cache_stores_timestamp> is marked with '@pytest.mark.asyncio' but it is not an async function. Please remove the asyncio mark. If the test is not marked explicitly, check for global marks applied via 'pytestmark'.
    def test_manifest_cache_stores_timestamp(self, adapter: MCPAdapter) -> None:

tests/mcp/test_mcp_optimization.py::TestManifestCaching::test_manifest_cache_is_valid_within_ttl
  tests/mcp/test_mcp_optimization.py:165: PytestWarning: The test <Function test_manifest_cache_is_valid_within_ttl> is marked with '@pytest.mark.asyncio' but it is not an async function. Please remove the asyncio mark. If the test is not marked explicitly, check for global marks applied via 'pytestmark'.
    def test_manifest_cache_is_valid_within_ttl(self, adapter: MCPAdapter) -> None:

tests/mcp/test_mcp_optimization.py::TestManifestCaching::test_manifest_cache_expires_after_ttl
  tests/mcp/test_mcp_optimization.py:172: PytestWarning: The test <Function test_manifest_cache_expires_after_ttl> is marked with '@pytest.mark.asyncio' but it is not an async function. Please remove the asyncio mark. If the test is not marked explicitly, check for global marks applied via 'pytestmark'.
    def test_manifest_cache_expires_after_ttl(self, adapter: MCPAdapter) -> None:

tests/mcp/test_mcp_optimization.py::TestManifestCaching::test_get_manifest_uses_cache
  tests/mcp/test_mcp_optimization.py:182: PytestWarning: The test <Function test_get_manifest_uses_cache> is marked with '@pytest.mark.asyncio' but it is not an async function. Please remove the asyncio mark. If the test is not marked explicitly, check for global marks applied via 'pytestmark'.
    def test_get_manifest_uses_cache(self, adapter: MCPAdapter) -> None:

tests/mcp/test_mcp_optimization.py::TestManifestCaching::test_get_manifest_regenerates_after_expiry
  tests/mcp/test_mcp_optimization.py:192: PytestWarning: The test <Function test_get_manifest_regenerates_after_expiry> is marked with '@pytest.mark.asyncio' but it is not an async function. Please remove the asyncio mark. If the test is not marked explicitly, check for global marks applied via 'pytestmark'.
    def test_get_manifest_regenerates_after_expiry(self, adapter: MCPAdapter) -> None:

tests/mcp/test_mcp_optimization.py::TestManifestCaching::test_cache_ttl_configurable
  tests/mcp/test_mcp_optimization.py:215: PytestWarning: The test <Function test_cache_ttl_configurable> is marked with '@pytest.mark.asyncio' but it is not an async function. Please remove the asyncio mark. If the test is not marked explicitly, check for global marks applied via 'pytestmark'.
    def test_cache_ttl_configurable(self, adapter: MCPAdapter) -> None:

tests/mcp/test_mcp_optimization.py::TestOptimizationPerformance::test_manifest_cache_reduces_builds
  tests/mcp/test_mcp_optimization.py:324: PytestWarning: The test <Function test_manifest_cache_reduces_builds> is marked with '@pytest.mark.asyncio' but it is not an async function. Please remove the asyncio mark. If the test is not marked explicitly, check for global marks applied via 'pytestmark'.
    def test_manifest_cache_reduces_builds(

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
================================ tests coverage ================================
_______________ coverage: platform linux, python 3.10.19-final-0 _______________

Name                                        Stmts   Miss   Cover   Missing
--------------------------------------------------------------------------
app/__init__.py                                 1      0 100.00%
app/api.py                                    124     37  70.16%   52, 68-70, 86, 150-154, 157-161, 170-175, 200-205, 228-234, 256-265, 315, 339-345, 364-366
app/auth.py                                    86     13  84.88%   84-89, 92-97, 162, 181, 187, 253, 324-325, 339
app/exceptions.py                              61     31  49.18%   60-61, 86-88, 113-115, 136-137, 153-154, 172-173, 193-194, 215-216, 232-233, 250-251, 269-270, 291-292, 310-311, 339-341
app/main.py                                   122     59  51.64%   58-59, 75-84, 92-93, 99-100, 111-125, 138-139, 176-180, 194-196, 226-302, 319
app/mcp/__init__.py                             6      0 100.00%
app/mcp/adapter.py                            110      9  91.82%   175, 212, 241-244, 264-265, 416
app/mcp/handlers.py                            69     12  82.61%   189-194, 224-225, 237-238, 280-289
app/mcp/jsonrpc.py                             35      0 100.00%
app/mcp/routes.py                              45      4  91.11%   156-166
app/mcp/transport.py                           93     14  84.95%   137-147, 200-206, 265-280, 323-324
app/models.py                                  59      0 100.00%
app/plugin_loader.py                          139     64  53.96%   36, 53, 61, 69, 85-86, 98, 113, 129-130, 139, 146-147, 160-172, 246-248, 280, 298-303, 339-372, 387-398, 430-445
app/plugins/__init__.py                         0      0 100.00%
app/protocols.py                               43     18  58.14%   42, 53, 64, 83, 91, 105, 121, 141, 163, 171, 191, 211, 222, 239, 257, 284, 295, 306
app/services/__init__.py                        7      0 100.00%
app/services/analysis_service.py               44     15  65.91%   112-138, 167-168, 172-180
app/services/health_check.py                   74     66  10.81%   46-54, 85-157, 178-205
app/services/image_acquisition.py              47     33  29.79%   56, 58, 89-140, 166-186
app/services/job_management_service.py         40     27  32.50%   76-91, 119-139, 159-174
app/services/plugin_management_service.py      50     28  44.00%   84-86, 111-118, 122-127, 152-167, 189-205
app/services/vision_analysis.py                46     32  30.43%   77-147, 161-170
app/tasks.py                                  137     19  86.13%   75, 79, 187-207, 285-286, 401-405, 499-503
app/websocket_manager.py                      100      3  97.00%   75, 87, 98
--------------------------------------------------------------------------
TOTAL                                        1538    484  68.53%
FAIL Required test coverage of 80.0% not reached. Total coverage: 68.53%
=========================== short test summary info ============================
SKIPPED [1] tests/api/test_api_endpoints.py:170: Pre-existing failure: request validation issue unrelated to refactoring
SKIPPED [1] tests/api/test_api_endpoints.py:178: Pre-existing failure: request validation issue unrelated to refactoring
SKIPPED [1] tests/api/test_api_endpoints.py:186: Pre-existing failure: request validation issue unrelated to refactoring
SKIPPED [1] tests/api/test_api_endpoints.py:194: Pre-existing failure: request validation issue unrelated to refactoring
FAILED tests/mcp/test_mcp_adapter.py::TestMCPAdapterValidation::test_invalid_metadata_skipped_with_logging - AssertionError: assert 'invalid' in 'ERROR    app.mcp.adapter:adapter.py:287 Invalid plugin metadata\n'
 +  where 'ERROR    app.mcp.adapter:adapter.py:287 Invalid plugin metadata\n' = <_pytest.logging.LogCaptureFixture object at 0x7fa06d9b17b0>.text
FAILED tests/tasks/test_tasks.py::TestJobStoreUpdate::test_update_multiple_fields - TypeError: JobStore.update() got an unexpected keyword argument 'status'
FAILED tests/tasks/test_tasks.py::TestJobStoreList::test_list_jobs_respects_limit - AttributeError: 'str' object has no attribute 'get'
FAILED tests/tasks/test_tasks.py::TestJobStoreCleanup::test_cleanup_triggered_at_capacity - AttributeError: 'str' object has no attribute 'get'
FAILED tests/tasks/test_tasks.py::TestJobStoreCleanup::test_cleanup_removes_completed_jobs - AttributeError: 'str' object has no attribute 'get'
FAILED tests/tasks/test_tasks.py::TestTaskProcessorCancelJob::test_cancel_running_job - TypeError: JobStore.update() got an unexpected keyword argument 'status'
FAILED tests/tasks/test_tasks.py::TestTaskProcessorCancelJob::test_cancel_completed_job - TypeError: JobStore.update() got an unexpected keyword argument 'status'
FAILED tests/tasks/test_tasks.py::TestEdgeCases::test_empty_image_bytes - ValueError: image_bytes cannot be empty
============ 8 failed, 433 passed, 4 skipped, 10 warnings in 16.26s ============
Error: Process completed with exit code 1.