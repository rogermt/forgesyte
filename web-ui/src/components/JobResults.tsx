import React from "react";

type Props = {
  results: {
    job_id: string;
    results?: Record<string, unknown> | null;
    total_frames?: number;
    frames?: unknown[];
    created_at?: string;
    updated_at?: string;
  };
};

export const JobResults: React.FC<Props> = ({ results }) => {
  // For flattened video results, show the whole object; otherwise show nested results
  const resultData = results.results ?? (results.total_frames || results.frames ? results : null);

  const codeBlockStyle: React.CSSProperties = {
    backgroundColor: "var(--bg-primary)",
    padding: "8px",
    borderRadius: "4px",
    overflow: "auto",
    fontSize: "11px",
    color: "#a8ff60",
    fontFamily: "monospace",
    border: "1px solid var(--border-light)",
    lineHeight: 1.5,
  };

  return (
    <div style={{ marginTop: "20px" }}>
      <div style={{ fontSize: "14px", fontWeight: 600, marginBottom: "12px" }}>
        Job Results
      </div>

      {resultData ? (
        <pre style={codeBlockStyle}>
          {JSON.stringify(resultData, null, 2)}
        </pre>
      ) : (
        <div style={{ fontSize: "13px", color: "var(--text-muted)" }}>
          No results available.
        </div>
      )}
    </div>
  );
};