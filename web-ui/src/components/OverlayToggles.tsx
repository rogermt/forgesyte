import React from 'react';

export interface VisibleLayers {
  players: boolean;
  ball: boolean;
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
    <div className="overlay-toggles">
      <label>
        <input
          type="checkbox"
          checked={visibleLayers.players}
          onChange={() => handleToggle('players')}
          disabled={disabled}
          data-testid="toggle-players"
        />
        Players
      </label>
      <label>
        <input
          type="checkbox"
          checked={visibleLayers.ball}
          onChange={() => handleToggle('ball')}
          disabled={disabled}
          data-testid="toggle-ball"
        />
        Ball
      </label>
      <label>
        <input
          type="checkbox"
          checked={visibleLayers.pitch}
          onChange={() => handleToggle('pitch')}
          disabled={disabled}
          data-testid="toggle-pitch"
        />
        Pitch
      </label>
      <label>
        <input
          type="checkbox"
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
