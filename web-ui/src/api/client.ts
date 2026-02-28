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
    status: "pending" | "running" | "completed" | "failed";  // Issue #212: Aligned with server enum
    plugin_id?: string;  // v0.9.2: plugin_id from server
    tool?: string;  // v0.9.2: tool from server (single-tool)
    tool_list?: string[];  // v0.9.4: tool_list from server (multi-tool)
    job_type?: "image" | "image_multi" | "video" | "video_multi";  // v0.9.8: added video_multi
    plugin?: string;  // Legacy: kept for backward compatibility
    results?: Record<string, unknown>;  // v0.9.2: results from server
    result?: Record<string, unknown>;  // Legacy: kept for backward compatibility
    error_message?: string | null;  // v0.9.2: error_message from server
    error?: string | null;  // Legacy: kept for backward compatibility
    created_at: string;
    updated_at?: string;  // v0.9.2: updated_at from server
    completed_at?: string | null;  // Legacy
    progress?: number | null;
    // v0.9.7: Multi-tool video job metadata
    current_tool?: string | null;  // Current tool being processed
    tools_total?: number | null;  // Total number of tools
    tools_completed?: number | null;  // Number of tools completed
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

    async getJob(jobId: string): Promise<Job> {
        // v0.9.2: Use unified /v1/jobs/{id} endpoint for both image and video jobs
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

            // Issue #212: Check for server status values (completed/failed)
            if (job.status === "completed" || job.status === "failed") {
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

    // v0.9.2: Image job submission using unified job system
    // v0.9.4: Updated to accept array of tools for multi-tool support
    // v0.9.8: Added useLogicalId parameter for logical_tool_id support
    async submitImage(
        file: File,
        pluginId: string,
        tools: string | string[],  // v0.9.4: Accept single tool or array of tools
        onProgress?: (percent: number) => void,
        useLogicalId = false  // v0.9.8: Set true to send logical_tool_id instead of tool
    ): Promise<{ job_id: string }> {
        return new Promise((resolve, reject) => {
            const xhr = new XMLHttpRequest();
            const url = new URL(`${this.baseUrl}/image/submit`, window.location.origin);
            url.searchParams.append("plugin_id", pluginId);
            
            // v0.9.8: Use logical_tool_id or tool based on flag
            const paramName = useLogicalId ? "logical_tool_id" : "tool";
            
            // v0.9.4: Support multiple tools - append each as separate query param
            if (Array.isArray(tools)) {
                tools.forEach(t => url.searchParams.append(paramName, t));
            } else {
                url.searchParams.append(paramName, tools);
            }
            
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

    // Video job submission
    // v0.9.7: Supports logical_tool_id for capability-based resolution
    // v0.9.8: Supports array of tools for multi-tool video analysis
    async submitVideo(
        file: File,
        pluginId: string,
        toolOrLogicalId: string | string[],  // v0.9.8: Accept single or array
        onProgress?: (percent: number) => void,
        useLogicalId = false  // v0.9.7: Set true to send logical_tool_id instead of tool
    ): Promise<{ job_id: string }> {
        return new Promise((resolve, reject) => {
            const xhr = new XMLHttpRequest();
            const url = new URL(`${this.baseUrl}/video/submit`, window.location.origin);
            url.searchParams.append("plugin_id", pluginId);

            // v0.9.8: Use logical_tool_id or tool based on flag
            const paramName = useLogicalId ? "logical_tool_id" : "tool";

            // v0.9.7: Send as logical_tool_id or tool based on flag
            if (Array.isArray(toolOrLogicalId)) {
                // v0.9.8: Multiple tools - append each as separate query param
                toolOrLogicalId.forEach(t => url.searchParams.append(paramName, t));
            } else {
                url.searchParams.append(paramName, toolOrLogicalId);
            }
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

    // v0.10.1: Video upload-only endpoint for deterministic tool-locking flow
    // Uploads video and returns {video_path} - no job submission
    async submitVideoUpload(
        file: File,
        pluginId: string,
        onProgress?: (percent: number) => void
    ): Promise<{ video_path: string }> {
        return new Promise((resolve, reject) => {
            const xhr = new XMLHttpRequest();
            const url = new URL(`${this.baseUrl}/video/upload`, window.location.origin);
            url.searchParams.append("plugin_id", pluginId);

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

    // v0.10.1: Submit job for already-uploaded video using lockedTools
    // Called after user clicks "Run Job" button
    async submitVideoJob(
        pluginId: string,
        videoPath: string,
        lockedTools: string[]
    ): Promise<{ job_id: string }> {
        const result = await this.fetch("/video/job", {
            method: "POST",
            body: JSON.stringify({
                plugin_id: pluginId,
                video_path: videoPath,
                lockedTools,
            }),
        });
        return result as unknown as { job_id: string };
    }
}

export const apiClient = new ForgeSyteAPIClient();
export default apiClient;

// v0.9.2: Utility function to filter tools by input type
export function filterToolsByInputType(
    tools: Array<{ id: string; inputs?: string[]; input_types?: string[] }>,
    inputType: "image" | "video"
): Array<{ id: string; inputs?: string[]; input_types?: string[] }> {
    return tools.filter((tool) => {
        const inputs = tool.inputs || tool.input_types || [];
        if (inputType === "image") {
            return inputs.some((i) =>
                i === "image_bytes" || i === "image_base64" || i === "image"
            );
        } else if (inputType === "video") {
            return inputs.some((i) =>
                i === "video_path" || i === "video"
            );
        }
        return false;
    });
}
