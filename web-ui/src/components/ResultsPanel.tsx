/**
 * Results panel component (plugin-agnostic for v0.9.4).
 * Shows raw JSON only - no specialized renderers for soccer or other plugins.
 */

import React from "react";
import { FrameResult } from "../hooks/useWebSocket";
import { Job } from "../api/client";
import { ImageMultiToolResults } from "./ImageMultiToolResults";

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
                                 {JSON.stringify(streamResult.result, null, 2)}
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

                        {/* v0.9.4: Handle multi-tool results format */}
                        {/* Use job.results (plural) from backend, fallback to job.result (legacy) */}
                        {(() => {
                            const resultData = job.results || job.result;
                            if (!resultData || typeof resultData !== "object") {
                                return (
                                    <pre style={styles.codeBlock}>
                                        {JSON.stringify(resultData, null, 2)}
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
                                         {JSON.stringify(result, null, 2)}
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
