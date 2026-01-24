/**
 * Tool Selector Component
 * Allows users to select a specific tool from a loaded plugin manifest
 *
 * Best Practices Applied:
 * - [BP-1] Controlled component synced with parent state
 * - [BP-2] useMemo for manifest parsing
 * - [BP-3] useCallback for stable event handlers
 * - [BP-4] Proper loading/error/empty states
 * - [BP-5] Accessible form controls with labels
 * - [BP-6] Tool information display with inputs/outputs
 */

import { useId, useMemo, useCallback } from "react";
import { useManifest } from "../hooks/useManifest";
import type { Tool } from "../types/plugin";

// ============================================================================
// Types
// ============================================================================

export interface ToolSelectorProps {
  /** Currently selected plugin ID */
  pluginId: string | null;
  /** Currently selected tool name */
  selectedTool: string;
  /** Callback when tool selection changes */
  onToolChange: (toolName: string) => void;
  /** Whether the selector is disabled (e.g., during streaming) */
  disabled?: boolean;
  /** Optional: Show compact version without description */
  compact?: boolean;
}

// ============================================================================
// Styles
// ============================================================================

const styles = {
  container: {
    display: "flex",
    flexDirection: "column" as const,
    gap: "12px",
  },
  heading: {
    margin: 0,
    fontSize: "14px",
    fontWeight: 600,
    color: "var(--text-primary)",
  },
  label: {
    display: "block",
    marginBottom: "6px",
    fontSize: "12px",
    fontWeight: 500,
    color: "var(--text-secondary)",
  },
  selectBase: {
    width: "100%",
    padding: "10px 12px",
    borderRadius: "4px",
    fontSize: "13px",
    fontWeight: 500,
    transition: "all 0.2s",
    outline: "none" as const,
  },
  loading: {
    color: "var(--text-muted)",
    margin: 0,
    padding: "10px 0",
    fontSize: "13px",
  },
  error: {
    color: "var(--accent-red)",
    backgroundColor: "rgba(220, 53, 69, 0.1)",
    padding: "10px 12px",
    borderRadius: "4px",
    border: "1px solid var(--accent-red)",
    margin: 0,
    fontSize: "13px",
  },
  empty: {
    color: "var(--text-muted)",
    margin: 0,
    padding: "10px 0",
    fontSize: "13px",
  },
  infoBox: {
    padding: "12px",
    backgroundColor: "rgba(0, 229, 255, 0.05)",
    border: "1px solid var(--border-light)",
    borderRadius: "4px",
    fontSize: "12px",
    color: "var(--text-secondary)",
    lineHeight: 1.6,
  },
  infoHeader: {
    marginBottom: "8px",
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
  },
  infoName: {
    fontWeight: 600,
    color: "var(--text-primary)",
  },
  infoDescription: {
    margin: "0 0 8px 0",
  },
  infoSection: {
    marginTop: "6px",
  },
  infoLabel: {
    fontSize: "11px",
    marginBottom: "2px",
    fontWeight: 500,
  },
  infoValue: {
    fontSize: "11px",
    marginTop: "2px",
    paddingLeft: "8px",
    borderLeft: "2px solid var(--border-light)",
  },
  inputsGrid: {
    display: "grid",
    gridTemplateColumns: "repeat(2, 1fr)",
    gap: "6px",
    marginTop: "4px",
  },
  inputItem: {
    fontSize: "10px",
    padding: "4px 6px",
    backgroundColor: "rgba(0, 229, 255, 0.1)",
    borderRadius: "2px",
    border: "1px solid var(--border-light)",
  },
} as const;

// ============================================================================
// Component
// ============================================================================

export function ToolSelector({
  pluginId,
  selectedTool,
  onToolChange,
  disabled = false,
  compact = false,
}: ToolSelectorProps) {
  // Generate unique ID for accessibility
  const selectId = useId();

  // Load manifest for the selected plugin
  const { manifest, loading, error } = useManifest(pluginId);

  // -------------------------------------------------------------------------
  // [BP-2] Memoized computed values
  // -------------------------------------------------------------------------
  const toolList = useMemo(() => {
    if (!manifest) return [];
    return Object.entries(manifest.tools).map(([name]) => name);
  }, [manifest]);

  const selectedToolData = useMemo<Tool | null>(() => {
    if (!manifest) return null;
    return manifest.tools[selectedTool] ?? null;
  }, [manifest, selectedTool]);

  const selectStyles = useMemo(
    () => ({
      ...styles.selectBase,
      backgroundColor: disabled ? "var(--bg-hover)" : "var(--bg-tertiary)",
      color: disabled ? "var(--text-muted)" : "var(--text-primary)",
      border: `1px solid ${
        disabled ? "var(--border-color)" : "var(--border-light)"
      }`,
      cursor: disabled ? "not-allowed" as const : ("pointer" as const),
    }),
    [disabled]
  );

  // -------------------------------------------------------------------------
  // [BP-3] Stable event handler
  // -------------------------------------------------------------------------
  const handleChange = useCallback(
    (event: React.ChangeEvent<HTMLSelectElement>) => {
      const newTool = event.target.value;
      onToolChange(newTool);
    },
    [onToolChange]
  );

  // -------------------------------------------------------------------------
  // Render: No plugin selected
  // -------------------------------------------------------------------------
  if (!pluginId) {
    return (
      <div style={styles.container}>
        <h3 style={styles.heading}>Select Tool</h3>
        <p style={styles.empty}>Select a plugin first</p>
      </div>
    );
  }

  // -------------------------------------------------------------------------
  // Render: Loading State
  // -------------------------------------------------------------------------
  if (loading) {
    return (
      <div style={styles.container}>
        <h3 style={styles.heading}>Select Tool</h3>
        <p style={styles.loading}>Loading tools...</p>
      </div>
    );
  }

  // -------------------------------------------------------------------------
  // Render: Error State
  // -------------------------------------------------------------------------
  if (error) {
    return (
      <div style={styles.container}>
        <h3 style={styles.heading}>Select Tool</h3>
        <p style={styles.error}>
          <strong>Error:</strong> {error}
        </p>
      </div>
    );
  }

  // -------------------------------------------------------------------------
  // Render: No tools available
  // -------------------------------------------------------------------------
  if (toolList.length === 0) {
    return (
      <div style={styles.container}>
        <h3 style={styles.heading}>Select Tool</h3>
        <p style={styles.empty}>No tools available in this plugin</p>
      </div>
    );
  }

  // -------------------------------------------------------------------------
  // Render: Main Component
  // -------------------------------------------------------------------------
  return (
    <div style={styles.container}>
      <div>
        <label htmlFor={selectId} style={styles.label}>
          Tool
        </label>
        <select
          id={selectId}
          value={selectedTool}
          onChange={handleChange}
          disabled={disabled}
          style={selectStyles}
          aria-describedby={selectedToolData ? `${selectId}-desc` : undefined}
        >
          {toolList.map((toolName) => (
            <option key={toolName} value={toolName}>
              {toolName}
            </option>
          ))}
        </select>
      </div>

      {/* Tool Info Box */}
      {!compact && selectedToolData && (
        <div
          style={styles.infoBox}
          id={`${selectId}-desc`}
          role="region"
          aria-label={`${selectedTool} tool details`}
        >
          <div style={styles.infoHeader}>
            <span style={styles.infoName}>{selectedTool}</span>
          </div>

          {selectedToolData.description && (
            <p style={styles.infoDescription}>{selectedToolData.description}</p>
          )}

          {Object.keys(selectedToolData.inputs).length > 0 && (
            <div style={styles.infoSection}>
              <div
                style={{
                  ...styles.infoLabel,
                  color: "var(--accent-cyan)",
                }}
              >
                Inputs:
              </div>
              <div style={styles.inputsGrid}>
                {Object.entries(selectedToolData.inputs).map(([key, input]) => (
                  <div key={key} style={styles.inputItem}>
                    <div>
                      <strong>{key}</strong>
                    </div>
                    <div style={{ marginTop: "2px" }}>
                      {input.type}
                      {input.default !== undefined && ` (default: ${String(input.default)})`}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {Object.keys(selectedToolData.outputs).length > 0 && (
            <div style={styles.infoSection}>
              <div
                style={{
                  ...styles.infoLabel,
                  color: "var(--accent-orange)",
                }}
              >
                Outputs:
              </div>
              <div style={styles.inputsGrid}>
                {Object.entries(selectedToolData.outputs).map(
                  ([key, output]) => (
                    <div key={key} style={styles.inputItem}>
                      <div>
                        <strong>{key}</strong>
                      </div>
                      <div style={{ marginTop: "2px" }}>{output.type}</div>
                    </div>
                  )
                )}
              </div>
            </div>
          )}
        </div>
      )}

      {disabled && (
        <p
          style={{
            margin: 0,
            fontSize: "11px",
            color: "var(--text-muted)",
            fontStyle: "italic",
          }}
        >
          Stop streaming to change tool
        </p>
      )}
    </div>
  );
}

export default ToolSelector;
