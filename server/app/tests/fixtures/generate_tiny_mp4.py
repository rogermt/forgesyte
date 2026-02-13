#!/usr/bin/env python3
"""Generate tiny.mp4 fixture for Phase 15 tests.

This script creates a 3-frame MP4 video at 320×240 resolution
for use in unit and integration tests.

Usage:
    python generate_tiny_mp4.py

Output:
    tiny.mp4 (in same directory as this script)
"""

import numpy as np
import cv2
from pathlib import Path


def generate_tiny_mp4(output_path: Path, num_frames: int = 3, width: int = 320, height: int = 240) -> None:
    """Generate a tiny MP4 video for testing.

    Args:
        output_path: Path to write the MP4 file
        num_frames: Number of frames to generate (default: 3)
        width: Frame width in pixels (default: 320)
        height: Frame height in pixels (default: 240)
    """
    # Define video codec and writer
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    fps = 1  # 1 frame per second for simplicity
    out = cv2.VideoWriter(str(output_path), fourcc, fps, (width, height))

    if not out.isOpened():
        raise RuntimeError(f"Failed to open video writer for {output_path}")

    try:
        # Generate num_frames simple frames
        for frame_idx in range(num_frames):
            # Create a simple frame with a color gradient and frame number
            frame = np.zeros((height, width, 3), dtype=np.uint8)

            # Add a gradient background (based on frame index)
            color_intensity = int(255 * frame_idx / num_frames)
            frame[:, :, frame_idx % 3] = color_intensity

            # Add frame number text
            text = f"Frame {frame_idx}"
            cv2.putText(
                frame,
                text,
                (50, 100),
                cv2.FONT_HERSHEY_SIMPLEX,
                1.0,
                (255, 255, 255),
                2,
            )

            # Write frame to video
            out.write(frame)

        print(f"✅ Generated {output_path} ({num_frames} frames, {width}×{height})")
    finally:
        out.release()


if __name__ == "__main__":
    # Generate tiny.mp4 in the same directory as this script
    script_dir = Path(__file__).resolve().parent
    output_file = script_dir / "tiny.mp4"

    generate_tiny_mp4(output_file)

    # Verify the file was created and can be read
    cap = cv2.VideoCapture(str(output_file))
    if not cap.isOpened():
        raise RuntimeError(f"Failed to open generated video: {output_file}")

    frame_count = 0
    while cap.read()[0]:
        frame_count += 1
    cap.release()

    assert frame_count == 3, f"Expected 3 frames, got {frame_count}"
    print(f"✅ Verified: {frame_count} frames readable")
