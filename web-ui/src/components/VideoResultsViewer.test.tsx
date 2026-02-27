import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { VideoResultsViewer } from './VideoResultsViewer';

describe('VideoResultsViewer', () => {
  beforeEach(() => {
    // Stub env variable for tests
    vi.stubEnv('VITE_API_URL', '/v1');
  });

  const mockResults = {
    total_frames: 3,
    frames: [
      {
        frame_index: 0,
        detections: {
          tracked_objects: [
            {
              track_id: 1,
              class_id: 2,
              xyxy: [10, 20, 30, 40],
              center: [20, 30],
            },
          ],
        },
      },
      { frame_index: 1, detections: { tracked_objects: [] } },
      { frame_index: 2, detections: { tracked_objects: [] } },
    ],
  };

  it('renders video element with correct src', () => {
    render(<VideoResultsViewer jobId="job-123" results={mockResults} />);
    // Video elements don't have an implicit role, query by tag name
    const video = document.querySelector('video');
    expect(video).toBeDefined();
    expect(video?.getAttribute('src')).toBe('/v1/jobs/job-123/video');
  });

  it('renders JSON output with total_frames', () => {
    render(<VideoResultsViewer jobId="job-123" results={mockResults} />);
    expect(screen.getByText(/total_frames/)).toBeDefined();
  });

  it('renders overlay canvas for detections', () => {
    render(<VideoResultsViewer jobId="job-123" results={mockResults} />);
    // Canvas elements don't have roles by default, so query by tag
    const canvas = document.querySelector('canvas');
    expect(canvas).toBeDefined();
    expect(canvas?.width).toBe(1280);
    expect(canvas?.height).toBe(720);
  });

  it('renders frame timeline slider', () => {
    render(<VideoResultsViewer jobId="job-123" results={mockResults} />);
    const slider = screen.getByRole('slider', { hidden: true });
    expect(slider).toBeDefined();
    expect(slider.getAttribute('min')).toBe('0');
    expect(slider.getAttribute('max')).toBe('2'); // total_frames - 1
  });

  it('handles empty frames array', () => {
    render(
      <VideoResultsViewer
        jobId="job-456"
        results={{ total_frames: 0, frames: [] }}
      />
    );
    // Video element should still render even without frames
    const video = document.querySelector('video');
    expect(video).toBeDefined();
    // No slider should render when total_frames is 0
    const slider = document.querySelector('input[type="range"]');
    expect(slider).toBeNull();
  });
});
