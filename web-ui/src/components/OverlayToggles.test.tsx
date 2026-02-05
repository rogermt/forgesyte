import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { OverlayToggles, VisibleLayers } from './OverlayToggles';

describe('OverlayToggles', () => {
  const defaultLayers: VisibleLayers = {
    boxes: true,
    labels: true,
    pitch: true,
    radar: false,
  };

  it('renders all layer checkboxes', () => {
    const onChange = vi.fn();
    render(
      <OverlayToggles visibleLayers={defaultLayers} onChange={onChange} />
    );

    expect(screen.getByText('Boxes')).toBeInTheDocument();
    expect(screen.getByText('Labels')).toBeInTheDocument();
    expect(screen.getByText('Pitch')).toBeInTheDocument();
    expect(screen.getByText('Radar')).toBeInTheDocument();
  });

  it('reflects initial visible layers state', () => {
    const onChange = vi.fn();
    render(
      <OverlayToggles visibleLayers={defaultLayers} onChange={onChange} />
    );

    expect(screen.getByTestId('toggle-boxes')).toBeChecked();
    expect(screen.getByTestId('toggle-labels')).toBeChecked();
    expect(screen.getByTestId('toggle-pitch')).toBeChecked();
    expect(screen.getByTestId('toggle-radar')).not.toBeChecked();
  });

  it('calls onChange when boxes toggle is clicked', async () => {
    const user = userEvent.setup();
    const onChange = vi.fn();
    render(
      <OverlayToggles visibleLayers={defaultLayers} onChange={onChange} />
    );

    await user.click(screen.getByTestId('toggle-boxes'));

    expect(onChange).toHaveBeenCalledWith({
      ...defaultLayers,
      boxes: false,
    });
  });

  it('calls onChange when labels toggle is clicked', async () => {
    const user = userEvent.setup();
    const onChange = vi.fn();
    render(
      <OverlayToggles visibleLayers={defaultLayers} onChange={onChange} />
    );

    await user.click(screen.getByTestId('toggle-labels'));

    expect(onChange).toHaveBeenCalledWith({
      ...defaultLayers,
      labels: false,
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

    expect(screen.getByTestId('toggle-boxes')).toBeDisabled();
    expect(screen.getByTestId('toggle-labels')).toBeDisabled();
    expect(screen.getByTestId('toggle-pitch')).toBeDisabled();
    expect(screen.getByTestId('toggle-radar')).toBeDisabled();
  });

  it('maintains other layers when toggling one', async () => {
    const user = userEvent.setup();
    const onChange = vi.fn();
    const allDisabled: VisibleLayers = {
      boxes: false,
      labels: false,
      pitch: false,
      radar: false,
    };
    render(
      <OverlayToggles visibleLayers={allDisabled} onChange={onChange} />
    );

    await user.click(screen.getByTestId('toggle-boxes'));

    expect(onChange).toHaveBeenCalledWith({
      boxes: true,
      labels: false,
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

    await user.click(screen.getByTestId('toggle-boxes'));
    await user.click(screen.getByTestId('toggle-labels'));
    await user.click(screen.getByTestId('toggle-radar'));

    expect(onChange).toHaveBeenCalledTimes(3);
  });
});
