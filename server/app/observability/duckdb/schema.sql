-- Phase 8 Metrics Schema (DuckDB)
-- Runtime implementation of metrics database
-- Reference: .ampcode/04_PHASE_NOTES/Phase_8/PHASE_8_METRICS_SCHEMA.sql

CREATE TABLE IF NOT EXISTS job_metrics (
    id UUID PRIMARY KEY,
    job_id TEXT NOT NULL,
    plugin TEXT NOT NULL,
    device TEXT NOT NULL,
    status TEXT NOT NULL,
    duration_ms INTEGER,
    created_at TIMESTAMP NOT NULL,
    completed_at TIMESTAMP,
    error_message TEXT
);

CREATE TABLE IF NOT EXISTS plugin_metrics (
    id UUID PRIMARY KEY,
    job_id TEXT NOT NULL,
    plugin TEXT NOT NULL,
    tool TEXT,
    duration_ms INTEGER NOT NULL,
    success BOOLEAN NOT NULL,
    created_at TIMESTAMP NOT NULL
);

CREATE TABLE IF NOT EXISTS overlay_metrics (
    id UUID PRIMARY KEY,
    job_id TEXT NOT NULL,
    frame_index INTEGER NOT NULL,
    render_time_ms INTEGER NOT NULL,
    dropped_frames INTEGER DEFAULT 0,
    fps REAL,
    created_at TIMESTAMP NOT NULL
);

CREATE TABLE IF NOT EXISTS device_usage (
    id UUID PRIMARY KEY,
    job_id TEXT NOT NULL,
    device_requested TEXT NOT NULL,
    device_used TEXT NOT NULL,
    fallback BOOLEAN NOT NULL,
    created_at TIMESTAMP NOT NULL
);
