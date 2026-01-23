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
} from "../types/video-tracker";

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

        if (!response.ok) {
            throw new Error(
                `API error: ${response.status} ${response.statusText}`
            );
        }

        return response.json();
    }

    async getPlugins(): Promise<Plugin[]> {
        const result = (await this.fetch("/plugins")) as Record<string, unknown>;
        return result.plugins as Plugin[];
    }

    async analyzeImage(
        file: File,
        plugin: string
    ): Promise<AnalysisResult> {
        const formData = new FormData();
        formData.append("file", file);

        const url = new URL(`${this.baseUrl}/analyze`, window.location.origin);
        url.searchParams.append("plugin", plugin);

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
        return this.fetch(`/plugins/${pluginId}/manifest`) as unknown as Promise<PluginManifest>;
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
}

export const apiClient = new ForgeSyteAPIClient();
export default apiClient;
