// src/api/types.ts

// Detection returned by both streaming and MP4 jobs
export interface Detection {
  x: number;
  y: number;
  width: number;
  height: number;
  label: string;
  score: number;
}

// Realtime streaming result (Phase 17 WebSocket)
export interface RealtimeResult {
  detections: Detection[];
  timestamp: string;
}

// MP4 batch job status (Phase 15/16 job pipeline)
export interface Mp4Job {
  id: string;
  status: "queued" | "processing" | "completed" | "error";
  progress: number;
  frames_processed: number;
  error?: string;
}