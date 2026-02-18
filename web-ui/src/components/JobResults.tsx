import React from "react";

type Props = {
  results: {
    job_id: string;
    results: {
      text?: string;
      detections?: Array<{
        label: string;
        confidence: number;
        bbox: number[];
      }>;
    } | null;
    created_at: string;
    updated_at: string;
  };
};

export const JobResults: React.FC<Props> = ({ results }) => {
  const { detections, text } = results.results || {};

  return (
    <div style={{ marginTop: "20px", padding: "20px", border: "1px solid #ccc" }}>
      <h3>Results</h3>

      {detections && detections.length > 0 && (
        <div style={{ marginBottom: "20px" }}>
          <h4>Object Detections</h4>
          {detections.map((det, idx) => (
            <div key={idx} style={{ marginBottom: "10px", padding: "10px", border: "1px solid #eee" }}>
              <div><strong>Label:</strong> {det.label}</div>
              <div><strong>Confidence:</strong> {(det.confidence * 100).toFixed(1)}%</div>
              <div><strong>Box:</strong> [{det.bbox.join(", ")}]</div>
            </div>
          ))}
        </div>
      )}

      {text && text.trim() ? (
        <div>
          <h4>OCR Text</h4>
          <pre style={{ whiteSpace: "pre-wrap", wordBreak: "break-word" }}>
            {text}
          </pre>
        </div>
      ) : (
        <div>
          <h4>OCR Text</h4>
          <div>No OCR text available.</div>
        </div>
      )}

      {!detections && !text && (
        <div>No results available.</div>
      )}
    </div>
  );
};