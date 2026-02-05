/**
 * Device Selector Component
 * 
 * Allows users to select a processing device (CPU, GPU, NVIDIA).
 * Persists device preference to localStorage.
 * 
 * Phase 9: UI Controls
 */

import { useState, useEffect, useCallback } from 'react';

// ============================================================================
// Types
// ============================================================================

export interface DeviceSelectorProps {
  /** Callback when device selection changes */
  onDeviceChange?: (device: string) => void;
  /** Currently selected device */
  selectedDevice?: string;
  /** Whether the selector is disabled */
  disabled?: boolean;
}

// ============================================================================
// Constants
// ============================================================================

const STORAGE_KEY = 'forgesyte_device_preference';

const AVAILABLE_DEVICES = [
  { value: 'cpu', label: 'CPU', description: 'Use processor (slower but compatible)' },
  { value: 'gpu', label: 'GPU', description: 'Use GPU acceleration' },
  { value: 'nvidia', label: 'NVIDIA', description: 'Use NVIDIA GPU (fastest)' },
];

// ============================================================================
// Component
// ============================================================================

export function DeviceSelector({
  onDeviceChange,
  selectedDevice = 'cpu',
  disabled = false,
}: DeviceSelectorProps) {
  const [device, setDevice] = useState<string>(selectedDevice);

  // Stable callback
  const handleChange = useCallback((newDevice: string) => {
    setDevice(newDevice);
    localStorage.setItem(STORAGE_KEY, newDevice);
    if (onDeviceChange) {
      onDeviceChange(newDevice);
    }
  }, [onDeviceChange]);

  // Load preference from localStorage on mount (only once)
  useEffect(() => {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved && AVAILABLE_DEVICES.some(d => d.value === saved)) {
      setDevice(saved);
      if (onDeviceChange) {
        onDeviceChange(saved);
      }
      return; // Don't apply selectedDevice prop if we loaded from storage
    }
    // Only update from prop if no localStorage value
    if (selectedDevice && selectedDevice !== device) {
      setDevice(selectedDevice);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []); // Empty dependency array - run only on mount

  const selectedDeviceInfo = AVAILABLE_DEVICES.find(d => d.value === device);

  return (
    <div style={styles.container}>
      <label htmlFor="device-selector" style={styles.label}>
        Processing Device
      </label>
      <select
        id="device-selector"
        value={device}
        onChange={(e) => handleChange(e.target.value)}
        disabled={disabled}
        style={styles.select}
        aria-describedby={device ? 'device-description' : undefined}
      >
        {AVAILABLE_DEVICES.map((dev) => (
          <option key={dev.value} value={dev.value}>
            {dev.label}
          </option>
        ))}
      </select>
      {selectedDeviceInfo && (
        <p id="device-description" style={styles.description}>
          {selectedDeviceInfo.description}
        </p>
      )}
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
    gap: '6px',
  },
  label: {
    fontSize: '12px',
    fontWeight: 500,
    color: 'var(--text-secondary)',
  },
  select: {
    width: '100%',
    padding: '8px 12px',
    borderRadius: '4px',
    fontSize: '13px',
    fontWeight: 500,
    backgroundColor: 'var(--bg-tertiary)',
    color: 'var(--text-primary)',
    border: '1px solid var(--border-light)',
    cursor: 'pointer',
    outline: 'none',
    transition: 'all 0.2s',
  },
  description: {
    margin: 0,
    fontSize: '11px',
    color: 'var(--text-muted)',
  },
} as const;

export default DeviceSelector;

