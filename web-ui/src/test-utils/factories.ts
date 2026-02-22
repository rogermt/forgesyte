/**
 * Mock factory functions for generating test data from API schemas
 *
 * These factories create mock objects that match actual server API responses.
 * Use these instead of hand-written mock objects to ensure test data matches reality.
 *
 * Sources:
 * - Job types: server/app/models.py:46 (JobResponse)
 * - Plugin types: server/app/models.py:78 (PluginMetadata)
 * - Frame results: web-ui/src/hooks/useWebSocket.ts:21 (FrameResult)
 */

import { Job, Plugin } from "../api/client";
import { FrameResult } from "../hooks/useWebSocket";

/**
 * Create a mock Job object matching JobResponse schema
 *
 * Usage:
 * ```typescript
 * const job = createMockJob(); // All defaults
 * const doneJob = createMockJob({ status: "done" });
 * const customJob = createMockJob({ job_id: "custom-123" });
 * ```
 */
export function createMockJob(overrides?: Partial<Job>): Job {
    const defaults: Job = {
        job_id: "550e8400-e29b-41d4-a716-446655440000",
        status: "pending",
        plugin_id: "ocr",
        tool: "analyze",
        created_at: "2026-01-12T21:00:00Z",
        updated_at: "2026-01-12T21:00:00Z",
        results: undefined,
        error_message: undefined,
        progress: 0,
    };

    return { ...defaults, ...overrides };
}

/**
 * Create a mock completed Job (status: "done")
 *
 * Usage:
 * ```typescript
 * const completedJob = createMockJobDone();
 * const customDone = createMockJobDone({ plugin: "object_detection" });
 * ```
 */
export function createMockJobDone(overrides?: Partial<Job>): Job {
    return createMockJob({
        status: "completed",
        updated_at: "2026-01-12T21:00:30Z",
        results: {
            text: "Extracted text from image",
            confidence: 0.95,
        },
        progress: 100,
        ...overrides,
    });
}

/**
 * Create a mock running Job (status: "running")
 *
 * Usage:
 * ```typescript
 * const runningJob = createMockJobRunning();
 * const customRunning = createMockJobRunning({ progress: 75 });
 * ```
 */
export function createMockJobRunning(overrides?: Partial<Job>): Job {
    return createMockJob({
        status: "running",
        progress: 45,
        ...overrides,
    });
}

/**
 * Create a mock failed Job (status: "error")
 *
 * Usage:
 * ```typescript
 * const failedJob = createMockJobError();
 * const customError = createMockJobError({ error: "Custom error message" });
 * ```
 */
export function createMockJobError(overrides?: Partial<Job>): Job {
    return createMockJob({
        status: "failed",
        updated_at: "2026-01-12T20:05:00Z",
        error_message: "Failed to process image: invalid format",
        progress: null,
        ...overrides,
    });
}

/**
 * Create a list of mock Jobs with various statuses
 *
 * Usage:
 * ```typescript
 * const jobs = createMockJobList(); // 4 jobs with different statuses
 * const customJobs = createMockJobList(2); // 2 jobs
 * ```
 */
export function createMockJobList(count: number = 4): Job[] {
    const jobs: Job[] = [createMockJobDone()];

    if (count >= 2) {
        jobs.push(createMockJobRunning());
    }
    if (count >= 3) {
        jobs.push(createMockJob({ status: "pending" }));
    }
    if (count >= 4) {
        jobs.push(createMockJobError());
    }

    return jobs.slice(0, count);
}

/**
 * Create a mock Plugin object matching PluginMetadata schema
 *
 * Usage:
 * ```typescript
 * const plugin = createMockPlugin();
 * const customPlugin = createMockPlugin({ name: "custom_detector" });
 * ```
 */
export function createMockPlugin(overrides?: Partial<Plugin>): Plugin {
    const defaults: Plugin = {
        name: "motion_detector",
        description: "Detects motion in video frames and returns coordinates",
        version: "1.0.0",
        inputs: ["image"],
        outputs: ["json"],
        permissions: ["read:images"],
        config_schema: {
            sensitivity: {
                type: "number",
                default: 0.5,
                description: "Motion detection sensitivity (0-1)",
            },
        },
    };

    return { ...defaults, ...overrides };
}

/**
 * Create a list of mock Plugins
 *
 * Usage:
 * ```typescript
 * const plugins = createMockPluginList(); // 2 default plugins
 * const customPlugins = createMockPluginList(3);
 * ```
 */
export function createMockPluginList(count: number = 2): Plugin[] {
    const plugins: Plugin[] = [createMockPlugin()];

    if (count >= 2) {
        plugins.push(
            createMockPlugin({
                name: "object_detection",
                description: "Detects objects in images using YOLO",
                version: "2.1.0",
                config_schema: {
                    model: {
                        type: "string",
                        default: "yolov8",
                        description: "YOLO model version",
                    },
                },
            })
        );
    }

    return plugins.slice(0, count);
}

/**
 * Create a mock FrameResult from WebSocket
 *
 * Usage:
 * ```typescript
 * const frameResult = createMockFrameResult();
 * const customFrame = createMockFrameResult({ plugin: "object_detection" });
 * ```
 */
export function createMockFrameResult(
    overrides?: Partial<FrameResult>
): FrameResult {
    const defaults: FrameResult = {
        frame_id: "frame-001",
        plugin: "motion_detector",
        result: {
            motion_detected: true,
            confidence: 0.87,
            regions: [
                {
                    x: 250,
                    y: 100,
                    width: 150,
                    height: 200,
                },
            ],
        },
        processing_time_ms: 45,
    };

    return { ...defaults, ...overrides };
}

/**
 * Create a list of mock FrameResults
 *
 * Usage:
 * ```typescript
 * const frames = createMockFrameResultList(3);
 * ```
 */
export function createMockFrameResultList(count: number = 1): FrameResult[] {
    const frames: FrameResult[] = [];

    for (let i = 0; i < count; i++) {
        frames.push(
            createMockFrameResult({
                frame_id: `frame-${String(i + 1).padStart(3, "0")}`,
                processing_time_ms: 40 + Math.random() * 20,
            })
        );
    }

    return frames;
}
