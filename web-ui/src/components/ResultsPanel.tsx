/**
 * Results panel component
 */

import React from "react";
import { FrameResult } from "../hooks/useWebSocket";
import { Job } from "../api/client";

export interface ResultsPanelProps {
    mode: "stream" | "job";
    streamResult?: FrameResult | null;
    job?: Job | null;
}

export function ResultsPanel({
    mode,
    streamResult,
    job,
}: ResultsPanelProps) {
    const styles: Record<string, React.CSSProperties> = {
        panel: {
            backgroundColor: "#1e1e2e",
            borderRadius: "8px",
            padding: "16px",
            minHeight: "400px",
            display: "flex",
            flexDirection: "column",
        },
        header: {
            fontSize: "14px",
            fontWeight: 600,
            marginBottom: "12px",
            color: "#fff",
        },
        content: {
            flex: 1,
            overflowY: "auto",
            fontSize: "13px",
            color: "#aaa",
        },
    };

    return (
        <div style={styles.panel}>
            <div style={styles.header}>Results</div>

            <div style={styles.content}>
                {mode === "stream" && streamResult ? (
                    <div>
                        <div style={{ marginBottom: "12px" }}>
                            <div style={{ color: "#fff", fontSize: "12px" }}>
                                Frame ID: {streamResult.frame_id}
                            </div>
                            <div style={{ color: "#888", fontSize: "11px" }}>
                                {streamResult.processing_time_ms}ms
                            </div>
                        </div>
                        <pre
                            style={{
                                backgroundColor: "#16162a",
                                padding: "8px",
                                borderRadius: "4px",
                                overflow: "auto",
                                fontSize: "11px",
                            }}
                        >
                            {JSON.stringify(streamResult.result, null, 2)}
                        </pre>
                    </div>
                ) : mode === "stream" ? (
                    <p>Waiting for results...</p>
                ) : null}

                {mode === "job" && job ? (
                    <div>
                        <div style={{ marginBottom: "12px" }}>
                            <div style={{ color: "#fff", fontSize: "12px" }}>
                                Job ID: {job.id}
                            </div>
                            <div style={{ color: "#888", fontSize: "11px" }}>
                                Status: {job.status}
                            </div>
                        </div>
                        <pre
                            style={{
                                backgroundColor: "#16162a",
                                padding: "8px",
                                borderRadius: "4px",
                                overflow: "auto",
                                fontSize: "11px",
                            }}
                        >
                            {JSON.stringify(job.result, null, 2)}
                        </pre>
                    </div>
                ) : mode === "job" ? (
                    <p>Select a job to view results</p>
                ) : null}
            </div>
        </div>
    );
}
