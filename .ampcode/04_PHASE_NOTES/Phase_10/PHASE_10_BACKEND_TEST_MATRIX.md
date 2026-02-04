# Phase 10 — Backend Test Matrix

Complete test matrix for Phase 10 backend components.

All tests are RED → GREEN. MUST NOT break Phase 9 invariants.

---

# 1. Real-Time Endpoint Tests

## 1.1 Smoke Tests

| Test | Expected | Files |
|------|----------|-------|
| `test_websocket_endpoint_exists` | Endpoint accepts WebSocket upgrade | `test_realtime_endpoint.py` |
| `test_websocket_connection_accepted` | Connection opens successfully | `test_realtime_endpoint.py` |
| `test_websocket_connection_refused_invalid_url` | Wrong URL returns 404 | `test_realtime_endpoint.py` |
| `test_websocket_multiple_connections` | Multiple clients can connect | `test_realtime_endpoint.py` |

## 1.2 Message Flow Tests

| Test | Trigger | Expected | Files |
|------|---------|----------|-------|
| `test_websocket_receives_frame_message` | frame emitted | Client receives JSON | `test_realtime_endpoint.py` |
| `test_websocket_receives_progress_message` | progress emitted | Client receives JSON | `test_realtime_endpoint.py` |
| `test_websocket_receives_plugin_status_message` | plugin_status emitted | Client receives JSON | `test_realtime_endpoint.py` |
| `test_websocket_receives_warning_message` | warning emitted | Client receives JSON | `test_realtime_endpoint.py` |
| `test_websocket_receives_error_message` | error emitted | Client receives JSON | `test_realtime_endpoint.py` |

## 1.3 Heartbeat Tests

| Test | Trigger | Expected | Files |
|------|---------|----------|-------|
| `test_websocket_sends_ping` | Periodic timer fires | ping sent to client | `test_realtime_endpoint.py` |
| `test_websocket_receives_pong` | pong received | Heartbeat recorded | `test_realtime_endpoint.py` |
| `test_websocket_heartbeat_timeout` | No pong in 60s | Connection closed | `test_realtime_endpoint.py` |
| `test_websocket_heartbeat_interval` | Multiple pings | Sent every 30s (±5s) | `test_realtime_endpoint.py` |

## 1.4 Disconnect Tests

| Test | Trigger | Expected | Files |
|------|---------|----------|-------|
| `test_websocket_client_disconnect` | Client closes connection | Server acknowledges | `test_realtime_endpoint.py` |
| `test_websocket_server_shutdown` | Server shuts down | WS closes cleanly | `test_realtime_endpoint.py` |
| `test_websocket_network_error` | Network breaks | Server cleans up client | `test_realtime_endpoint.py` |
| `test_websocket_reconnect` | Client reconnects | New connection accepted | `test_realtime_endpoint.py` |

---

# 2. Connection Manager Tests

## 2.1 Connection Lifecycle Tests

| Test | Expected | Files |
|------|----------|-------|
| `test_connection_manager_add_connection` | Connection registered | `test_connection_manager.py` |
| `test_connection_manager_has_connection` | `.is_connected()` returns true | `test_connection_manager.py` |
| `test_connection_manager_remove_connection` | Connection deregistered | `test_connection_manager.py` |
| `test_connection_manager_multiple_connections` | All tracked separately | `test_connection_manager.py` |

## 2.2 Broadcast Tests

| Test | Trigger | Expected | Files |
|------|---------|----------|-------|
| `test_connection_manager_broadcast_one_client` | send_all() | One client receives | `test_connection_manager.py` |
| `test_connection_manager_broadcast_multiple_clients` | send_all() | All clients receive | `test_connection_manager.py` |
| `test_connection_manager_broadcast_no_clients` | send_all() with 0 clients | No error | `test_connection_manager.py` |
| `test_connection_manager_broadcast_partial_failure` | One client drops mid-send | Other clients still receive | `test_connection_manager.py` |

## 2.3 Message Queuing Tests

| Test | Trigger | Expected | Files |
|------|---------|----------|-------|
| `test_connection_manager_queue_messages` | Send many messages quickly | Messages queued | `test_connection_manager.py` |
| `test_connection_manager_queue_limit` | Queue exceeds 1000 messages | Low-priority messages dropped | `test_connection_manager.py` |
| `test_connection_manager_queue_preserves_order` | Send 100 messages | Delivered in order | `test_connection_manager.py` |

---

# 3. Real-Time Message Type Tests

## 3.1 Frame Message Tests

| Test | Expected | Files |
|------|----------|-------|
| `test_frame_message_schema_valid` | Valid frame message | Passes validation | `test_realtime_messages.py` |
| `test_frame_message_has_frame_id` | frame_id present | String stored | `test_realtime_messages.py` |
| `test_frame_message_has_plugin` | plugin present | String stored | `test_realtime_messages.py` |
| `test_frame_message_has_data` | data dict present | Object stored | `test_realtime_messages.py` |
| `test_frame_message_has_timing_ms` | timing_ms present | Float stored | `test_realtime_messages.py` |
| `test_frame_message_serializable` | Serialize to JSON | Valid JSON output | `test_realtime_messages.py` |

## 3.2 Progress Message Tests

| Test | Expected | Files |
|------|----------|-------|
| `test_progress_message_schema_valid` | Valid progress message | Passes validation | `test_realtime_messages.py` |
| `test_progress_message_has_job_id` | job_id present | String stored | `test_realtime_messages.py` |
| `test_progress_message_has_progress` | progress present | 0-100 | `test_realtime_messages.py` |
| `test_progress_message_progress_range` | progress=50 | Accepted | `test_realtime_messages.py` |
| `test_progress_message_progress_boundary` | progress=0, 100 | Both accepted | `test_realtime_messages.py` |
| `test_progress_message_progress_invalid` | progress=150 | Rejected | `test_realtime_messages.py` |

## 3.3 Plugin Status Message Tests

| Test | Expected | Files |
|------|----------|-------|
| `test_plugin_status_message_valid` | Valid plugin_status message | Passes validation | `test_realtime_messages.py` |
| `test_plugin_status_message_has_plugin` | plugin present | String stored | `test_realtime_messages.py` |
| `test_plugin_status_message_has_status` | status in enum | accepted | `test_realtime_messages.py` |
| `test_plugin_status_message_has_timing_ms` | timing_ms present | Float >= 0 | `test_realtime_messages.py` |
| `test_plugin_status_message_status_values` | started/running/completed/failed | All accepted | `test_realtime_messages.py` |

## 3.4 Warning Message Tests

| Test | Expected | Files |
|------|----------|-------|
| `test_warning_message_valid` | Valid warning message | Passes validation | `test_realtime_messages.py` |
| `test_warning_message_has_plugin` | plugin present | String stored | `test_realtime_messages.py` |
| `test_warning_message_has_message` | message present | String stored | `test_realtime_messages.py` |
| `test_warning_message_has_severity` | severity optional | Accepted if present | `test_realtime_messages.py` |

## 3.5 Error Message Tests

| Test | Expected | Files |
|------|----------|-------|
| `test_error_message_valid` | Valid error message | Passes validation | `test_realtime_messages.py` |
| `test_error_message_has_error` | error present | String stored | `test_realtime_messages.py` |
| `test_error_message_has_details` | details optional | Object stored if present | `test_realtime_messages.py` |

## 3.6 Ping/Pong Tests

| Test | Expected | Files |
|------|----------|-------|
| `test_ping_message_valid` | Valid ping message | Passes validation | `test_realtime_messages.py` |
| `test_pong_message_valid` | Valid pong message | Passes validation | `test_realtime_messages.py` |

---

# 4. Extended Job Model Tests

## 4.1 Model Creation Tests

| Test | Expected | Files |
|------|----------|-------|
| `test_extended_job_response_creates` | Instantiate with required fields | No error | `test_models_phase10.py` |
| `test_extended_job_response_required_fields` | job_id, device_requested, etc. | All present | `test_models_phase10.py` |
| `test_extended_job_response_optional_fields` | progress, plugin_timings, warnings | Accepted if present | `test_models_phase10.py` |

## 4.2 Field Type Tests

| Test | Input | Expected | Files |
|------|-------|----------|-------|
| `test_extended_job_progress_type` | progress=50 | Stored as int | `test_models_phase10.py` |
| `test_extended_job_progress_range` | progress=0, 50, 100 | All accepted | `test_models_phase10.py` |
| `test_extended_job_progress_invalid` | progress=150 | Rejected | `test_models_phase10.py` |
| `test_extended_job_plugin_timings_type` | {"player": 145.5} | Stored as dict | `test_models_phase10.py` |
| `test_extended_job_warnings_type` | ["warning 1", "warning 2"] | Stored as list | `test_models_phase10.py` |

## 4.3 Serialization Tests

| Test | Expected | Files |
|------|----------|-------|
| `test_extended_job_response_to_json` | Serialize to JSON | Valid JSON output | `test_models_phase10.py` |
| `test_extended_job_response_from_json` | Parse from JSON | Correct object created | `test_models_phase10.py` |
| `test_extended_job_response_schema_valid` | Validate schema | Passes Pydantic validation | `test_models_phase10.py` |

## 4.4 Backward Compatibility Tests

| Test | Expected | Files |
|------|----------|-------|
| `test_phase9_job_response_still_works` | Legacy code creates JobResponse | No error | `test_models_phase10.py` |
| `test_extended_job_includes_all_phase9_fields` | All Phase 9 fields present | Unchanged | `test_models_phase10.py` |
| `test_extended_job_does_not_modify_phase9_model` | Phase 9 model untouched | Still works | `test_models_phase10.py` |

---

# 5. Inspector Service Tests

## 5.1 Initialization Tests

| Test | Expected | Files |
|------|----------|-------|
| `test_inspector_service_creates` | Instantiate | No error | `test_inspector_service.py` |
| `test_inspector_service_empty_state` | Fresh instance | No data | `test_inspector_service.py` |

## 5.2 Timing Tests

| Test | Expected | Files |
|------|----------|-------|
| `test_inspector_start_timing` | Call start_timing() | Timer started | `test_inspector_service.py` |
| `test_inspector_stop_timing` | Call stop_timing() | Timing returned (float) | `test_inspector_service.py` |
| `test_inspector_timing_accuracy` | Measure 100ms delay | Timing ≈ 100ms (±10ms) | `test_inspector_service.py` |
| `test_inspector_timing_stored` | Collect timings | All timings stored | `test_inspector_service.py` |
| `test_inspector_timing_monotonic` | Multiple calls | Uses monotonic clock | `test_inspector_service.py` |

## 5.3 Metadata Tests

| Test | Expected | Files |
|------|----------|-------|
| `test_inspector_metadata_extracted` | Call inspect() | Metadata returned | `test_inspector_service.py` |
| `test_inspector_metadata_fields` | Metadata has version, model, etc. | All fields present | `test_inspector_service.py` |
| `test_inspector_metadata_accuracy` | Compare to plugin | Metadata accurate | `test_inspector_service.py` |

## 5.4 Warning Tests

| Test | Expected | Files |
|------|----------|-------|
| `test_inspector_warning_recorded` | Plugin emits warning | Warning stored | `test_inspector_service.py` |
| `test_inspector_warnings_accumulated` | Multiple warnings | All stored | `test_inspector_service.py` |
| `test_inspector_warnings_not_deduplicated` | Same warning twice | Both stored | `test_inspector_service.py` |

---

# 6. Tool Runner Integration Tests

## 6.1 Execution Tests

| Test | Expected | Files |
|------|----------|-------|
| `test_tool_runner_executes_plugin` | Run plugin | Returns result | `test_tool_runner.py` |
| `test_tool_runner_measures_timing` | Run plugin | Timing recorded | `test_tool_runner.py` |
| `test_tool_runner_captures_warnings` | Plugin emits warning | Warning captured | `test_tool_runner.py` |

## 6.2 Message Emission Tests

| Test | Expected | Files |
|------|----------|-------|
| `test_tool_runner_emits_progress` | During execution | progress messages sent | `test_tool_runner.py` |
| `test_tool_runner_emits_frame` | After processing frame | frame messages sent | `test_tool_runner.py` |
| `test_tool_runner_emits_plugin_status` | After plugin complete | plugin_status message sent | `test_tool_runner.py` |
| `test_tool_runner_emits_warning` | Plugin warns | warning message sent | `test_tool_runner.py` |

## 6.3 Broadcast Integration Tests

| Test | Expected | Files |
|------|----------|-------|
| `test_tool_runner_broadcasts_to_connection_manager` | Execute job | All messages broadcast | `test_tool_runner.py` |
| `test_tool_runner_broadcasts_all_message_types` | Full execution | frame, progress, plugin_status all sent | `test_tool_runner.py` |
| `test_tool_runner_does_not_block_on_broadcast` | Send messages | Execution continues | `test_tool_runner.py` |

## 6.4 Error Handling Tests

| Test | Expected | Files |
|------|----------|-------|
| `test_tool_runner_handles_plugin_error` | Plugin raises | Error message sent, job continues | `test_tool_runner.py` |
| `test_tool_runner_handles_broadcast_error` | Broadcast fails | Logging, but execution continues | `test_tool_runner.py` |
| `test_tool_runner_handles_timing_error` | Timing fails | No crash | `test_tool_runner.py` |

---

# 7. Jobs Endpoint Integration Tests

## 7.1 Extended Endpoint Tests

| Test | Expected | Files |
|------|----------|-------|
| `test_get_extended_job_endpoint_exists` | GET /v1/jobs/{id}/extended | 200 OK | `test_api_jobs.py` |
| `test_get_extended_job_returns_model` | Endpoint called | ExtendedJobResponse returned | `test_api_jobs.py` |
| `test_get_extended_job_has_progress` | Job in progress | progress field populated | `test_api_jobs.py` |
| `test_get_extended_job_has_timings` | Job complete | plugin_timings populated | `test_api_jobs.py` |
| `test_get_extended_job_has_warnings` | Job had warnings | warnings field populated | `test_api_jobs.py` |

## 7.2 Backward Compatibility Tests

| Test | Expected | Files |
|------|----------|-------|
| `test_get_job_endpoint_still_works` | GET /v1/jobs/{id} | 200 OK (Phase 9) | `test_api_jobs.py` |
| `test_get_job_returns_job_response` | Legacy endpoint | JobResponse returned | `test_api_jobs.py` |
| `test_get_job_no_extended_fields` | Phase 9 model | No progress/timings/warnings | `test_api_jobs.py` |

## 7.3 Integration Tests

| Test | Expected | Files |
|------|----------|-------|
| `test_job_with_realtime_integration` | Start job → connect realtime → complete | Extended model populated | `test_api_jobs.py` |
| `test_job_progress_updates_in_extended_model` | progress messages emitted | Extended model reflects updates | `test_api_jobs.py` |
| `test_job_timings_update_in_extended_model` | plugin_status emitted | Timings reflect in extended model | `test_api_jobs.py` |

---

# 8. End-to-End Integration Tests

## 8.1 Full Flow Tests

| Test | Flow | Expected | Files |
|------|------|----------|-------|
| `test_e2e_start_job_to_realtime` | POST /v1/jobs → WS /v1/realtime | Both work together | `test_e2e.py` |
| `test_e2e_realtime_messages_arrive` | Start job → messages emitted → arrive at client | Messages in correct order | `test_e2e.py` |
| `test_e2e_extended_model_updates` | Progress messages → extended model reflects | Field values accurate | `test_e2e.py` |
| `test_e2e_multiple_clients_receive_same_messages` | 2+ WebSocket clients → same messages | All clients get messages | `test_e2e.py` |

## 8.2 Phase 9 Compatibility Tests

| Test | Expected | Files |
|------|----------|-------|
| `test_phase9_job_endpoint_still_works` | All Phase 9 tests pass | No regressions | `test_e2e.py` |
| `test_phase9_analysis_results_unchanged` | Job results same as Phase 9 | No breaking changes | `test_e2e.py` |
| `test_phase9_no_mandatory_realtime` | Can run jobs without WebSocket | Phase 9 mode works | `test_e2e.py` |

---

# 9. Performance Tests

## 9.1 Throughput Tests

| Test | Scenario | Expected | Files |
|------|----------|----------|-------|
| `test_message_throughput_1000_per_sec` | 1000 frames/sec | No dropped messages | `test_performance.py` |
| `test_broadcast_latency_p50` | Broadcast to 5 clients | p50 < 5ms | `test_performance.py` |
| `test_broadcast_latency_p95` | Broadcast to 5 clients | p95 < 50ms | `test_performance.py` |

## 9.2 Memory Tests

| Test | Expected | Files |
|------|----------|-------|
| `test_connection_manager_memory_leak` | 100 connect/disconnect cycles | No memory leak | `test_performance.py` |
| `test_message_queue_memory_bounded` | 1000+ messages | Queue size capped | `test_performance.py` |

---

# 10. Test Execution Plan

## 10.1 Local Development

```bash
# All Phase 10 backend tests
cd server
uv run pytest tests/phase10/ -v

# Specific test file
uv run pytest tests/phase10/test_realtime_endpoint.py -v

# Watch mode
uv run pytest tests/phase10/ -v --tb=short

# With coverage
uv run pytest tests/phase10/ -v --cov=app.realtime --cov-report=term-missing
```

## 10.2 CI Pipeline

```bash
# Full backend test suite (all phases)
uv run pytest tests/ -v --cov=app --cov-report=term-missing

# Phase 10 only
uv run pytest tests/phase10/ -v --cov=app.realtime --cov-report=html
```

---

# 11. Completion Criteria

Phase 10 backend testing is complete when:

✅ All endpoint tests pass
✅ All connection manager tests pass
✅ All message type tests pass
✅ All model tests pass
✅ All inspector service tests pass
✅ All tool runner tests pass
✅ All integration tests pass
✅ All Phase 9 tests still pass
✅ Coverage >80% on new code
✅ No memory leaks
✅ Message throughput >1000/sec
✅ Broadcast latency p95 <50ms

