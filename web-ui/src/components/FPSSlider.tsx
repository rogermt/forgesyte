/**
 * FPS Slider Component
 * 
 * Allows users to adjust target FPS for video processing.
 * Persists FPS target to localStorage.
 * 
 * Phase 9: UI Controls
 */

import { useState, useEffect, useCallback } from 'react';

// ============================================================================
// Types
// ============================================================================

export interface FPSSliderProps {
  /** Callback when FPS target changes */
  onFPSChange?: (fps: number) => void;
  /** Currently selected FPS target */
  selectedFPS?: number;
  /** Whether the slider is disabled */
  disabled?: boolean;
}

// ============================================================================
// Constants
// ============================================================================

const STORAGE_KEY = 'forgesyte_fps_target';

const MIN_FPS = 1;
const MAX_FPS = 120;
const DEFAULT_FPS = 30;

// ============================================================================
// Component
// ============================================================================

export function FPSSlider({
  onFPSChange,
  selectedFPS = DEFAULT_FPS,
  disabled = false,
}: FPSSliderProps) {
  const [fps, setFPS] = useState<number>(selectedFPS);

  // Stable callback
  const handleChange = useCallback((newFPS: number) => {
    setFPS(newFPS);
    localStorage.setItem(STORAGE_KEY, String(newFPS));
    if (onFPSChange) {
      onFPSChange(newFPS);
    }
  }, [onFPSChange]);

  // Load preference from localStorage on mount (only once)
  useEffect(() => {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved) {
      const parsed = parseInt(saved, 10);
      if (!isNaN(parsed) && parsed >= MIN_FPS && parsed <= MAX_FPS) {
        setFPS(parsed);
        if (onFPSChange) {
          onFPSChange(parsed);
        }
        return; // Don't apply selectedFPS prop if we loaded from storage
      }
    }
    // Only update from prop if no localStorage value
    if (selectedFPS && selectedFPS !== fps) {
      setFPS(selectedFPS);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []); // Empty dependency array - run only on mount

  return (
    <div style={styles.container}>
      <div style={styles.header}>
        <label htmlFor="fps-slider" style={styles.label}>
          Target FPS
        </label>
        <span style={styles.value}>{fps} FPS</span>
      </div>
      <input
        type="range"
        id="fps-slider"
        min={MIN_FPS}
        max={MAX_FPS}
        value={fps}
        onChange={(e) => handleChange(parseInt(e.target.value, 10))}
        disabled={disabled}
        style={styles.slider}
        aria-valuemin={MIN_FPS}
        aria-valuemax={MAX_FPS}
        aria-valuenow={fps}
      />
      <div style={styles.legend}>
        <span style={styles.legendItem}>{MIN_FPS}</span>
        <span style={styles.legendItem}>{MAX_FPS}</span>
      </div>
    </div>
  );
}

// ============================================================================
// Styles
// ============================================================================

const styles = {
  container: {
    display: 'flex',
    flexDirection: 'column' as const,
    gap: '8px',
  },
  header: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  label: {
    fontSize: '12px',
    fontWeight: 500,
    color: 'var(--text-secondary)',
  },
  value: {
    fontSize: '12px',
    fontWeight: 600,
    color: 'var(--text-primary)',
    fontFamily: 'monospace',
  },
  slider: {
    width: '100%',
    height: '6px',
    borderRadius: '3px',
    backgroundColor: 'var(--bg-tertiary)',
    outline: 'none',
    cursor: 'pointer',
    appearance: 'none' as const,
    WebkitAppearance: 'none' as const,
  },
  legend: {
    display: 'flex',
    justifyContent: 'space-between',
    fontSize: '10px',
    color: 'var(--text-muted)',
  },
  legendItem: {
    fontFamily: 'monospace',
  },
} as const;

export default FPSSlider;

