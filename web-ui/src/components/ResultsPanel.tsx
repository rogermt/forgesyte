/**
 * Results panel component with support for specialized renderers.
 */

import React from "react";
import { FrameResult } from "../hooks/useWebSocket";
import { Job } from "../api/client";
import { BoundingBoxOverlay, BoundingBox } from "./BoundingBoxOverlay";
import { RadarView, PlayerPosition } from "./RadarView";

export interface ResultsPanelProps {
    mode?: "stream" | "job";
    streamResult?: FrameResult | null;
    job?: Job | null;
    pluginName?: string;
    result?: Record<string, unknown> | null;
}

/**
 * Helper function to extract bounding boxes from result data.
 */
function extractBoundingBoxes(result: Record<string, unknown>): BoundingBox[] {
    const boxes: BoundingBox[] = [];
    if (!result) return boxes;

    // Handle array of boxes
    if (Array.isArray(result.boxes)) {
        return result.boxes.map((box: unknown) => {
            if (typeof box === "object" && box !== null) {
                const b = box as Record<string, unknown>;
                return {
                    x: (b.x as number) || 0,
                    y: (b.y as number) || 0,
                    width: (b.width as number) || 0,
                    height: (b.height as number) || 0,
                    label: (b.label as string) || undefined,
                    confidence: (b.confidence as number) || undefined,
                    color: (b.color as string) || undefined,
                };
            }
            return { x: 0, y: 0, width: 0, height: 0 };
        });
    }

    // Handle nested detection objects
    if (typeof result.detections === "object" && result.detections) {
        const detections = result.detections as Record<string, unknown>;
        Object.values(detections).forEach((det: unknown) => {
            if (typeof det === "object" && det !== null) {
                const d = det as Record<string, unknown>;
                boxes.push({
                    x: (d.x as number) || 0,
                    y: (d.y as number) || 0,
                    width: (d.width as number) || 0,
                    height: (d.height as number) || 0,
                    label: (d.label as string) || undefined,
                    confidence: (d.confidence as number) || undefined,
                });
            }
        });
    }

    return boxes;
}

/**
 * Helper function to extract player positions from result data.
 */
function extractPlayerPositions(result: Record<string, unknown>): PlayerPosition[] {
    const players: PlayerPosition[] = [];
    if (!result) return players;

    // Handle array of players
    if (Array.isArray(result.players)) {
        return result.players.map((player: unknown, idx: number) => {
            if (typeof player === "object" && player !== null) {
                const p = player as Record<string, unknown>;
                return {
                    id: (p.id as string) || `player-${idx}`,
                    x: (p.x as number) || 0,
                    y: (p.y as number) || 0,
                    team: (p.team as "home" | "away") || undefined,
                    label: (p.label as string) || (p.number as string),
                    confidence: (p.confidence as number) || undefined,
                };
            }
            return { id: `player-${idx}`, x: 0, y: 0 };
        });
    }

    return players;
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

                        {/* Render specialized components */}
                        {streamResult.result &&
                        typeof streamResult.result === "object" ? (
                            <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
                                {/* Bounding box overlay */}
                                {extractBoundingBoxes(streamResult.result).length > 0 && (
                                    <div>
                                        <div style={styles.label}>Detection Results</div>
                                        <BoundingBoxOverlay
                                            boxes={extractBoundingBoxes(streamResult.result)}
                                        />
                                    </div>
                                )}

                                {/* Radar/pitch view */}
                                {extractPlayerPositions(streamResult.result).length > 0 && (
                                    <div>
                                        <div style={styles.label}>Player Positions</div>
                                        <RadarView
                                            players={extractPlayerPositions(streamResult.result)}
                                        />
                                    </div>
                                )}

                                {/* Raw result JSON */}
                                <div>
                                    <div style={styles.label}>Raw Result</div>
                                    <pre style={styles.codeBlock}>
                                        {JSON.stringify(streamResult.result, null, 2)}
                                    </pre>
                                </div>
                            </div>
                        ) : (
                            <pre style={styles.codeBlock}>
                                {JSON.stringify(streamResult.result, null, 2)}
                            </pre>
                        )}
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
                            </div>
                        </div>

                        {/* Render specialized components for job results */}
                        {job.result && typeof job.result === "object" ? (
                            <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
                                {/* Bounding box overlay */}
                                {extractBoundingBoxes(job.result as Record<string, unknown>).length > 0 && (
                                    <div>
                                        <div style={styles.label}>Detection Results</div>
                                        <BoundingBoxOverlay
                                            boxes={extractBoundingBoxes(job.result as Record<string, unknown>)}
                                        />
                                    </div>
                                )}

                                {/* Radar/pitch view */}
                                {extractPlayerPositions(job.result as Record<string, unknown>).length > 0 && (
                                    <div>
                                        <div style={styles.label}>Player Positions</div>
                                        <RadarView
                                            players={extractPlayerPositions(job.result as Record<string, unknown>)}
                                        />
                                    </div>
                                )}

                                {/* Raw result JSON */}
                                <div>
                                    <div style={styles.label}>Raw Result</div>
                                    <pre style={styles.codeBlock}>
                                        {JSON.stringify(job.result, null, 2)}
                                    </pre>
                                </div>
                            </div>
                        ) : (
                            <pre style={styles.codeBlock}>
                                {JSON.stringify(job.result, null, 2)}
                            </pre>
                        )}
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
