import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { OverlayToggles, VisibleLayers } from './OverlayToggles';

describe('OverlayToggles', () => {
  const defaultLayers: VisibleLayers = {
    players: true,
    ball: true,
    pitch: true,
    radar: false,
  };

  it('renders all layer checkboxes', () => {
    const onChange = vi.fn();
    render(
      <OverlayToggles visibleLayers={defaultLayers} onChange={onChange} />
    );

    expect(screen.getByText('Players')).toBeInTheDocument();
    expect(screen.getByText('Ball')).toBeInTheDocument();
    expect(screen.getByText('Pitch')).toBeInTheDocument();
    expect(screen.getByText('Radar')).toBeInTheDocument();
  });

  it('reflects initial visible layers state', () => {
    const onChange = vi.fn();
    render(
      <OverlayToggles visibleLayers={defaultLayers} onChange={onChange} />
    );

    expect(screen.getByTestId('toggle-players')).toBeChecked();
    expect(screen.getByTestId('toggle-ball')).toBeChecked();
    expect(screen.getByTestId('toggle-pitch')).toBeChecked();
    expect(screen.getByTestId('toggle-radar')).not.toBeChecked();
  });

  it('calls onChange when players toggle is clicked', async () => {
    const user = userEvent.setup();
    const onChange = vi.fn();
    render(
      <OverlayToggles visibleLayers={defaultLayers} onChange={onChange} />
    );

    await user.click(screen.getByTestId('toggle-players'));

    expect(onChange).toHaveBeenCalledWith({
      ...defaultLayers,
      players: false,
    });
  });

  it('calls onChange when ball toggle is clicked', async () => {
    const user = userEvent.setup();
    const onChange = vi.fn();
    render(
      <OverlayToggles visibleLayers={defaultLayers} onChange={onChange} />
    );

    await user.click(screen.getByTestId('toggle-ball'));

    expect(onChange).toHaveBeenCalledWith({
      ...defaultLayers,
      ball: false,
    });
  });

  it('calls onChange when pitch toggle is clicked', async () => {
    const user = userEvent.setup();
    const onChange = vi.fn();
    render(
      <OverlayToggles visibleLayers={defaultLayers} onChange={onChange} />
    );

    await user.click(screen.getByTestId('toggle-pitch'));

    expect(onChange).toHaveBeenCalledWith({
      ...defaultLayers,
      pitch: false,
    });
  });

  it('calls onChange when radar toggle is clicked', async () => {
    const user = userEvent.setup();
    const onChange = vi.fn();
    render(
      <OverlayToggles visibleLayers={defaultLayers} onChange={onChange} />
    );

    await user.click(screen.getByTestId('toggle-radar'));

    expect(onChange).toHaveBeenCalledWith({
      ...defaultLayers,
      radar: true,
    });
  });

  it('disables all checkboxes when disabled prop is true', () => {
    const onChange = vi.fn();
    render(
      <OverlayToggles
        visibleLayers={defaultLayers}
        onChange={onChange}
        disabled={true}
      />
    );

    expect(screen.getByTestId('toggle-players')).toBeDisabled();
    expect(screen.getByTestId('toggle-ball')).toBeDisabled();
    expect(screen.getByTestId('toggle-pitch')).toBeDisabled();
    expect(screen.getByTestId('toggle-radar')).toBeDisabled();
  });

  it('maintains other layers when toggling one', async () => {
    const user = userEvent.setup();
    const onChange = vi.fn();
    const allDisabled: VisibleLayers = {
      players: false,
      ball: false,
      pitch: false,
      radar: false,
    };
    render(
      <OverlayToggles visibleLayers={allDisabled} onChange={onChange} />
    );

    await user.click(screen.getByTestId('toggle-players'));

    expect(onChange).toHaveBeenCalledWith({
      players: true,
      ball: false,
      pitch: false,
      radar: false,
    });
  });

  it('handles rapid toggle clicks', async () => {
    const user = userEvent.setup();
    const onChange = vi.fn();
    render(
      <OverlayToggles visibleLayers={defaultLayers} onChange={onChange} />
    );

    await user.click(screen.getByTestId('toggle-players'));
    await user.click(screen.getByTestId('toggle-ball'));
    await user.click(screen.getByTestId('toggle-radar'));

    expect(onChange).toHaveBeenCalledTimes(3);
  });
});
