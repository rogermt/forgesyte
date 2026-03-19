/**
 * Results panel component (plugin-agnostic for v0.9.4).
 * Shows raw JSON only - no specialized renderers for soccer or other plugins.
 *
 * Issue #350: Implements lazy loading for video jobs via result_url.
 */

import React, { useMemo, useState, useCallback } from "react";
import { FrameResult } from "../hooks/useWebSocket";
import { Job } from "../api/client";
import { ImageMultiToolResults } from "./ImageMultiToolResults";
import { apiClient } from "../api/client";

export interface ResultsPanelProps {
    mode?: "stream" | "job";
    streamResult?: FrameResult | null;
    job?: Job | null;
    pluginName?: string;
    result?: Record<string, unknown> | null;
}

/**
 * Helper function to detect if result is multi-tool format.
 * v0.9.4: Multi-tool results have {plugin_id, tools: {...}} structure.
 */
function isMultiToolResult(result: Record<string, unknown>): boolean {
    return (
        typeof result === "object" &&
        result !== null &&
        "plugin_id" in result &&
        "tools" in result &&
        typeof result.tools === "object"
    );
}

export function ResultsPanel({
    mode = "stream",
    streamResult,
    job,
}: ResultsPanelProps) {
    // Issue #350: State for lazy-loaded video results
    const [loadedResult, setLoadedResult] = useState<Record<string, unknown> | null>(null);
    const [isLoading, setIsLoading] = useState(false);
    const [loadError, setLoadError] = useState<string | null>(null);

    // PERFORMANCE: Memoize JSON stringification to prevent UI freeze on large results
    // See: https://github.com/rogermt/forgesyte/discussions/349
    const resultData = loadedResult || job?.results || job?.result;
    const jobResultJson = useMemo(() => {
        if (!resultData) return "null";
        // PERFORMANCE GUARD: video_multi results can be 1-10 MB.
        // Skip stringification entirely to prevent UI freeze.
        // The JSX below has a separate guard to display a message instead.
        if (job?.job_type === "video_multi" && !loadedResult) return "";
        return JSON.stringify(resultData, null, 2);
    }, [resultData, job?.job_type, loadedResult]);

    // PERFORMANCE: Memoize stream result JSON
    const streamResultJson = useMemo(() => {
        if (!streamResult?.result) return "null";
        return JSON.stringify(streamResult.result, null, 2);
    }, [streamResult?.result]);

    // Issue #350: Handler for lazy loading video results
    const handleLoadResults = useCallback(async () => {
        if (!job?.result_url) return;
        
        setIsLoading(true);
        setLoadError(null);
        
        try {
            const result = await apiClient.getJobResult(job.job_id, "stream");
            setLoadedResult(result);
        } catch (err) {
            setLoadError(err instanceof Error ? err.message : "Failed to load results");
        } finally {
            setIsLoading(false);
        }
    }, [job?.result_url, job?.job_id]);

    // Reset loaded result when job changes
    React.useEffect(() => {
        setLoadedResult(null);
        setLoadError(null);
    }, [job?.job_id]);

    // TODO: Implement UI plugin loading for result components
    // Future: Load Renderer dynamically via UIPluginManager for pluginName mode
    const styles: Record<string, React.CSSProperties> = {
        panel: {
            backgroundColor: "var(--bg-secondary)",
            borderRadius: "8px",
            padding: "16px",
            minHeight: "400px",
            display: "flex",
            flexDirection: "column",
            border: "1px solid var(--border-light)",
        },
        header: {
            fontSize: "14px",
            fontWeight: 600,
            marginBottom: "12px",
            color: "var(--text-primary)",
        },
        content: {
            flex: 1,
            overflowY: "auto",
            fontSize: "13px",
            color: "var(--text-secondary)",
            paddingRight: "4px",
        },
        metaInfo: {
            marginBottom: "12px",
            display: "flex",
            justifyContent: "space-between",
            alignItems: "flex-start",
        },
        label: {
            fontSize: "12px",
            color: "var(--text-primary)",
            fontWeight: 500,
        },
        subLabel: {
            fontSize: "11px",
            color: "var(--text-muted)",
            marginTop: "4px",
            fontFamily: "monospace",
        },
        codeBlock: {
            backgroundColor: "var(--bg-primary)",
            padding: "8px",
            borderRadius: "4px",
            overflow: "auto",
            fontSize: "11px",
            color: "#a8ff60",
            fontFamily: "monospace",
            border: "1px solid var(--border-light)",
            lineHeight: 1.5,
        },
        emptyState: {
            color: "var(--text-muted)",
            fontSize: "13px",
        },
    };

    return (
        <div
            data-testid="results-panel"
            style={{
                ...styles.panel,
                minHeight: "400px",
                display: "flex",
                flexDirection: "column",
            }}
        >
            <div
                style={{
                    fontSize: "14px",
                    fontWeight: 600,
                    marginBottom: "12px",
                    color: "var(--text-primary)",
                }}
            >
                Results
            </div>

            <div
                data-testid="results-content"
                style={{
                    flex: 1,
                    overflowY: "auto",
                    fontSize: "13px",
                    color: "var(--text-secondary)",
                    paddingRight: "4px",
                }}
            >
                {mode === "stream" && streamResult ? (
                    <div>
                        <div style={styles.metaInfo}>
                            <div>
                                <div style={styles.label}>
                                    Frame ID: {streamResult.frame_id}
                                </div>
                                <div style={styles.subLabel}>
                                    {streamResult.processing_time_ms}ms
                                </div>
                            </div>
                        </div>

                        {/* Raw result JSON only (plugin-agnostic) */}
                         <div>
                             <div style={styles.label}>Raw Result</div>
                             <pre style={styles.codeBlock}>
                                 {streamResultJson}
                             </pre>
                         </div>
                    </div>
                ) : mode === "stream" ? (
                    <p style={styles.emptyState}>Waiting for results...</p>
                ) : null}

                {mode === "job" && job ? (
                    <div>
                        <div style={styles.metaInfo}>
                            <div>
                                <div style={styles.label}>Job ID: {job.job_id}</div>
                                <div style={styles.subLabel}>
                                    Status: {job.status}
                                </div>
                                {/* v0.9.4: Show job type and tools for multi-tool jobs */}
                                {job.job_type && (
                                    <div style={styles.subLabel}>
                                        Type: {job.job_type}
                                    </div>
                                )}
                                {job.tool_list && job.tool_list.length > 0 && (
                                    <div style={styles.subLabel}>
                                        Tools: {job.tool_list.join(", ")}
                                    </div>
                                )}
                            </div>
                        </div>

                        {/* Issue #350: Show summary for video jobs with result_url */}
                        {job.result_url && job.summary && !loadedResult && (
                            <div style={{ ...styles.codeBlock, marginBottom: "12px" }}>
                                <div style={styles.label}>Summary</div>
                                <pre style={{ margin: 0, fontSize: "11px" }}>
                                    {JSON.stringify(job.summary, null, 2)}
                                </pre>
                            </div>
                        )}

                        {/* Issue #350: Load Results button for video jobs */}
                        {job.result_url && !loadedResult && (
                            <div style={{ marginBottom: "12px" }}>
                                <button
                                    onClick={handleLoadResults}
                                    disabled={isLoading}
                                    style={{
                                        padding: "8px 16px",
                                        fontSize: "13px",
                                        backgroundColor: "var(--accent-primary)",
                                        color: "white",
                                        border: "none",
                                        borderRadius: "4px",
                                        cursor: isLoading ? "wait" : "pointer",
                                        opacity: isLoading ? 0.7 : 1,
                                    }}
                                >
                                    {isLoading ? "Loading..." : "Load Results"}
                                </button>
                                {loadError && (
                                    <div style={{ color: "var(--error)", marginTop: "8px", fontSize: "12px" }}>
                                        {loadError}
                                    </div>
                                )}
                            </div>
                        )}

                        {/* v0.9.4: Handle multi-tool results format */}
                        {/* Use job.results (plural) from backend, fallback to job.result (legacy) */}
                        {(() => {
                            // PERFORMANCE GUARD: video_multi jobs can produce huge JSON.
                            // For these without result_url, do NOT pretty-print the full result to avoid UI freeze.
                            if (job.job_type === "video_multi" && !job.result_url && !loadedResult) {
                                return (
                                    <div>
                                        <div style={styles.label}>Result</div>
                                        <pre style={styles.codeBlock}>
{`Job type: video_multi

The full result is too large to render in the browser.
Please inspect the JSON artifact directly in storage (MinIO/S3).`}
                                        </pre>
                                    </div>
                                );
                            }

                            // Issue #350: If video job has result_url but not loaded yet, don't show results
                            if (job.result_url && !loadedResult) {
                                return null;
                            }

                            if (!resultData || typeof resultData !== "object") {
                                return (
                                    <pre style={styles.codeBlock}>
                                        {jobResultJson}
                                    </pre>
                                );
                            }

                            const result = resultData as Record<string, unknown>;

                            // Check for multi-tool result format
                            if (isMultiToolResult(result)) {
                                return <ImageMultiToolResults results={result as { tools: Record<string, unknown> }} />;
                            }

                            // Single-tool result: show raw JSON only
                            return (
                                <div>
                                    <div style={styles.label}>Raw Result</div>
                                    <pre style={styles.codeBlock}>
                                        {jobResultJson}
                                    </pre>
                                </div>
                            );
                        })()}
                    </div>
                ) : mode === "job" ? (
                    <p style={styles.emptyState}>
                        Select a job to view results
                    </p>
                ) : null}
            </div>
        </div>
    );
}
