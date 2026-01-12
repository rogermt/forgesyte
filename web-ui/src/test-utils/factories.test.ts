/**
 * Tests for mock factory functions
 * Ensures factories produce objects matching API schemas
 */

import { describe, it, expect } from "vitest";
import {
    createMockJob,
    createMockJobDone,
    createMockJobRunning,
    createMockJobError,
    createMockJobList,
    createMockPlugin,
    createMockPluginList,
    createMockFrameResult,
    createMockFrameResultList,
} from "./factories";

describe("Mock Factories", () => {
    describe("createMockJob", () => {
        it("should create job with default values", () => {
            const job = createMockJob();
            expect(job.job_id).toBeDefined();
            expect(job.status).toBe("queued");
            expect(job.plugin).toBe("motion_detector");
            expect(job.created_at).toBeDefined();
        });

        it("should allow overrides", () => {
            const job = createMockJob({ status: "done", plugin: "ocr" });
            expect(job.status).toBe("done");
            expect(job.plugin).toBe("ocr");
        });

        it("should have required fields", () => {
            const job = createMockJob();
            expect(job).toHaveProperty("job_id");
            expect(job).toHaveProperty("status");
            expect(job).toHaveProperty("plugin");
            expect(job).toHaveProperty("created_at");
        });
    });

    describe("createMockJobDone", () => {
        it("should create job with done status", () => {
            const job = createMockJobDone();
            expect(job.status).toBe("done");
            expect(job.completed_at).toBeDefined();
            expect(job.result).toBeDefined();
            expect(job.progress).toBe(100);
        });

        it("should have result data", () => {
            const job = createMockJobDone();
            expect(job.result).toHaveProperty("motion_detected");
            expect(job.result).toHaveProperty("confidence");
        });
    });

    describe("createMockJobRunning", () => {
        it("should create job with running status", () => {
            const job = createMockJobRunning();
            expect(job.status).toBe("running");
            expect(job.progress).toBeDefined();
            expect(job.progress).toBeGreaterThan(0);
        });
    });

    describe("createMockJobError", () => {
        it("should create job with error status", () => {
            const job = createMockJobError();
            expect(job.status).toBe("error");
            expect(job.error).toBeDefined();
            expect(job.completed_at).toBeDefined();
        });

        it("should have error message", () => {
            const job = createMockJobError();
            expect(job.error).toContain("Failed");
        });
    });

    describe("createMockJobList", () => {
        it("should create multiple jobs with different statuses", () => {
            const jobs = createMockJobList(4);
            expect(jobs).toHaveLength(4);
            expect(jobs[0].status).toBe("done");
            expect(jobs[1].status).toBe("running");
            expect(jobs[2].status).toBe("queued");
            expect(jobs[3].status).toBe("error");
        });

        it("should respect count parameter", () => {
            expect(createMockJobList(1)).toHaveLength(1);
            expect(createMockJobList(2)).toHaveLength(2);
            expect(createMockJobList(3)).toHaveLength(3);
        });
    });

    describe("createMockPlugin", () => {
        it("should create plugin with default values", () => {
            const plugin = createMockPlugin();
            expect(plugin.name).toBe("motion_detector");
            expect(plugin.description).toBeDefined();
            expect(plugin.version).toBeDefined();
            expect(plugin.inputs).toBeInstanceOf(Array);
            expect(plugin.outputs).toBeInstanceOf(Array);
        });

        it("should allow overrides", () => {
            const plugin = createMockPlugin({ name: "custom_plugin" });
            expect(plugin.name).toBe("custom_plugin");
        });

        it("should have config schema", () => {
            const plugin = createMockPlugin();
            expect(plugin.config_schema).toBeDefined();
        });
    });

    describe("createMockPluginList", () => {
        it("should create multiple plugins", () => {
            const plugins = createMockPluginList(2);
            expect(plugins).toHaveLength(2);
            expect(plugins[0].name).toBe("motion_detector");
            expect(plugins[1].name).toBe("object_detection");
        });

        it("should respect count parameter", () => {
            expect(createMockPluginList(1)).toHaveLength(1);
            expect(createMockPluginList(2)).toHaveLength(2);
        });
    });

    describe("createMockFrameResult", () => {
        it("should create frame result with required fields", () => {
            const frame = createMockFrameResult();
            expect(frame.frame_id).toBeDefined();
            expect(frame.plugin).toBeDefined();
            expect(frame.result).toBeDefined();
            expect(frame.processing_time_ms).toBeGreaterThan(0);
        });

        it("should allow overrides", () => {
            const frame = createMockFrameResult({ plugin: "ocr" });
            expect(frame.plugin).toBe("ocr");
        });

        it("should have result data", () => {
            const frame = createMockFrameResult();
            expect(frame.result).toHaveProperty("motion_detected");
        });
    });

    describe("createMockFrameResultList", () => {
        it("should create multiple frame results", () => {
            const frames = createMockFrameResultList(3);
            expect(frames).toHaveLength(3);
            frames.forEach((frame, index) => {
                expect(frame.frame_id).toContain(`frame-${String(index + 1).padStart(3, "0")}`);
            });
        });

        it("should have unique frame IDs", () => {
            const frames = createMockFrameResultList(5);
            const ids = frames.map((f) => f.frame_id);
            expect(new Set(ids).size).toBe(5);
        });
    });
});
