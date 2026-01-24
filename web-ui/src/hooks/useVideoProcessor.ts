/**
 * useVideoProcessor Hook
 * Manages real-time video frame processing with:
 * - Frame buffering (last N frames)
 * - Track persistence (maintains track_id across frames)
 * - FPS calculation
 * - Error handling
 */

import { useCallback, useRef, useState } from "react";
import { apiClient } from "../api/client";
import type {
    Detection,
    TrackFrame,
    VideoProcessorConfig,
    VideoProcessorState,
} from "../types/video-tracker";

const FRAME_BUFFER_SIZE = 10;
const TRACK_TIMEOUT_MS = 5000; // Tracks expire after 5 seconds of no detection

interface TrackState {
    lastDetection: Detection;
    lastSeenTime: number;
    consecutiveFrames: number;
}

export function useVideoProcessor(config: VideoProcessorConfig | null) {
    const [state, setState] = useState<VideoProcessorState>({
        isProcessing: false,
        frameCount: 0,
        fps: 0,
        error: undefined,
    });

    const [frames, setFrames] = useState<TrackFrame[]>([]);
    const [detections, setDetections] = useState<Detection[]>([]);

    const frameBuffer = useRef<TrackFrame[]>([]);
    const trackMap = useRef<Map<number, TrackState>>(new Map());
    const lastFrameTime = useRef<number>(Date.now());
    const frameCounterRef = useRef<number>(0);
    const fpsIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

    // Initialize FPS counter
    const startFpsCounter = useCallback(() => {
        fpsIntervalRef.current = setInterval(() => {
            const now = Date.now();
            const elapsed = (now - lastFrameTime.current) / 1000;
            if (elapsed > 0) {
                const fps = Math.round(frameCounterRef.current / elapsed);
                setState((prev) => ({ ...prev, fps }));
                frameCounterRef.current = 0;
                lastFrameTime.current = now;
            }
        }, 1000);
    }, []);

    const stopFpsCounter = useCallback(() => {
        if (fpsIntervalRef.current) {
            clearInterval(fpsIntervalRef.current);
            fpsIntervalRef.current = null;
        }
    }, []);

    // Process a single frame
    const processFrame = useCallback(
        async (frameBase64: string) => {
            if (!config) {
                setState((prev) => ({
                    ...prev,
                    error: "No config provided",
                }));
                return;
            }

            setState((prev) => ({ ...prev, isProcessing: true, error: undefined }));

            try {
                const args: Record<string, unknown> = {
                    frame_base64: frameBase64,
                    device: config.device,
                };

                if (config.annotated !== undefined) {
                    args.annotated = config.annotated;
                }

                const response = await apiClient.runPluginTool(
                    config.pluginId,
                    config.toolName,
                    args
                );

                frameCounterRef.current++;

                // Add to frame buffer
                const trackFrame: TrackFrame = {
                    frame_number: frameCounterRef.current,
                    timestamp: Date.now(),
                    tool_name: config.toolName,
                    result: response.result,
                    annotated_frame_base64: response.result
                        .annotated_frame_base64 as string | undefined,
                };

                frameBuffer.current.push(trackFrame);
                if (frameBuffer.current.length > FRAME_BUFFER_SIZE) {
                    frameBuffer.current.shift();
                }

                // Update track persistence
                const frameDetections: Detection[] =
                    (response.result.detections as Detection[]) || [];
                updateTracking(frameDetections);

                setFrames([...frameBuffer.current]);
                setDetections(frameDetections);

                setState((prev) => ({
                    ...prev,
                    frameCount: frameCounterRef.current,
                    isProcessing: false,
                }));
            } catch (err) {
                const message =
                    err instanceof Error ? err.message : "Frame processing failed";
                setState((prev) => ({
                    ...prev,
                    isProcessing: false,
                    error: message,
                }));
            }
        },
        // eslint-disable-next-line react-hooks/exhaustive-deps
        [config]
    );

    // Update track persistence
    const updateTracking = useCallback((frameDetections: Detection[]) => {
        const now = Date.now();
        const newTracks = new Map<number, TrackState>();

        // Mark all existing tracks as potentially expired
        const validTracks = new Set<number>();

        // Assign tracks to detections (simple proximity matching)
        frameDetections.forEach((detection) => {
            let assignedTrackId: number | null = null;
            let minDistance = Infinity;

            // Find closest track
            trackMap.current.forEach((trackState, trackId) => {
                const lastDet = trackState.lastDetection;
                const distance = Math.sqrt(
                    (detection.x - lastDet.x) ** 2 +
                    (detection.y - lastDet.y) ** 2
                );

                if (
                    distance < minDistance &&
                    distance < 50 &&
                    now - trackState.lastSeenTime < TRACK_TIMEOUT_MS
                ) {
                    minDistance = distance;
                    assignedTrackId = trackId;
                }
            });

            // If no track assigned, create new one
            if (assignedTrackId === null) {
                assignedTrackId = Math.max(
                    0,
                    ...Array.from(trackMap.current.keys())
                ) + 1;
            }

            validTracks.add(assignedTrackId);
            newTracks.set(assignedTrackId, {
                lastDetection: { ...detection, track_id: assignedTrackId },
                lastSeenTime: now,
                consecutiveFrames:
                    (trackMap.current.get(assignedTrackId)?.consecutiveFrames || 0) +
                    1,
            });
        });

        // Remove expired tracks
        trackMap.current.forEach((_, trackId) => {
            if (!validTracks.has(trackId)) {
                trackMap.current.delete(trackId);
            }
        });

        // Update with new tracks
        newTracks.forEach((state, trackId) => {
            trackMap.current.set(trackId, state);
        });
    }, []);

    // Start processing
    const start = useCallback(() => {
        frameBuffer.current = [];
        trackMap.current.clear();
        frameCounterRef.current = 0;
        lastFrameTime.current = Date.now();
        setState({ isProcessing: false, frameCount: 0, fps: 0, error: undefined });
        startFpsCounter();
    }, [startFpsCounter]);

    // Stop processing
    const stop = useCallback(() => {
        stopFpsCounter();
        frameBuffer.current = [];
        trackMap.current.clear();
    }, [stopFpsCounter]);

    // Clear buffers
    const clear = useCallback(() => {
        frameBuffer.current = [];
        trackMap.current.clear();
        setFrames([]);
        setDetections([]);
        setState({ isProcessing: false, frameCount: 0, fps: 0, error: undefined });
    }, []);

    return {
        state,
        frames,
        detections,
        processFrame,
        start,
        stop,
        clear,
    };
}
