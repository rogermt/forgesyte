import React, { useEffect, useRef, useState } from 'react';

/** Tracked object from video analysis */
interface TrackedObject {
  track_id: number;
  class_id: number;
  xyxy: [number, number, number, number];
  center: [number, number];
}

/** Frame detection results */
interface FrameDetection {
  frame_index: number;
  detections: {
    tracked_objects: TrackedObject[];
  };
}

/** Video analysis results from backend */
export interface VideoResults {
  total_frames: number;
  frames: FrameDetection[];
  video_url?: string;
}

/** Props for VideoResultsViewer component */
interface Props {
  jobId: string;
  results: VideoResults;
}

/**
 * VideoResultsViewer - Displays video with detection overlays
 *
 * Features:
 * - Video playback of the uploaded file
 * - Canvas overlay rendering tracked objects
 * - Frame timeline scrubbing
 * - Real-time sync between video time and frame index
 * - JSON results panel for debugging
 */
export function VideoResultsViewer({ jobId, results }: Props) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [frameIndex, setFrameIndex] = useState(0);

  const frame = results.frames?.[frameIndex] ?? null;

  // Render detection overlays on canvas
  useEffect(() => {
    if (!canvasRef.current || !frame) return;
    const ctx = canvasRef.current.getContext('2d');
    if (!ctx) return;

    ctx.clearRect(0, 0, canvasRef.current.width, canvasRef.current.height);

    const objects = frame.detections?.tracked_objects ?? [];
    ctx.strokeStyle = 'lime';
    ctx.fillStyle = 'lime';
    ctx.lineWidth = 2;
    ctx.font = '12px sans-serif';

    for (const obj of objects) {
      const [x1, y1, x2, y2] = obj.xyxy;
      ctx.strokeRect(x1, y1, x2 - x1, y2 - y1);
      ctx.fillText(`ID ${obj.track_id}`, x1, Math.max(10, y1 - 4));
    }
  }, [frame]);

  // Sync video time with frame index
  useEffect(() => {
    if (!videoRef.current || !results.total_frames) return;
    const video = videoRef.current;

    const update = () => {
      if (!video.duration) return;
      const ratio = video.currentTime / video.duration;
      const idx = Math.floor(ratio * results.total_frames);
      setFrameIndex(Math.max(0, Math.min(results.total_frames - 1, idx)));
    };

    video.addEventListener('timeupdate', update);
    return () => video.removeEventListener('timeupdate', update);
  }, [results.total_frames]);

  // Handle timeline slider change
  const onTimeline = (e: React.ChangeEvent<HTMLInputElement>) => {
    const idx = Number(e.target.value);
    setFrameIndex(idx);
    if (videoRef.current && videoRef.current.duration) {
      const ratio = idx / results.total_frames;
      videoRef.current.currentTime = ratio * videoRef.current.duration;
    }
  };

  // Video URL - use provided URL or construct from job ID and API base
  const apiBase = import.meta.env.VITE_API_URL || '/v1';
  const videoUrl = results.video_url ?? `${apiBase}/jobs/${jobId}/video`;

  return (
    <div className="video-results-viewer">
      <div className="video-wrapper" style={{ position: 'relative', minHeight: '300px', background: '#000' }}>
        <video
          ref={videoRef}
          src={videoUrl}
          controls
          style={{ width: '100%', display: 'block' }}
          data-testid="video-player"
        />
        <canvas
          ref={canvasRef}
          width={1280}
          height={720}
          style={{
            position: 'absolute',
            top: 0,
            left: 0,
            width: '100%',
            height: '100%',
            pointerEvents: 'none',
          }}
        />
      </div>

      {results.total_frames > 0 && (
        <input
          type="range"
          min={0}
          max={results.total_frames - 1}
          value={frameIndex}
          onChange={onTimeline}
          style={{ width: '100%', marginTop: '1rem' }}
          aria-label="Frame timeline"
        />
      )}

      <pre style={{ marginTop: '1rem', overflow: 'auto', maxHeight: '300px' }}>
        {JSON.stringify(results, null, 2)}
      </pre>
    </div>
  );
}
