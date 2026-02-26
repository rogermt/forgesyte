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

import { useMemo, useCallback } from "react";
import { useManifest } from "../hooks/useManifest";
import type { Tool } from "../types/plugin";

// ============================================================================
// Types
// ============================================================================

export interface ToolSelectorProps {
  /** Currently selected plugin ID */
  pluginId: string | null;
  /** Currently selected tool names (multi-select) */
  selectedTools: string[];
  /** Callback when tool selection changes */
  onToolChange: (toolNames: string[]) => void;
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
  buttonList: {
    display: "flex",
    flexDirection: "column" as const,
    gap: "6px",
  },
  toolButton: {
    padding: "10px 12px",
    borderRadius: "4px",
    fontSize: "13px",
    fontWeight: 500,
    transition: "all 0.2s",
    outline: "none" as const,
    border: "1px solid var(--border-light)",
    backgroundColor: "var(--bg-tertiary)",
    color: "var(--text-primary)",
    cursor: "pointer",
    textAlign: "left" as const,
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
  },
  firstIndicator: {
    fontSize: "11px",
    marginLeft: "8px",
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
  selectedTools = [],
  onToolChange,
  disabled = false,
  compact = false,
}: ToolSelectorProps) {
  // Load manifest for the selected plugin
  const { manifest, loading, error } = useManifest(pluginId);

  // -------------------------------------------------------------------------
  // [BP-2] Memoized computed values
  // -------------------------------------------------------------------------
  const toolList = useMemo(() => {
    if (!manifest) return [];

    // Phase 6: Prefer top-level capabilities (logical tools) over all tools
    // This shows 4 capabilities (player_detection, ball_detection, etc.)
    // instead of 8 concrete tools (video_player_tracking, player_detection, etc.)
    const manifestWithCapabilities = manifest as { capabilities?: string[]; tools: unknown };
    if (manifestWithCapabilities.capabilities && Array.isArray(manifestWithCapabilities.capabilities)) {
      return manifestWithCapabilities.capabilities.map((cap: string) => ({
        id: cap,
        title: cap.replace(/_/g, " ").replace(/\b\w/g, (l: string) => l.toUpperCase()),
      }));
    }

    // Fallback: Union of all tool.capabilities
    const tools = manifest.tools;
    if (Array.isArray(tools)) {
      const allCapabilities = new Set<string>();
      for (const tool of tools) {
        const toolWithCapabilities = tool as { capabilities?: string[] };
        if (toolWithCapabilities.capabilities) {
          for (const cap of toolWithCapabilities.capabilities) {
            allCapabilities.add(cap);
          }
        }
      }
      if (allCapabilities.size > 0) {
        return Array.from(allCapabilities).map((cap) => ({
          id: cap,
          title: cap.replace(/_/g, " ").replace(/\b\w/g, (l) => l.toUpperCase()),
        }));
      }
      // No capabilities, return tools as-is
      return tools;
    } else {
      // Legacy: tools is an object, convert to array of objects
      return Object.entries(tools).map(([name]) => ({
        id: name,
        title: name,
      }));
    }
  }, [manifest]);

  const selectedToolData = useMemo<Tool | null>(() => {
    if (!manifest || selectedTools.length === 0) return null;
    // Show info for first selected tool
    const firstToolId = selectedTools[0];
    // Handle both Phase-12 array format and legacy object format
    if (Array.isArray(manifest.tools)) {
      // Phase-12: find tool by id in array
      return manifest.tools.find((tool) => tool.id === firstToolId) ?? null;
    } else {
      // Legacy: access tool by key
      return manifest.tools[firstToolId] ?? null;
    }
  }, [manifest, selectedTools]);

  // -------------------------------------------------------------------------
  // [BP-3] Stable event handler - toggle tool in array
  // -------------------------------------------------------------------------
  const handleToggleTool = useCallback(
    (toolId: string) => {
      if (selectedTools.includes(toolId)) {
        // Remove tool if already selected (but keep at least one)
        if (selectedTools.length > 1) {
          onToolChange(selectedTools.filter((t) => t !== toolId));
        }
      } else {
        // Add tool
        onToolChange([...selectedTools, toolId]);
      }
    },
    [selectedTools, onToolChange]
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
        <label style={styles.label}>
          Tool{selectedTools.length > 1 ? "s" : ""}
        </label>
        <div style={styles.buttonList}>
          {toolList.map((tool) => {
            const isSelected = selectedTools.includes(tool.id);
            const isFirstSelected = selectedTools[0] === tool.id;
            return (
              <button
                key={tool.id}
                onClick={() => handleToggleTool(tool.id)}
                disabled={disabled}
                style={{
                  ...styles.toolButton,
                  backgroundColor: isSelected
                    ? "var(--accent-orange)"
                    : "var(--bg-tertiary)",
                  color: isSelected
                    ? "white"
                    : "var(--text-primary)",
                  borderColor: isSelected
                    ? "var(--accent-orange)"
                    : "var(--border-light)",
                  cursor: disabled
                    ? "not-allowed"
                    : "pointer",
                  opacity: disabled ? 0.6 : 1,
                }}
                aria-pressed={isSelected}
                title={tool.description ?? tool.title ?? tool.id}
              >
                {tool.title ?? tool.id}
                {isSelected && selectedTools.length > 1 && isFirstSelected && (
                  <span style={styles.firstIndicator}>★</span>
                )}
              </button>
            );
          })}
        </div>
      </div>

      {/* Tool Info Box */}
      {!compact && selectedToolData && (
        <div
          style={styles.infoBox}
          role="region"
          aria-label={`${selectedTools[0]} tool details`}
        >
          <div style={styles.infoHeader}>
            <span style={styles.infoName}>
              {selectedToolData.title ?? selectedTools[0]}
            </span>
            {selectedTools.length > 1 && (
              <span style={{ fontSize: "11px", color: "var(--text-muted)" }}>
                +{selectedTools.length - 1} more
              </span>
            )}
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
          Stop streaming to change tools
        </p>
      )}
    </div>
  );
}

export default ToolSelector;
