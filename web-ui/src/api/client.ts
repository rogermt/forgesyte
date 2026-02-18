/**
 * API client for ForgeSyte Server
 *
 * Uses environment variables:
 * - VITE_API_URL: Full API endpoint URL (default: /v1)
 * - VITE_API_KEY: Optional API authentication key
 */

import type {
    PluginManifest,
    ToolExecutionResponse,
} from "../types/plugin";

const API_BASE =
    import.meta.env.VITE_API_URL || import.meta.env.VITE_API_BASE || "/v1";
const API_KEY = import.meta.env.VITE_API_KEY;

export interface Plugin {
    name: string;
    description: string;
    version: string;
    inputs: string[];
    outputs: string[];
    permissions: string[];
    config_schema?: Record<string, unknown>;
}

export interface Job {
    job_id: string;
    status: "queued" | "running" | "done" | "error" | "not_found";
    plugin: string;
    result?: Record<string, unknown>;
    error?: string | null;
    created_at: string;
    completed_at?: string | null;
    progress?: number | null;
}

export interface AnalysisResult {
    job_id: string;
    status: string;
}

export class ForgeSyteAPIClient {
    private baseUrl: string;
    private apiKey?: string;

    constructor(baseUrl: string = API_BASE, apiKey: string | undefined = API_KEY) {
        this.baseUrl = baseUrl;
        this.apiKey = apiKey;
    }

    private async fetch(
        endpoint: string,
        options?: RequestInit
    ): Promise<Record<string, unknown>> {
        const url = `${this.baseUrl}${endpoint}`;
        const headers: HeadersInit = {
            "Content-Type": "application/json",
            ...((options?.headers as Record<string, string>) || {}),
        };

        if (this.apiKey) {
            headers["X-API-Key"] = this.apiKey;
        }

        const response = await fetch(url, {
            ...options,
            headers,
        });

        // Check content type to detect HTML error pages (e.g., 404)
        const contentType = response.headers.get("content-type");
        const isJson = contentType && contentType.includes("application/json");

        if (!response.ok) {
            if (isJson) {
                const errorData = await response.json();
                throw new Error(errorData.detail || `API error: ${response.status} ${response.statusText}`);
            } else {
                // Server returned non-JSON (e.g., HTML error page, tunnel redirect)
                // Don't include raw HTML in error message
                if (response.status === 511) {
                    throw new Error("Server unavailable. Please ensure the server is running and try again.");
                } else if (response.status >= 500) {
                    throw new Error(`Server error (HTTP ${response.status}). Please try again later.`);
                } else {
                    throw new Error(`Server returned non-JSON response (HTTP ${response.status}).`);
                }
            }
        }

        if (!isJson) {
            // Success response but not JSON - likely an error from tunnel/proxy
            throw new Error("Server unavailable. Please ensure the server is running and try again.");
        }

        return response.json();
    }

    async getPlugins(): Promise<Plugin[]> {
        // Phase 11: /v1/plugins returns array directly (not wrapped in object)
        const result = (await this.fetch("/plugins")) as unknown;
        if (Array.isArray(result)) {
            return result as Plugin[];
        }
        // Fallback for older API versions
        return (result as Record<string, unknown>).plugins as Plugin[];
    }

    async analyzeImage(
        file: File,
        plugin: string,
        tool?: string
    ): Promise<AnalysisResult> {
        const formData = new FormData();
        formData.append("file", file);

        const url = new URL(`${this.baseUrl}/analyze`, window.location.origin);
        url.searchParams.append("plugin", plugin);
        if (tool) {
            url.searchParams.append("tool", tool);
        }

        const headers: HeadersInit = {};

        if (this.apiKey) {
            headers["X-API-Key"] = this.apiKey;
        }

        const response = await fetch(url.toString(), {
            method: "POST",
            headers,
            body: formData,
        });

        if (!response.ok) {
            throw new Error(
                `API error: ${response.status} ${response.statusText}`
            );
        }

        return response.json() as Promise<AnalysisResult>;
    }

    async getJob(jobId: string): Promise<Job> {
        const result = (await this.fetch(`/jobs/${jobId}`)) as Record<
            string,
            unknown
        >;
        return result.job ? (result.job as unknown as Job) : (result as unknown as Job);
    }

    async listJobs(
        limit = 10,
        skip = 0,
        status?: string
    ): Promise<Job[]> {
        const searchParams = new URLSearchParams();
        searchParams.append("limit", limit.toString());
        searchParams.append("skip", skip.toString());
        if (status) {
            searchParams.append("status", status);
        }

        const query = searchParams.toString();
        const result = (await this.fetch(
            `/jobs${query ? `?${query}` : ""}`
        )) as Record<string, unknown>;
        return result.jobs as Job[];
    }

    async cancelJob(
        jobId: string
    ): Promise<{ status: string; job_id: string }> {
        const result = (await this.fetch(`/jobs/${jobId}`, {
            method: "DELETE",
        })) as Record<string, unknown>;
        return {
            status: (result.status as string) || "cancelled",
            job_id: (result.job_id as string) || jobId,
        };
    }

    async getHealth(): Promise<{
        status: string;
        plugins_loaded: number;
        version: string;
    }> {
        return this.fetch("/health") as Promise<{
            status: string;
            plugins_loaded: number;
            version: string;
        }>;
    }

    async pollJob(
        jobId: string,
        intervalMs = 500,
        timeoutMs = 60000
    ): Promise<Job> {
        const startTime = Date.now();

        while (Date.now() - startTime < timeoutMs) {
            const job = await this.getJob(jobId);

            if (job.status === "done" || job.status === "error") {
                return job;
            }

            await new Promise((resolve) =>
                setTimeout(resolve, intervalMs)
            );
        }

        throw new Error("Job polling timed out");
    }

    async getPluginManifest(pluginId: string): Promise<PluginManifest> {
        // Phase 11: Use canonical /plugins/{pluginId}/manifest endpoint
        // (baseUrl already includes /v1)
        return this.fetch(
            `/plugins/${pluginId}/manifest`
        ) as unknown as Promise<PluginManifest>;
    }

    async runPluginTool(
        pluginId: string,
        toolName: string,
        args: Record<string, unknown>
    ): Promise<ToolExecutionResponse> {
        return this.fetch(`/plugins/${pluginId}/tools/${toolName}/run`, {
            method: "POST",
            body: JSON.stringify({ args }),
        }) as unknown as Promise<ToolExecutionResponse>;
    }

    // Video job submission
    async submitVideo(
        file: File,
        pipelineId: string = "ocr_only",
        onProgress?: (percent: number) => void
    ): Promise<{ job_id: string }> {
        return new Promise((resolve, reject) => {
            const xhr = new XMLHttpRequest();
            const url = new URL(`${this.baseUrl}/video/submit`, window.location.origin);
            url.searchParams.append("pipeline_id", pipelineId);
            xhr.open("POST", url.toString());

            if (this.apiKey) {
                xhr.setRequestHeader("X-API-Key", this.apiKey);
            }

            xhr.upload.onprogress = (event) => {
                if (!onProgress || !event.lengthComputable) return;
                const percent = (event.loaded / event.total) * 100;
                onProgress(percent);
            };

            xhr.onload = () => {
                if (xhr.status >= 200 && xhr.status < 300) {
                    try {
                        resolve(JSON.parse(xhr.responseText));
                    } catch (e) {
                        reject(new Error("Invalid server response."));
                    }
                } else {
                    reject(new Error(`Upload failed with status ${xhr.status}.`));
                }
            };

            xhr.onerror = () => reject(new Error("Network error during upload."));

            const formData = new FormData();
            formData.append("file", file);
            xhr.send(formData);
        });
    }

    // Video job status
    async getVideoJobStatus(jobId: string): Promise<{
        job_id: string;
        status: "pending" | "running" | "completed" | "failed";
        progress: number;
        created_at: string;
        updated_at: string;
    }> {
        const result = await this.fetch(`/video/status/${jobId}`);
        return result as {
            job_id: string;
            status: "pending" | "running" | "completed" | "failed";
            progress: number;
            created_at: string;
            updated_at: string;
        };
    }

    // Video job results
    async getVideoJobResults(jobId: string): Promise<{
        job_id: string;
        results: {
            text?: string;
            detections?: Array<{
                label: string;
                confidence: number;
                bbox: number[];
            }>;
        };
        created_at: string;
        updated_at: string;
    }> {
        const result = await this.fetch(`/video/results/${jobId}`);
        return result as {
            job_id: string;
            results: {
                text?: string;
                detections?: Array<{
                    label: string;
                    confidence: number;
                    bbox: number[];
                }>;
            };
            created_at: string;
            updated_at: string;
        };
    }
}

export const apiClient = new ForgeSyteAPIClient();
export default apiClient;
