import React from "react";

type Props = {
  results: {
    job_id: string;
    job_type?: string;  // Issue #350: Added for large result guard
    results?: Record<string, unknown> | null;
    total_frames?: number;
    frames?: unknown[];
    created_at?: string;
    updated_at?: string;
  };
};

/**
 * Check if results have tools structure (multi-tool format).
 * Issue #350: These results can be 1-10 MB and should not be stringified.
 */
function hasToolsStructure(results: unknown): boolean {
  if (!results || typeof results !== "object") return false;
  const r = results as Record<string, unknown>;
  return "tools" in r && typeof r.tools === "object" && r.tools !== null;
}

export const JobResults: React.FC<Props> = ({ results }) => {
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

  // Issue #350: Guard against large video_multi results
  // video_multi results can be 1-10 MB, which freezes the UI when stringified
  if (results.job_type === "video_multi" || hasToolsStructure(results.results)) {
    return (
      <div style={{ marginTop: "20px" }}>
        <div style={{ fontSize: "14px", fontWeight: 600, marginBottom: "12px" }}>
          Job Results
        </div>
        <pre style={codeBlockStyle}>
{`Job type: video_multi

The full result is too large to render in the browser.
Use the artifact URL to download the JSON file directly.`}
        </pre>
      </div>
    );
  }

  // For flattened video results, show the whole object; otherwise show nested results
  const resultData = results.results ?? (results.total_frames || results.frames ? results : null);

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