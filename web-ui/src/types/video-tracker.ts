/**
 * Video Tracker Types
 * Types for real-time video frame processing with plugin tools
 */

export interface Detection {
    x: number;
    y: number;
    width: number;
    height: number;
    confidence: number;
    class?: string;
    track_id?: number;
}

export interface ToolResult {
    detections?: Detection[];
    tracks?: Record<number, Detection[]>;
    annotated_frame_base64?: string;
    radar_base64?: string;
    [key: string]: unknown;
}

export interface ToolExecutionResponse {
    tool_name: string;
    plugin_id: string;
    result: ToolResult;
    processing_time_ms: number;
}

export interface TrackFrame {
    frame_number: number;
    timestamp: number;
    tool_name: string;
    result: ToolResult;
    annotated_frame_base64?: string;
}

export interface VideoProcessorConfig {
    pluginId: string;
    toolName: string;
    device: "cpu" | "cuda";
    confidence?: number;
    annotated?: boolean;
}

export interface VideoProcessorState {
    isProcessing: boolean;
    frameCount: number;
    fps: number;
    error?: string;
}
