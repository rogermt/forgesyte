/**
 * API client for ForgeSyte Server
 */

const API_BASE = "/v1";

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
    id: string;
    status: "pending" | "processing" | "done" | "error";
    plugin: string;
    input_file?: string;
    result?: Record<string, unknown>;
    error?: string;
    created_at: string;
    updated_at: string;
}

export interface AnalysisResult {
    job_id: string;
    status: string;
}

export class ForgeSyteAPIClient {
    private baseUrl: string;
    private apiKey?: string;

    constructor(baseUrl = API_BASE, apiKey?: string) {
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
        formData.append("plugin", plugin);

        const url = `${this.baseUrl}/analyze`;
        const headers: HeadersInit = {};

        if (this.apiKey) {
            headers["X-API-Key"] = this.apiKey;
        }

        const response = await fetch(url, {
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
        return this.fetch(`/jobs/${jobId}`) as Promise<Job>;
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
        return this.fetch(`/jobs/${jobId}`, {
            method: "DELETE",
        }) as Promise<{ status: string; job_id: string }>;
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
}

export const apiClient = new ForgeSyteAPIClient();
export default apiClient;
