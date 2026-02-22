rogermt@LAPTOP-8B85T8ID:~/forgesyte/server$
rogermt@LAPTOP-8B85T8ID:~/forgesyte/server$
rogermt@LAPTOP-8B85T8ID:~/forgesyte/server$ # 1. Plugin execution (most uncertain)
uv run pytest tests/services/test_plugin_management_service.py::TestPluginManagementService::test_run_plugin_tool_success_sync -v --tb=long 2>&1

# 2. Image validation (medium uncertainty)
uv run pytest tests/image/test_image_submit_mocked.py::TestImageSubmitValidation::test_null_manifest_returns_400 -v --tb=long 2>&1

# 3. Device integration (medium uncertainty)
uv run pytest tests/integration/test_phase8_end_to_end.py::TestPhase8Pipeline::test_end_to_end_device_default_when_not_specified -v --tb=long 2>&1

# 4. Import errors (very uncertain)
uv run pytest tests/services/test_manifest_canonicalization.py::test_manifest_with_inputs_preserved -v --tb=long 2>&1
============================================================================================= test session starts ==============================================================================================
platform linux -- Python 3.13.11, pytest-9.0.2, pluggy-1.6.0 -- /home/rogermt/forgesyte/server/.venv/bin/python
cachedir: .pytest_cache
rootdir: /home/rogermt/forgesyte/server
configfile: pyproject.toml
plugins: anyio-4.12.1, asyncio-1.3.0, cov-7.0.0
asyncio: mode=Mode.AUTO, debug=False, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
collected 1 item

tests/services/test_plugin_management_service.py::TestPluginManagementService::test_run_plugin_tool_success_sync FAILED                                                                                  [100%]

=================================================================================================== FAILURES ===================================================================================================
________________________________________________________________________ TestPluginManagementService.test_run_plugin_tool_success_sync _________________________________________________________________________

self = <test_plugin_management_service.TestPluginManagementService object at 0x7d5d5a226c10>, service = <app.services.plugin_management_service.PluginManagementService object at 0x7d5d27e6c830>
mock_registry = <Mock spec='PluginRegistry' id='137839054866144'>

    def test_run_plugin_tool_success_sync(self, service, mock_registry):
        """Test successful sync tool execution via registry.get()."""
        # Create a mock plugin with a callable tool method
        mock_plugin = Mock()
        mock_plugin.test_tool.return_value = {"result": "success"}

        # registry.get() returns the plugin instance
        mock_registry.get.return_value = mock_plugin

        # Execute the tool
>       result = service.run_plugin_tool(
            plugin_id="test-plugin",
            tool_name="test_tool",
            args={"arg1": "value1"},
        )

tests/services/test_plugin_management_service.py:158:
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _

self = <app.services.plugin_management_service.PluginManagementService object at 0x7d5d27e6c830>, plugin_id = 'test-plugin', tool_name = 'test_tool', args = {'arg1': 'value1'}

    def run_plugin_tool(
        self,
        plugin_id: str,
        tool_name: str,
        args: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Execute a plugin tool with given arguments using sandbox.

        Finds the plugin, locates the tool function, validates arguments,
        and executes the tool in a crash-proof sandbox. Handles both sync
        and async tool functions with state tracking.

        Args:
            plugin_id: Plugin ID
            tool_name: Tool function name (must exist as method on plugin)
            args: Tool arguments (dict, should match manifest input schema)

        Returns:
            Tool result dict (should match manifest output schema)

        Raises:
            ValueError: Plugin/tool not found, or validation error
            TimeoutError: Tool execution exceeded timeout
            Exception: Tool execution failed
        """
        # Get registry for state tracking
        registry = get_registry()

        # 1. Find plugin in registry
        plugin = self.registry.get(plugin_id)

        if not plugin:
            plugins_dict = self.registry.list()
            available = (
                list(plugins_dict.keys())
                if isinstance(plugins_dict, dict)
                else [getattr(p, "name", "unknown") for p in plugins_dict]
            )
            raise ValueError(f"Plugin '{plugin_id}' not found. Available: {available}")

        logger.debug(f"Found plugin: {plugin}")

        # 2. Validate tool exists in plugin.tools (canonical source)
>       if not hasattr(plugin, "tools") or tool_name not in plugin.tools:
                                           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E       TypeError: argument of type 'Mock' is not iterable

app/services/plugin_management_service.py:372: TypeError
-------------------------------------------------------------------------------------------- Captured stderr setup ---------------------------------------------------------------------------------------------
Resolved 9 packages in 690ms
   Building forgesyte-ocr @ file:///home/rogermt/forgesyte-plugins/plugins/ocr
      Built forgesyte-ocr @ file:///home/rogermt/forgesyte-plugins/plugins/ocr
Prepared 1 package in 1.21s
Uninstalled 1 package in 6ms
Installed 1 package in 3ms
 ~ forgesyte-ocr==1.0.0 (from file:///home/rogermt/forgesyte-plugins/plugins/ocr)
=============================================================================================== warnings summary ===============================================================================================
app/plugins/health/health_model.py:14
  /home/rogermt/forgesyte/server/tests/services/../../app/plugins/health/health_model.py:14: PydanticDeprecatedSince20: Support for class-based `config` is deprecated, use ConfigDict instead. Deprecated in Pydantic V2.0 to be removed in V3.0. See Pydantic V2 Migration Guide at https://errors.pydantic.dev/2.12/migration/
    class PluginHealthResponse(BaseModel):

app/plugins/health/health_model.py:53
  /home/rogermt/forgesyte/server/tests/services/../../app/plugins/health/health_model.py:53: PydanticDeprecatedSince20: Support for class-based `config` is deprecated, use ConfigDict instead. Deprecated in Pydantic V2.0 to be removed in V3.0. See Pydantic V2 Migration Guide at https://errors.pydantic.dev/2.12/migration/
    class PluginListResponse(BaseModel):

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
=========================================================================================== short test summary info ============================================================================================
FAILED tests/services/test_plugin_management_service.py::TestPluginManagementService::test_run_plugin_tool_success_sync - TypeError: argument of type 'Mock' is not iterable
======================================================================================== 1 failed, 2 warnings in 3.90s =========================================================================================
============================================================================================= test session starts ==============================================================================================
platform linux -- Python 3.13.11, pytest-9.0.2, pluggy-1.6.0 -- /home/rogermt/forgesyte/server/.venv/bin/python
cachedir: .pytest_cache
rootdir: /home/rogermt/forgesyte/server
configfile: pyproject.toml
plugins: anyio-4.12.1, asyncio-1.3.0, cov-7.0.0
asyncio: mode=Mode.AUTO, debug=False, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
collected 1 item

tests/image/test_image_submit_mocked.py::TestImageSubmitValidation::test_null_manifest_returns_400 FAILED                                                                                                [100%]

=================================================================================================== FAILURES ===================================================================================================
___________________________________________________________________________ TestImageSubmitValidation.test_null_manifest_returns_400 ___________________________________________________________________________

self = <server.tests.image.test_image_submit_mocked.TestImageSubmitValidation object at 0x7772801097f0>, client = <starlette.testclient.TestClient object at 0x77728017c2f0>

    def test_null_manifest_returns_400(self, client):
        with (
>           patch(f"{ROUTE}.plugin_manager") as pm,
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
            patch(f"{ROUTE}.plugin_service") as ps,
        ):

tests/image/test_image_submit_mocked.py:142:
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _

self = <unittest.mock._patch object at 0x77728017d010>

    def __enter__(self):
        """Perform the patch."""
        if self.is_started:
            raise RuntimeError("Patch is already started")

        new, spec, spec_set = self.new, self.spec, self.spec_set
        autospec, kwargs = self.autospec, self.kwargs
        new_callable = self.new_callable
        self.target = self.getter()

        # normalise False to None
        if spec is False:
            spec = None
        if spec_set is False:
            spec_set = None
        if autospec is False:
            autospec = None

        if spec is not None and autospec is not None:
            raise TypeError("Can't specify spec and autospec")
        if ((spec is not None or autospec is not None) and
            spec_set not in (True, None)):
            raise TypeError("Can't provide explicit spec_set *and* spec or autospec")

>       original, local = self.get_original()
                          ^^^^^^^^^^^^^^^^^^^

../../.local/share/uv/python/cpython-3.13.11-linux-x86_64-gnu/lib/python3.13/unittest/mock.py:1497:
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _

self = <unittest.mock._patch object at 0x77728017d010>

    def get_original(self):
        target = self.getter()
        name = self.attribute

        original = DEFAULT
        local = False

        try:
            original = target.__dict__[name]
        except (AttributeError, KeyError):
            original = getattr(target, name, DEFAULT)
        else:
            local = True

        if name in _builtins and isinstance(target, ModuleType):
            self.create = True

        if not self.create and original is DEFAULT:
>           raise AttributeError(
                "%s does not have the attribute %r" % (target, name)
            )
E           AttributeError: <module 'app.api_routes.routes.image_submit' from '/home/rogermt/forgesyte/server/tests/../app/api_routes/routes/image_submit.py'> does not have the attribute 'plugin_manager'

../../.local/share/uv/python/cpython-3.13.11-linux-x86_64-gnu/lib/python3.13/unittest/mock.py:1467: AttributeError
-------------------------------------------------------------------------------------------- Captured stderr setup ---------------------------------------------------------------------------------------------
Resolved 9 packages in 63ms
   Building forgesyte-ocr @ file:///home/rogermt/forgesyte-plugins/plugins/ocr
      Built forgesyte-ocr @ file:///home/rogermt/forgesyte-plugins/plugins/ocr
Prepared 1 package in 1.64s
Uninstalled 1 package in 0.97ms
Installed 1 package in 1ms
 ~ forgesyte-ocr==1.0.0 (from file:///home/rogermt/forgesyte-plugins/plugins/ocr)
=============================================================================================== warnings summary ===============================================================================================
app/models_pydantic.py:246
  /home/rogermt/forgesyte/server/tests/../app/models_pydantic.py:246: PydanticDeprecatedSince20: Using extra keyword arguments on `Field` is deprecated and will be removed. Use `json_schema_extra` instead. (Extra keys: 'example'). Deprecated in Pydantic V2.0 to be removed in V3.0. See Pydantic V2 Migration Guide at https://errors.pydantic.dev/2.12/migration/
    args: Dict[str, Any] = Field(

app/models_pydantic.py:243
  /home/rogermt/forgesyte/server/tests/../app/models_pydantic.py:243: PydanticDeprecatedSince20: Support for class-based `config` is deprecated, use ConfigDict instead. Deprecated in Pydantic V2.0 to be removed in V3.0. See Pydantic V2 Migration Guide at https://errors.pydantic.dev/2.12/migration/
    class PluginToolRunRequest(BaseModel):

app/models_pydantic.py:264
  /home/rogermt/forgesyte/server/tests/../app/models_pydantic.py:264: PydanticDeprecatedSince20: Support for class-based `config` is deprecated, use ConfigDict instead. Deprecated in Pydantic V2.0 to be removed in V3.0. See Pydantic V2 Migration Guide at https://errors.pydantic.dev/2.12/migration/
    class PluginToolRunResponse(BaseModel):

app/plugins/health/health_model.py:14
  /home/rogermt/forgesyte/server/tests/../app/plugins/health/health_model.py:14: PydanticDeprecatedSince20: Support for class-based `config` is deprecated, use ConfigDict instead. Deprecated in Pydantic V2.0 to be removed in V3.0. See Pydantic V2 Migration Guide at https://errors.pydantic.dev/2.12/migration/
    class PluginHealthResponse(BaseModel):

app/plugins/health/health_model.py:53
  /home/rogermt/forgesyte/server/tests/../app/plugins/health/health_model.py:53: PydanticDeprecatedSince20: Support for class-based `config` is deprecated, use ConfigDict instead. Deprecated in Pydantic V2.0 to be removed in V3.0. See Pydantic V2 Migration Guide at https://errors.pydantic.dev/2.12/migration/
    class PluginListResponse(BaseModel):

app/schemas/job.py:10
  /home/rogermt/forgesyte/server/tests/../app/schemas/job.py:10: PydanticDeprecatedSince20: Support for class-based `config` is deprecated, use ConfigDict instead. Deprecated in Pydantic V2.0 to be removed in V3.0. See Pydantic V2 Migration Guide at https://errors.pydantic.dev/2.12/migration/
    class JobStatusResponse(BaseModel):

app/schemas/job.py:25
  /home/rogermt/forgesyte/server/tests/../app/schemas/job.py:25: PydanticDeprecatedSince20: Support for class-based `config` is deprecated, use ConfigDict instead. Deprecated in Pydantic V2.0 to be removed in V3.0. See Pydantic V2 Migration Guide at https://errors.pydantic.dev/2.12/migration/
    class JobResultsResponse(BaseModel):

app/realtime/message_types.py:49
  /home/rogermt/forgesyte/server/tests/../app/realtime/message_types.py:49: PydanticDeprecatedSince20: Support for class-based `config` is deprecated, use ConfigDict instead. Deprecated in Pydantic V2.0 to be removed in V3.0. See Pydantic V2 Migration Guide at https://errors.pydantic.dev/2.12/migration/
    class RealtimeMessage(BaseModel):

.venv/lib/python3.13/site-packages/pydantic/_internal/_generate_schema.py:392
  /home/rogermt/forgesyte/server/.venv/lib/python3.13/site-packages/pydantic/_internal/_generate_schema.py:392: PydanticDeprecatedSince20: `json_encoders` is deprecated. See https://docs.pydantic.dev/2.12/concepts/serialization/#custom-serializers for alternatives. Deprecated in Pydantic V2.0 to be removed in V3.0. See Pydantic V2 Migration Guide at https://errors.pydantic.dev/2.12/migration/
    warnings.warn(

.venv/lib/python3.13/site-packages/pythonjsonlogger/jsonlogger.py:11
  /home/rogermt/forgesyte/server/.venv/lib/python3.13/site-packages/pythonjsonlogger/jsonlogger.py:11: DeprecationWarning: pythonjsonlogger.jsonlogger has been moved to pythonjsonlogger.json
    warnings.warn(

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
=========================================================================================== short test summary info ============================================================================================
FAILED tests/image/test_image_submit_mocked.py::TestImageSubmitValidation::test_null_manifest_returns_400 - AttributeError: <module 'app.api_routes.routes.image_submit' from '/home/rogermt/forgesyte/server/tests/../app/api_routes/routes/image_submit.py'> does not have the attribute 'plugin_manager'
======================================================================================== 1 failed, 10 warnings in 3.81s ========================================================================================
============================================================================================= test session starts ==============================================================================================
platform linux -- Python 3.13.11, pytest-9.0.2, pluggy-1.6.0 -- /home/rogermt/forgesyte/server/.venv/bin/python
cachedir: .pytest_cache
rootdir: /home/rogermt/forgesyte/server
configfile: pyproject.toml
plugins: anyio-4.12.1, asyncio-1.3.0, cov-7.0.0
asyncio: mode=Mode.AUTO, debug=False, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
collected 1 item

tests/integration/test_phase8_end_to_end.py::TestPhase8Pipeline::test_end_to_end_device_default_when_not_specified FAILED                                                                                [100%]

=================================================================================================== FAILURES ===================================================================================================
_____________________________________________________________________ TestPhase8Pipeline.test_end_to_end_device_default_when_not_specified _____________________________________________________________________

self = <test_phase8_end_to_end.TestPhase8Pipeline object at 0x72e71bc61eb0>, client = <httpx.AsyncClient object at 0x72e6cc14acf0>

    @pytest.mark.asyncio
    async def test_end_to_end_device_default_when_not_specified(self, client) -> None:
        """Phase 12: Device defaults to 'default' when not specified (plugin resolves via models.yaml)."""
        response = await client.post(
            "/v1/analyze?plugin=ocr",
            files={"file": ("test.png", b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR")},
        )

>       assert response.status_code == 200
E       assert 404 == 200
E        +  where 404 = <Response [404 Not Found]>.status_code

tests/integration/test_phase8_end_to_end.py:174: AssertionError
-------------------------------------------------------------------------------------------- Captured stdout setup ---------------------------------------------------------------------------------------------
📝 Logging to: /home/rogermt/forgesyte/server/forgesyte.log
-------------------------------------------------------------------------------------------- Captured stderr setup ---------------------------------------------------------------------------------------------
Resolved 9 packages in 34ms
   Building forgesyte-ocr @ file:///home/rogermt/forgesyte-plugins/plugins/ocr
      Built forgesyte-ocr @ file:///home/rogermt/forgesyte-plugins/plugins/ocr
Prepared 1 package in 914ms
Uninstalled 1 package in 0.58ms
Installed 1 package in 3ms
 ~ forgesyte-ocr==1.0.0 (from file:///home/rogermt/forgesyte-plugins/plugins/ocr)
{"timestamp": "2026-02-22T16:44:06.779972+00:00", "level": null, "name": "app.main", "message": "\ud83d\ude80 ForgeSyte server starting..."}
{"timestamp": "2026-02-22T16:44:06.816148+00:00", "level": null, "name": "app.auth", "message": "Loaded admin API key from settings"}
{"timestamp": "2026-02-22T16:44:06.816862+00:00", "level": null, "name": "app.auth", "message": "Loaded user API key from settings"}
{"timestamp": "2026-02-22T16:44:06.817010+00:00", "level": null, "name": "app.auth", "message": "AuthService initialized"}
{"timestamp": "2026-02-22T16:44:06.817090+00:00", "level": null, "name": "app.auth", "message": "Authentication service initialized"}
{"timestamp": "2026-02-22T16:44:06.817167+00:00", "level": null, "name": "app.plugin_loader", "message": "PluginRegistry initialized"}
{"timestamp": "2026-02-22T16:44:06.889870+00:00", "level": null, "name": "app.plugin_loader", "message": "Plugin registered successfully", "plugin_name": "ocr"}
{"timestamp": "2026-02-22T16:44:06.890117+00:00", "level": null, "name": "app.plugin_loader", "message": "Entrypoint plugin loaded successfully", "plugin_name": "ocr", "source": "entrypoint:ocr"}
{"timestamp": "2026-02-22T16:44:06.890228+00:00", "level": null, "name": "app.plugins.loader.plugin_registry", "message": "\u2713 Registered plugin: ocr"}
{"timestamp": "2026-02-22T16:44:06.890288+00:00", "level": null, "name": "app.services.vision_analysis", "message": "VisionAnalysisService initialized"}
{"timestamp": "2026-02-22T16:44:06.890332+00:00", "level": null, "name": "app.services.plugin_management_service", "message": "PluginManagementService initialized"}
{"timestamp": "2026-02-22T16:44:06.890699+00:00", "level": null, "name": "asyncio", "message": "Using selector: EpollSelector"}
{"timestamp": "2026-02-22T16:44:06.893568+00:00", "level": null, "name": "asyncio", "message": "Using selector: EpollSelector"}
--------------------------------------------------------------------------------------------- Captured stderr call ---------------------------------------------------------------------------------------------
{"timestamp": "2026-02-22T16:44:06.904628+00:00", "level": null, "name": "httpx", "message": "HTTP Request: POST http://test/v1/analyze?plugin=ocr \"HTTP/1.1 404 Not Found\""}
---------------------------------------------------------------------------------------------- Captured log call -----------------------------------------------------------------------------------------------
INFO     httpx:_client.py:1744 HTTP Request: POST http://test/v1/analyze?plugin=ocr "HTTP/1.1 404 Not Found"
=============================================================================================== warnings summary ===============================================================================================
tests/integration/test_phase8_end_to_end.py::TestPhase8Pipeline::test_end_to_end_device_default_when_not_specified
  /home/rogermt/forgesyte/server/tests/../app/plugins/health/health_model.py:14: PydanticDeprecatedSince20: Support for class-based `config` is deprecated, use ConfigDict instead. Deprecated in Pydantic V2.0 to be removed in V3.0. See Pydantic V2 Migration Guide at https://errors.pydantic.dev/2.12/migration/
    class PluginHealthResponse(BaseModel):

tests/integration/test_phase8_end_to_end.py::TestPhase8Pipeline::test_end_to_end_device_default_when_not_specified
  /home/rogermt/forgesyte/server/tests/../app/plugins/health/health_model.py:53: PydanticDeprecatedSince20: Support for class-based `config` is deprecated, use ConfigDict instead. Deprecated in Pydantic V2.0 to be removed in V3.0. See Pydantic V2 Migration Guide at https://errors.pydantic.dev/2.12/migration/
    class PluginListResponse(BaseModel):

tests/integration/test_phase8_end_to_end.py::TestPhase8Pipeline::test_end_to_end_device_default_when_not_specified
  /home/rogermt/forgesyte/server/tests/../app/models_pydantic.py:246: PydanticDeprecatedSince20: Using extra keyword arguments on `Field` is deprecated and will be removed. Use `json_schema_extra` instead. (Extra keys: 'example'). Deprecated in Pydantic V2.0 to be removed in V3.0. See Pydantic V2 Migration Guide at https://errors.pydantic.dev/2.12/migration/
    args: Dict[str, Any] = Field(

tests/integration/test_phase8_end_to_end.py::TestPhase8Pipeline::test_end_to_end_device_default_when_not_specified
  /home/rogermt/forgesyte/server/tests/../app/models_pydantic.py:243: PydanticDeprecatedSince20: Support for class-based `config` is deprecated, use ConfigDict instead. Deprecated in Pydantic V2.0 to be removed in V3.0. See Pydantic V2 Migration Guide at https://errors.pydantic.dev/2.12/migration/
    class PluginToolRunRequest(BaseModel):

tests/integration/test_phase8_end_to_end.py::TestPhase8Pipeline::test_end_to_end_device_default_when_not_specified
  /home/rogermt/forgesyte/server/tests/../app/models_pydantic.py:264: PydanticDeprecatedSince20: Support for class-based `config` is deprecated, use ConfigDict instead. Deprecated in Pydantic V2.0 to be removed in V3.0. See Pydantic V2 Migration Guide at https://errors.pydantic.dev/2.12/migration/
    class PluginToolRunResponse(BaseModel):

tests/integration/test_phase8_end_to_end.py::TestPhase8Pipeline::test_end_to_end_device_default_when_not_specified
  /home/rogermt/forgesyte/server/tests/../app/schemas/job.py:10: PydanticDeprecatedSince20: Support for class-based `config` is deprecated, use ConfigDict instead. Deprecated in Pydantic V2.0 to be removed in V3.0. See Pydantic V2 Migration Guide at https://errors.pydantic.dev/2.12/migration/
    class JobStatusResponse(BaseModel):

tests/integration/test_phase8_end_to_end.py::TestPhase8Pipeline::test_end_to_end_device_default_when_not_specified
  /home/rogermt/forgesyte/server/tests/../app/schemas/job.py:25: PydanticDeprecatedSince20: Support for class-based `config` is deprecated, use ConfigDict instead. Deprecated in Pydantic V2.0 to be removed in V3.0. See Pydantic V2 Migration Guide at https://errors.pydantic.dev/2.12/migration/
    class JobResultsResponse(BaseModel):

tests/integration/test_phase8_end_to_end.py::TestPhase8Pipeline::test_end_to_end_device_default_when_not_specified
  /home/rogermt/forgesyte/server/tests/../app/realtime/message_types.py:49: PydanticDeprecatedSince20: Support for class-based `config` is deprecated, use ConfigDict instead. Deprecated in Pydantic V2.0 to be removed in V3.0. See Pydantic V2 Migration Guide at https://errors.pydantic.dev/2.12/migration/
    class RealtimeMessage(BaseModel):

tests/integration/test_phase8_end_to_end.py::TestPhase8Pipeline::test_end_to_end_device_default_when_not_specified
  /home/rogermt/forgesyte/server/.venv/lib/python3.13/site-packages/pydantic/_internal/_generate_schema.py:392: PydanticDeprecatedSince20: `json_encoders` is deprecated. See https://docs.pydantic.dev/2.12/concepts/serialization/#custom-serializers for alternatives. Deprecated in Pydantic V2.0 to be removed in V3.0. See Pydantic V2 Migration Guide at https://errors.pydantic.dev/2.12/migration/
    warnings.warn(

tests/integration/test_phase8_end_to_end.py::TestPhase8Pipeline::test_end_to_end_device_default_when_not_specified
  /home/rogermt/forgesyte/server/.venv/lib/python3.13/site-packages/pythonjsonlogger/jsonlogger.py:11: DeprecationWarning: pythonjsonlogger.jsonlogger has been moved to pythonjsonlogger.json
    warnings.warn(

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
=========================================================================================== short test summary info ============================================================================================
FAILED tests/integration/test_phase8_end_to_end.py::TestPhase8Pipeline::test_end_to_end_device_default_when_not_specified - assert 404 == 200
======================================================================================== 1 failed, 10 warnings in 2.30s ========================================================================================
============================================================================================= test session starts ==============================================================================================
platform linux -- Python 3.13.11, pytest-9.0.2, pluggy-1.6.0 -- /home/rogermt/forgesyte/server/.venv/bin/python
cachedir: .pytest_cache
rootdir: /home/rogermt/forgesyte/server
configfile: pyproject.toml
plugins: anyio-4.12.1, asyncio-1.3.0, cov-7.0.0
asyncio: mode=Mode.AUTO, debug=False, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
collected 1 item

tests/services/test_manifest_canonicalization.py::test_manifest_with_inputs_preserved ERROR                                                                                                              [100%]

==================================================================================================== ERRORS ====================================================================================================
____________________________________________________________________________ ERROR at setup of test_manifest_with_inputs_preserved _____________________________________________________________________________
file /home/rogermt/forgesyte/server/tests/services/test_manifest_canonicalization.py, line 32
  def test_manifest_with_inputs_preserved(plugin_service):
E       fixture 'plugin_service' not found
>       available fixtures: _class_scoped_runner, _function_scoped_runner, _module_scoped_runner, _package_scoped_runner, _session_scoped_runner, anyio_backend, anyio_backend_name, anyio_backend_options, app_with_mock_yolo_plugin, app_with_plugins, cache, capfd, capfdbinary, caplog, capsys, capsysbinary, capteesys, client, client_with_mock_yolo, cov, doctest_namespace, event_loop_policy, free_tcp_port, free_tcp_port_factory, free_udp_port, free_udp_port_factory, install_plugins, mock_job_store, mock_plugin_registry, mock_session_local, mock_task_processor, monkeypatch, no_cover, pytestconfig, record_property, record_testsuite_property, record_xml_attribute, recwarn, session, subtests, test_engine, tmp_path, tmp_path_factory, tmpdir, tmpdir_factory, unused_tcp_port, unused_tcp_port_factory, unused_udp_port, unused_udp_port_factory
>       use 'pytest --fixtures [testpath]' for help on them.

/home/rogermt/forgesyte/server/tests/services/test_manifest_canonicalization.py:32
-------------------------------------------------------------------------------------------- Captured stderr setup ---------------------------------------------------------------------------------------------
Resolved 9 packages in 17ms
   Building forgesyte-ocr @ file:///home/rogermt/forgesyte-plugins/plugins/ocr
      Built forgesyte-ocr @ file:///home/rogermt/forgesyte-plugins/plugins/ocr
Prepared 1 package in 794ms
Uninstalled 1 package in 0.57ms
Installed 1 package in 1ms
 ~ forgesyte-ocr==1.0.0 (from file:///home/rogermt/forgesyte-plugins/plugins/ocr)
=============================================================================================== warnings summary ===============================================================================================
app/plugins/health/health_model.py:14
  /home/rogermt/forgesyte/server/tests/../app/plugins/health/health_model.py:14: PydanticDeprecatedSince20: Support for class-based `config` is deprecated, use ConfigDict instead. Deprecated in Pydantic V2.0 to be removed in V3.0. See Pydantic V2 Migration Guide at https://errors.pydantic.dev/2.12/migration/
    class PluginHealthResponse(BaseModel):

app/plugins/health/health_model.py:53
  /home/rogermt/forgesyte/server/tests/../app/plugins/health/health_model.py:53: PydanticDeprecatedSince20: Support for class-based `config` is deprecated, use ConfigDict instead. Deprecated in Pydantic V2.0 to be removed in V3.0. See Pydantic V2 Migration Guide at https://errors.pydantic.dev/2.12/migration/
    class PluginListResponse(BaseModel):

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
=========================================================================================== short test summary info ============================================================================================
ERROR tests/services/test_manifest_canonicalization.py::test_manifest_with_inputs_preserved
========================================================================================= 2 warnings, 1 error in 1.58s =========================================================================================
rogermt@LAPTOP-8B85T8ID:~/forgesyte/server$