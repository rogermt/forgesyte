# Phase 10 — UI Test Matrix

Complete test matrix for Phase 10 UI components and integration.

All tests are RED → GREEN. MUST NOT break Phase 9 invariants.

---

# 1. RealtimeOverlay Tests

## 1.1 Smoke Tests

| Test | Expected | Files |
|------|----------|-------|
| `test_realtime_overlay_renders` | Component mounts without error | `RealtimeOverlay.spec.ts` |
| `test_realtime_overlay_visible` | When `isVisible={true}`, overlay appears | `RealtimeOverlay.spec.ts` |
| `test_realtime_overlay_hidden` | When `isVisible={false}`, overlay hidden | `RealtimeOverlay.spec.ts` |
| `test_realtime_overlay_close_button` | Close button exists and is clickable | `RealtimeOverlay.spec.ts` |

## 1.2 Real-Time Tests

| Test | Trigger | Expected | Files |
|------|---------|----------|-------|
| `test_realtime_overlay_frame_updates` | `frame` message | Frame viewer displays new frame | `RealtimeOverlay.spec.ts` |
| `test_realtime_overlay_multiple_frames` | Multiple `frame` messages | Frames update without flicker | `RealtimeOverlay.spec.ts` |
| `test_realtime_overlay_clears_on_restart` | Job restart (new job_id) | Overlay state clears | `RealtimeOverlay.spec.ts` |
| `test_realtime_overlay_error_state` | `error` message | Error banner shown | `RealtimeOverlay.spec.ts` |
| `test_realtime_overlay_disconnect` | WebSocket disconnect | Overlay shows "Reconnecting..." | `RealtimeOverlay.spec.ts` |
| `test_realtime_overlay_reconnect` | WebSocket reconnects | Overlay hides "Reconnecting..." | `RealtimeOverlay.spec.ts` |

## 1.3 Component Integration Tests

| Test | Expected | Files |
|------|----------|-------|
| `test_realtime_overlay_renders_progress_bar` | ProgressBar child component visible | `RealtimeOverlay.spec.ts` |
| `test_realtime_overlay_renders_plugin_inspector` | PluginInspector child component visible | `RealtimeOverlay.spec.ts` |
| `test_realtime_overlay_all_children_coordinate` | Progress, frame, inspector all update together | `RealtimeOverlay.spec.ts` |

---

# 2. ProgressBar Tests

## 2.1 Smoke Tests

| Test | Expected | Files |
|------|----------|-------|
| `test_progress_bar_renders` | Component mounts without error | `ProgressBar.spec.ts` |
| `test_progress_bar_has_correct_id` | Element with `id="progress-bar"` exists | `ProgressBar.spec.ts` |
| `test_progress_bar_initial_state` | Initial progress is 0 | `ProgressBar.spec.ts` |

## 2.2 Update Tests

| Test | Trigger | Expected | Files |
|------|---------|----------|-------|
| `test_progress_bar_updates_on_message` | `progress` message (50%) | Bar fill width is 50% | `ProgressBar.spec.ts` |
| `test_progress_bar_smooth_animation` | Progress 0 → 100 | Smooth CSS animation (no jumping) | `ProgressBar.spec.ts` |
| `test_progress_bar_label_updates` | `progress` message with `stage` | Label text updates | `ProgressBar.spec.ts` |
| `test_progress_bar_multiple_updates` | Sequential `progress` messages | Bar updates each time | `ProgressBar.spec.ts` |

## 2.3 Edge Cases

| Test | Input | Expected | Files |
|------|-------|----------|-------|
| `test_progress_bar_zero` | progress=0 | Bar width 0%, shows "0%" | `ProgressBar.spec.ts` |
| `test_progress_bar_complete` | progress=100 | Bar width 100%, shows "Complete" | `ProgressBar.spec.ts` |
| `test_progress_bar_negative` | progress=-5 | Clamped to 0 | `ProgressBar.spec.ts` |
| `test_progress_bar_over_100` | progress=150 | Clamped to 100 | `ProgressBar.spec.ts` |
| `test_progress_bar_non_integer` | progress=42.5 | Displayed as 42.5% | `ProgressBar.spec.ts` |

## 2.4 Accessibility Tests

| Test | Expected | Files |
|------|----------|-------|
| `test_progress_bar_aria_progressbar` | `role="progressbar"` present | `ProgressBar.spec.ts` |
| `test_progress_bar_aria_values` | `aria-valuenow`, `aria-valuemin`, `aria-valuemax` | `ProgressBar.spec.ts` |
| `test_progress_bar_aria_label` | `aria-label` or `aria-labelledby` | `ProgressBar.spec.ts` |

---

# 3. PluginInspector Tests

## 3.1 Smoke Tests

| Test | Expected | Files |
|------|----------|-------|
| `test_plugin_inspector_renders` | Component mounts without error | `PluginInspector.spec.ts` |
| `test_plugin_inspector_has_correct_id` | Element with `id="plugin-inspector"` exists | `PluginInspector.spec.ts` |
| `test_plugin_inspector_empty_state` | When no data, shows "No data available" | `PluginInspector.spec.ts` |

## 3.2 Timing Display Tests

| Test | Trigger | Expected | Files |
|------|---------|----------|-------|
| `test_plugin_inspector_displays_timings` | `pluginTimings` prop with data | Timings displayed in ms | `PluginInspector.spec.ts` |
| `test_plugin_inspector_timing_bar_chart` | `pluginTimings` with multiple plugins | Bar chart shows all plugins | `PluginInspector.spec.ts` |
| `test_plugin_inspector_timing_scale` | Plugin A: 100ms, B: 50ms | B bar is half size of A | `PluginInspector.spec.ts` |
| `test_plugin_inspector_timing_labels` | `pluginTimings` | Label shows exact ms value | `PluginInspector.spec.ts` |

## 3.3 Status Badge Tests

| Test | Trigger | Expected | Files |
|------|---------|----------|-------|
| `test_plugin_inspector_status_started` | `status: 'started'` | Badge shows "⏳ Started" (or icon) | `PluginInspector.spec.ts` |
| `test_plugin_inspector_status_running` | `status: 'running'` | Badge shows "⚙️ Running" with animation | `PluginInspector.spec.ts` |
| `test_plugin_inspector_status_completed` | `status: 'completed'` | Badge shows "✓ Completed" | `PluginInspector.spec.ts` |
| `test_plugin_inspector_status_failed` | `status: 'failed'` | Badge shows "✗ Failed" in red | `PluginInspector.spec.ts` |
| `test_plugin_inspector_status_colors` | Various statuses | Colors correspond to status | `PluginInspector.spec.ts` |

## 3.4 Warning Display Tests

| Test | Trigger | Expected | Files |
|------|---------|----------|-------|
| `test_plugin_inspector_warning_displays` | 1 warning message | Warning appears in list | `PluginInspector.spec.ts` |
| `test_plugin_inspector_warnings_accumulate` | Multiple `warning` messages | List grows; old warnings remain | `PluginInspector.spec.ts` |
| `test_plugin_inspector_warnings_not_duplicated` | Same warning twice | Both shown (not deduplicated) | `PluginInspector.spec.ts` |
| `test_plugin_inspector_warnings_scrollable` | >10 warnings | List is scrollable | `PluginInspector.spec.ts` |
| `test_plugin_inspector_warning_format` | Warning message | Shows plugin name + message | `PluginInspector.spec.ts` |
| `test_plugin_inspector_warnings_clear` | Job restart | Warning list clears | `PluginInspector.spec.ts` |

## 3.5 Real-Time Update Tests

| Test | Trigger | Expected | Files |
|------|---------|----------|-------|
| `test_plugin_inspector_timing_update` | `plugin_status` message | Timing updates immediately | `PluginInspector.spec.ts` |
| `test_plugin_inspector_status_update` | `plugin_status` message | Status badge updates immediately | `PluginInspector.spec.ts` |
| `test_plugin_inspector_multiple_plugins` | Multiple `plugin_status` messages | All plugins display separately | `PluginInspector.spec.ts` |

---

# 4. RealtimeClient Tests

## 4.1 Connection Tests

| Test | Expected | Files |
|------|----------|-------|
| `test_realtime_client_connects` | `.connect()` opens WebSocket | Connection established | `RealtimeClient.spec.ts` |
| `test_realtime_client_disconnect` | `.disconnect()` closes WebSocket | Connection closed | `RealtimeClient.spec.ts` |
| `test_realtime_client_is_connected` | After connect, `isConnected()` returns true | Boolean correct | `RealtimeClient.spec.ts` |
| `test_realtime_client_endpoint_correct` | Connection URL is correct | `/v1/realtime` reached | `RealtimeClient.spec.ts` |

## 4.2 Message Parsing Tests

| Test | Input | Expected | Files |
|------|-------|----------|-------|
| `test_realtime_client_parses_frame` | Valid `frame` message JSON | Message object returned | `RealtimeClient.spec.ts` |
| `test_realtime_client_parses_progress` | Valid `progress` message JSON | Message object returned | `RealtimeClient.spec.ts` |
| `test_realtime_client_parses_plugin_status` | Valid `plugin_status` message JSON | Message object returned | `RealtimeClient.spec.ts` |
| `test_realtime_client_parses_warning` | Valid `warning` message JSON | Message object returned | `RealtimeClient.spec.ts` |
| `test_realtime_client_parses_all_types` | All 8 message types | Each parses correctly | `RealtimeClient.spec.ts` |

## 4.3 Handler Tests

| Test | Trigger | Expected | Files |
|------|---------|----------|-------|
| `test_realtime_client_calls_on_message` | Incoming message | Handler called with message | `RealtimeClient.spec.ts` |
| `test_realtime_client_calls_on_error` | Connection error | Error handler called | `RealtimeClient.spec.ts` |
| `test_realtime_client_calls_on_connection_change` | Connect/disconnect | Handler called with boolean | `RealtimeClient.spec.ts` |

## 4.4 Reconnection Tests

| Test | Trigger | Expected | Files |
|------|---------|----------|-------|
| `test_realtime_client_reconnects` | Server drops, comes back | Reconnects automatically | `RealtimeClient.spec.ts` |
| `test_realtime_client_backoff_timing` | Reconnect attempts | Delays: 1s, 2s, 4s, 8s, 16s | `RealtimeClient.spec.ts` |
| `test_realtime_client_backoff_resets` | Successful reconnect | Next failure starts at 1s | `RealtimeClient.spec.ts` |
| `test_realtime_client_max_reconnect_attempts` | 5 failed reconnects | Stops and calls error handler | `RealtimeClient.spec.ts` |

## 4.5 Error Handling Tests

| Test | Input | Expected | Files |
|------|-------|----------|-------|
| `test_realtime_client_invalid_json` | Malformed JSON | Error logged, connection continues | `RealtimeClient.spec.ts` |
| `test_realtime_client_missing_field` | Message missing `type` | Error logged, message ignored | `RealtimeClient.spec.ts` |
| `test_realtime_client_unknown_type` | Message with unknown `type` | No error, silently ignored | `RealtimeClient.spec.ts` |
| `test_realtime_client_network_error` | Network error during receive | Error handler called | `RealtimeClient.spec.ts` |

---

# 5. RealtimeContext Tests

## 5.1 State Update Tests

| Test | Action | Expected | Files |
|------|--------|----------|-------|
| `test_realtime_context_stores_frame` | Dispatch `frame` message | State.currentFrame updated | `RealtimeContext.spec.ts` |
| `test_realtime_context_stores_progress` | Dispatch `progress` message | State.progress updated | `RealtimeContext.spec.ts` |
| `test_realtime_context_stores_timing` | Dispatch `plugin_status` message | State.pluginTimings updated | `RealtimeContext.spec.ts` |
| `test_realtime_context_stores_warning` | Dispatch `warning` message | State.warnings appended | `RealtimeContext.spec.ts` |
| `test_realtime_context_stores_error` | Dispatch `error` message | State.errors appended | `RealtimeContext.spec.ts` |

## 5.2 Multiple Update Tests

| Test | Actions | Expected | Files |
|------|---------|----------|-------|
| `test_realtime_context_accumulates_warnings` | Multiple `warning` dispatches | All warnings stored | `RealtimeContext.spec.ts` |
| `test_realtime_context_accumulates_errors` | Multiple `error` dispatches | All errors stored | `RealtimeContext.spec.ts` |
| `test_realtime_context_overwrites_frame` | Multiple `frame` dispatches | Latest frame stored | `RealtimeContext.spec.ts` |
| `test_realtime_context_overwrites_progress` | Multiple `progress` dispatches | Latest progress stored | `RealtimeContext.spec.ts` |

## 5.3 Lifecycle Tests

| Test | Trigger | Expected | Files |
|------|---------|----------|-------|
| `test_realtime_context_initial_state` | Provider mount | State has correct defaults | `RealtimeContext.spec.ts` |
| `test_realtime_context_reset` | New job starts | State resets to initial | `RealtimeContext.spec.ts` |
| `test_realtime_context_cleanup` | Provider unmount | No memory leaks | `RealtimeContext.spec.ts` |

## 5.4 Hook Tests

| Test | Expected | Files |
|------|----------|-------|
| `test_use_realtime_hook_returns_state` | Hook call | Returns current state | `useRealtime.spec.ts` |
| `test_use_realtime_hook_updates` | State change | Hook subscribers notified | `useRealtime.spec.ts` |
| `test_use_realtime_hook_outside_provider` | Hook called outside provider | Throws error | `useRealtime.spec.ts` |

---

# 6. Storybook Tests

## 6.1 Story Rendering Tests

| Story | Expected | Files |
|-------|----------|-------|
| `Idle` | Renders without data | `RealtimeOverlay.stories.tsx` |
| `Loading` | Progress 10%, "Starting..." | `RealtimeOverlay.stories.tsx` |
| `InProgress` | Progress 50%, "Processing..." | `RealtimeOverlay.stories.tsx` |
| `Completing` | Progress 95%, "Finishing..." | `RealtimeOverlay.stories.tsx` |
| `Complete` | Progress 100%, "Done" | `RealtimeOverlay.stories.tsx` |
| `WithWarnings` | Shows warning list | `RealtimeOverlay.stories.tsx` |
| `WithError` | Shows error banner | `RealtimeOverlay.stories.tsx` |
| `WithTimings` | Shows plugin inspector | `RealtimeOverlay.stories.tsx` |

## 6.2 Story Content Tests

| Test | Story | Expected | Files |
|------|-------|----------|-------|
| `test_story_idle_no_data` | Idle | No frame, no warnings, progress=0 | `RealtimeOverlay.stories.tsx` |
| `test_story_loading_spinner` | Loading | Spinner animation visible | `RealtimeOverlay.stories.tsx` |
| `test_story_warnings_list` | WithWarnings | 3+ sample warnings displayed | `RealtimeOverlay.stories.tsx` |
| `test_story_error_prominent` | WithError | Error message bold/red | `RealtimeOverlay.stories.tsx` |

---

# 7. Integration Tests

## 7.1 End-to-End Flow

| Test | Flow | Expected | Files |
|------|------|----------|-------|
| `test_e2e_job_to_overlay` | Start job → connect realtime → frames arrive | Overlay updates live | `e2e.spec.ts` |
| `test_e2e_progress_flow` | Start job → progress messages → complete | Progress bar 0→100 | `e2e.spec.ts` |
| `test_e2e_plugin_inspector_flow` | Start job → plugin_status messages → complete | Timings/status update | `e2e.spec.ts` |
| `test_e2e_warning_flow` | Start job → warning messages → accumulate | Warnings display | `e2e.spec.ts` |
| `test_e2e_full_stack` | Full job execution | All components update together | `e2e.spec.ts` |

## 7.2 Phase 9 Compatibility

| Test | Expected | Files |
|------|----------|-------|
| `test_phase9_device_selector_still_works` | `#device-selector` unchanged | Works as before | `e2e.spec.ts` |
| `test_phase9_control_panel_still_works` | `#toggle-*` still work | Works as before | `e2e.spec.ts` |
| `test_phase9_fps_slider_still_works` | `#fps-slider` still works | Works as before | `e2e.spec.ts` |
| `test_phase9_no_regressions` | All Phase 9 tests pass | No breaking changes | `e2e.spec.ts` |

---

# 8. Test Execution Plan

## 8.1 Local Development

```bash
# All UI tests
npm run test -- --run tests/phase10/

# Specific component
npm run test -- --run tests/phase10/ProgressBar.spec.ts

# Watch mode
npm run test tests/phase10/
```

## 8.2 CI Pipeline

```bash
# Full test suite (all phases)
npm run test -- --run

# Coverage report
npm run test -- --run --coverage
```

---

# 9. Completion Criteria

Phase 10 UI testing is complete when:

✅ All smoke tests pass
✅ All real-time update tests pass
✅ All edge case tests pass
✅ All accessibility tests pass
✅ All integration tests pass
✅ All Phase 9 tests still pass
✅ No flaky tests (100% deterministic)
✅ Coverage >80% on new code

