import React from 'react';
import styles from './OverlayToggles.module.css';

export interface VisibleLayers {
  boxes: boolean;
  labels: boolean;
  pitch: boolean;
  radar: boolean;
}

export interface OverlayTogglesProps {
  visibleLayers: VisibleLayers;
  onChange: (layers: VisibleLayers) => void;
  disabled?: boolean;
}

export const OverlayToggles: React.FC<OverlayTogglesProps> = ({
  visibleLayers,
  onChange,
  disabled = false,
}) => {
  const handleToggle = (layer: keyof VisibleLayers) => {
    onChange({
      ...visibleLayers,
      [layer]: !visibleLayers[layer],
    });
  };

  return (
    <div className={styles.container}>
      <label className={styles.label}>
        <input
          type="checkbox"
          id="toggle-boxes"
          checked={visibleLayers.boxes}
          onChange={() => handleToggle('boxes')}
          disabled={disabled}
          data-testid="toggle-boxes"
        />
        Boxes
      </label>
      <label className={styles.label}>
        <input
          type="checkbox"
          id="toggle-labels"
          checked={visibleLayers.labels}
          onChange={() => handleToggle('labels')}
          disabled={disabled}
          data-testid="toggle-labels"
        />
        Labels
      </label>
      <label className={styles.label}>
        <input
          type="checkbox"
          id="toggle-pitch"
          checked={visibleLayers.pitch}
          onChange={() => handleToggle('pitch')}
          disabled={disabled}
          data-testid="toggle-pitch"
        />
        Pitch
      </label>
      <label className={styles.label}>
        <input
          type="checkbox"
          id="toggle-radar"
          checked={visibleLayers.radar}
          onChange={() => handleToggle('radar')}
          disabled={disabled}
          data-testid="toggle-radar"
        />
        Radar
      </label>
    </div>
  );
};
