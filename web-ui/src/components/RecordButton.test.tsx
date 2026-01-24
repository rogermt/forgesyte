import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { RecordButton } from './RecordButton';

describe('RecordButton', () => {
  beforeEach(() => {
    // Mock basic browser APIs
    if (!global.MediaStream) {
      global.MediaStream = class {
        constructor() {}
        getTracks() { return []; }
        getAudioTracks() { return []; }
        getVideoTracks() { return []; }
      } as unknown as typeof MediaStream;
    }
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  it('renders button with initial text', () => {
    const canvas = document.createElement('canvas');
    const video = document.createElement('video');
    render(<RecordButton canvas={canvas} videoElement={video} />);
    expect(screen.getByTestId('record-button')).toHaveTextContent('Start Recording');
  });

  it('disables button when canvas is null', () => {
    const video = document.createElement('video');
    render(<RecordButton canvas={null} videoElement={video} />);
    expect(screen.getByTestId('record-button')).toBeDisabled();
  });

  it('disables button when video element is null', () => {
    const canvas = document.createElement('canvas');
    render(<RecordButton canvas={canvas} videoElement={null} />);
    expect(screen.getByTestId('record-button')).toBeDisabled();
  });

  it('disables button when disabled prop is true', () => {
    const canvas = document.createElement('canvas');
    const video = document.createElement('video');
    render(
      <RecordButton canvas={canvas} videoElement={video} disabled={true} />
    );
    expect(screen.getByTestId('record-button')).toBeDisabled();
  });

  it('renders with default filename', () => {
    const canvas = document.createElement('canvas');
    const video = document.createElement('video');
    render(<RecordButton canvas={canvas} videoElement={video} filename="test" />);
    expect(screen.getByTestId('record-button')).toBeInTheDocument();
  });
});
