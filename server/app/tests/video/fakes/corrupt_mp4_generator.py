"""Generate corrupted MP4 files for fuzz testing.

This module provides utilities to create intentionally malformed MP4 files
for testing error handling in the video processing pipeline.
"""

import os
from pathlib import Path


def create_corrupt_mp4_header_only(output_path: Path) -> None:
    """Create a file with valid MP4 header but invalid data.

    Args:
        output_path: Path to write the corrupted file
    """
    # Minimal MP4 header (ftyp box)
    # This is enough to make OpenCV attempt to open it, but it will fail
    # when trying to read frames
    header = bytes([
        0x00, 0x00, 0x00, 0x20,  # Box size (32 bytes)
        0x66, 0x74, 0x79, 0x70,  # 'ftyp' signature
        0x69, 0x73, 0x6f, 0x6d,  # Major brand: 'isom'
        0x00, 0x00, 0x00, 0x00,  # Minor version
        0x69, 0x73, 0x6f, 0x6d,  # Compatible brand
        0x6d, 0x64, 0x61, 0x74,  # 'mdat' signature
        0x69, 0x73, 0x6f, 0x32,  # More compatible brands
        0x67, 0x33, 0x67, 0x70,
        0x6d, 0x70, 0x34, 0x31,
    ])

    with open(output_path, "wb") as f:
        f.write(header)


def create_corrupt_mp4_random_bytes(output_path: Path, size: int = 256) -> None:
    """Create a file with random bytes (not a valid MP4).

    Args:
        output_path: Path to write the corrupted file
        size: Size of the file in bytes (default: 256)
    """
    import os
    random_data = os.urandom(size)
    with open(output_path, "wb") as f:
        f.write(random_data)


def create_corrupt_mp4_truncated(output_path: Path) -> None:
    """Create a file that looks like MP4 but is truncated mid-stream.

    Args:
        output_path: Path to write the corrupted file
    """
    # Start with a valid MP4 header
    header = bytes([
        0x00, 0x00, 0x00, 0x20,  # Box size
        0x66, 0x74, 0x79, 0x70,  # 'ftyp'
        0x69, 0x73, 0x6f, 0x6d,  # 'isom'
        0x00, 0x00, 0x00, 0x00,
        0x69, 0x73, 0x6f, 0x6d,
        0x6d, 0x64, 0x61, 0x74,
        0x69, 0x73, 0x6f, 0x32,
    ])

    # Add a moov box header that claims to have data but doesn't
    moov_header = bytes([
        0x00, 0x00, 0x10, 0x00,  # Claims 4096 bytes
        0x6d, 0x6f, 0x6f, 0x76,  # 'moov' signature
    ])

    with open(output_path, "wb") as f:
        f.write(header)
        f.write(moov_header)
        # Write only partial data, not the claimed 4096 bytes
        f.write(bytes([0x00] * 16))


def verify_corrupt_mp4_fails_to_open(file_path: Path) -> bool:
    """Verify that OpenCV cannot open the corrupted MP4.

    Args:
        file_path: Path to the (corrupted) MP4 file

    Returns:
        True if OpenCV fails to open it (as expected)
    """
    import cv2

    cap = cv2.VideoCapture(str(file_path))
    result = not cap.isOpened()
    cap.release()
    return result
