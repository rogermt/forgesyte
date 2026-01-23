/**
 * Confidence Slider Component
 * Allows users to adjust detection confidence threshold (0.0-1.0)
 *
 * Best Practices Applied:
 * - [BP-1] Controlled component synced with parent state
 * - [BP-2] useMemo for calculated values
 * - [BP-3] useCallback for stable event handlers
 * - [BP-4] Real-time slider feedback with input synchronization
 * - [BP-5] Accessible form controls with labels and ARIA
 */

import { useCallback, useMemo, useId } from "react";

// ============================================================================
// Types
// ============================================================================

export interface ConfidenceSliderProps {
  /** Current confidence value (0.0-1.0) */
  confidence: number;
  /** Callback when confidence changes */
  onConfidenceChange: (confidence: number) => void;
  /** Minimum confidence value (default: 0.0) */
  min?: number;
  /** Maximum confidence value (default: 1.0) */
  max?: number;
  /** Step size (default: 0.05) */
  step?: number;
  /** Whether the slider is disabled */
  disabled?: boolean;
}

// ============================================================================
// Styles
// ============================================================================

const styles = {
  container: {
    display: "flex",
    flexDirection: "column" as const,
    gap: "8px",
  },
  header: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    gap: "8px",
  },
  label: {
    fontSize: "12px",
    fontWeight: 500,
    color: "var(--text-secondary)",
    margin: 0,
  },
  value: {
    fontSize: "13px",
    fontWeight: 600,
    color: "var(--accent-cyan)",
    minWidth: "40px",
    textAlign: "right" as const,
  },
  controlsContainer: {
    display: "flex",
    gap: "8px",
    alignItems: "center",
  },
  slider: {
    flex: 1,
    height: "6px",
    borderRadius: "3px",
    outline: "none" as const,
    cursor: "pointer" as const,
    appearance: "none" as const,
    transition: "all 0.2s",
  },
  input: {
    width: "50px",
    padding: "6px 8px",
    borderRadius: "4px",
    fontSize: "12px",
    fontWeight: 500,
    textAlign: "center" as const,
    outline: "none" as const,
    transition: "all 0.2s",
  },
  infoBox: {
    padding: "8px 10px",
    backgroundColor: "rgba(0, 229, 255, 0.05)",
    border: "1px solid var(--border-light)",
    borderRadius: "4px",
    fontSize: "11px",
    color: "var(--text-secondary)",
    lineHeight: 1.5,
  },
  infoText: {
    margin: 0,
  },
} as const;

// ============================================================================
// Component
// ============================================================================

export function ConfidenceSlider({
  confidence,
  onConfidenceChange,
  min = 0.0,
  max = 1.0,
  step = 0.05,
  disabled = false,
}: ConfidenceSliderProps) {
  // Generate unique ID for accessibility
  const sliderId = useId();
  const inputId = useId();

  // -------------------------------------------------------------------------
  // Validation and clamping
  // -------------------------------------------------------------------------
  const clampedConfidence = useMemo(() => {
    return Math.max(min, Math.min(max, confidence));
  }, [confidence, min, max]);

  // -------------------------------------------------------------------------
  // Formatted value for display
  // -------------------------------------------------------------------------
  const formattedValue = useMemo(() => {
    return clampedConfidence.toFixed(2);
  }, [clampedConfidence]);

  // -------------------------------------------------------------------------
  // Slider background gradient based on value
  // -------------------------------------------------------------------------
  const sliderGradient = useMemo(() => {
    const percentage = ((clampedConfidence - min) / (max - min)) * 100;
    return `linear-gradient(to right, var(--accent-cyan) 0%, var(--accent-cyan) ${percentage}%, var(--bg-hover) ${percentage}%, var(--bg-hover) 100%)`;
  }, [clampedConfidence, min, max]);

  const sliderStyles = useMemo(
    () => ({
      ...styles.slider,
      background: sliderGradient,
      opacity: disabled ? 0.5 : 1,
      cursor: disabled ? "not-allowed" as const : "pointer" as const,
    }),
    [sliderGradient, disabled]
  );

  const inputStyles = useMemo(
    () => ({
      ...styles.input,
      backgroundColor: disabled ? "var(--bg-hover)" : "var(--bg-tertiary)",
      color: disabled ? "var(--text-muted)" : "var(--text-primary)",
      border: `1px solid ${
        disabled ? "var(--border-color)" : "var(--border-light)"
      }`,
      cursor: disabled ? "not-allowed" as const : "text" as const,
    }),
    [disabled]
  );

  // -------------------------------------------------------------------------
  // [BP-3] Stable event handlers
  // -------------------------------------------------------------------------
  const handleSliderChange = useCallback(
    (event: React.ChangeEvent<HTMLInputElement>) => {
      const newValue = parseFloat(event.target.value);
      onConfidenceChange(newValue);
    },
    [onConfidenceChange]
  );

  const handleInputChange = useCallback(
    (event: React.ChangeEvent<HTMLInputElement>) => {
      const input = event.target.value;
      const newValue = parseFloat(input);

      if (!isNaN(newValue)) {
        onConfidenceChange(newValue);
      }
    },
    [onConfidenceChange]
  );

  const handleInputBlur = useCallback(
    (event: React.FocusEvent<HTMLInputElement>) => {
      let newValue = parseFloat(event.target.value);

      if (isNaN(newValue)) {
        newValue = confidence; // Use original confidence, not clampedConfidence
      } else {
        newValue = Math.max(min, Math.min(max, newValue));
      }

      onConfidenceChange(newValue);
    },
    [confidence, min, max, onConfidenceChange]
  );

  // -------------------------------------------------------------------------
  // Render
  // -------------------------------------------------------------------------
  return (
    <div style={styles.container}>
      <div style={styles.header}>
        <label htmlFor={sliderId} style={styles.label}>
          Detection Confidence
        </label>
        <div style={styles.value}>{formattedValue}</div>
      </div>

      <div style={styles.controlsContainer}>
        <input
          id={sliderId}
          type="range"
          min={min}
          max={max}
          step={step}
          value={clampedConfidence}
          onChange={handleSliderChange}
          disabled={disabled}
          style={sliderStyles}
          aria-label="Confidence threshold slider"
          aria-valuemin={min}
          aria-valuemax={max}
          aria-valuenow={parseFloat(formattedValue)}
          aria-valuetext={`${formattedValue} confidence`}
        />

        <input
          id={inputId}
          type="number"
          min={min}
          max={max}
          step={step}
          value={formattedValue}
          onChange={handleInputChange}
          onBlur={handleInputBlur}
          disabled={disabled}
          style={inputStyles}
          aria-label="Confidence value input"
          aria-describedby={`${inputId}-desc`}
        />
      </div>

      <div style={styles.infoBox} id={`${inputId}-desc`}>
        <p style={styles.infoText}>
          ⓘ Only detections with confidence above this threshold will be
          displayed. Lower values show more detections (including less certain
          ones), higher values show only the most confident detections.
        </p>
      </div>
    </div>
  );
}

export default ConfidenceSlider;
