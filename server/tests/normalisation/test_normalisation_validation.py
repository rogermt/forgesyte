"""TEST-CHANGE: Validation tests for normalisation layer — Step 3.

Tests error handling and edge cases.
"""

import pytest

from app.schemas.normalisation import normalise_output


class TestValidationErrors:
    """Tests that invalid inputs raise appropriate errors."""

    def test_normalisation_rejects_missing_boxes(self):
        """Verify missing 'boxes' raises error."""
        raw = {"scores": [0.9], "labels": ["player"]}

        with pytest.raises((IndexError, KeyError, ValueError)):
            normalise_output(raw)

    def test_normalisation_rejects_missing_scores(self):
        """Verify missing 'scores' raises error."""
        raw = {"boxes": [[10, 20, 30, 40]], "labels": ["player"]}

        with pytest.raises((IndexError, ValueError)):
            normalise_output(raw)

    def test_normalisation_rejects_missing_labels(self):
        """Verify missing 'labels' raises error."""
        raw = {"boxes": [[10, 20, 30, 40]], "scores": [0.9]}

        with pytest.raises((IndexError, ValueError)):
            normalise_output(raw)

    def test_normalisation_rejects_mismatched_lengths(self):
        """Verify boxes/scores/labels must have same length."""
        raw = {
            "boxes": [[10, 20, 30, 40], [50, 60, 70, 80]],
            "scores": [0.9],  # Only 1, but 2 boxes
            "labels": ["player"],  # Only 1, but 2 boxes
        }

        with pytest.raises((IndexError, ValueError)):
            normalise_output(raw)

    def test_normalisation_rejects_invalid_box_coordinates(self):
        """Verify boxes with wrong number of coords raise error."""
        raw = {
            "boxes": [[10, 20, 30]],  # Only 3, need 4
            "scores": [0.9],
            "labels": ["player"],
        }

        with pytest.raises((IndexError, ValueError, TypeError)):
            normalise_output(raw)

    def test_normalisation_rejects_negative_scores(self):
        """Verify negative scores raise error."""
        raw = {
            "boxes": [[10, 20, 30, 40]],
            "scores": [-0.1],  # Invalid: < 0
            "labels": ["player"],
        }

        with pytest.raises(ValueError):
            normalise_output(raw)

    def test_normalisation_rejects_scores_over_one(self):
        """Verify scores > 1.0 raise error."""
        raw = {
            "boxes": [[10, 20, 30, 40]],
            "scores": [1.1],  # Invalid: > 1
            "labels": ["player"],
        }

        with pytest.raises(ValueError):
            normalise_output(raw)

    def test_normalisation_rejects_empty_outputs(self):
        """Verify empty boxes/scores/labels raises error."""
        raw = {"boxes": [], "scores": [], "labels": []}

        with pytest.raises(ValueError):
            normalise_output(raw)
