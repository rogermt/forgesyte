"""TEST-CHANGE: Basic tests for normalisation layer — Step 3.

Tests canonical normalisation schema transformation.
"""

from app.schemas.normalisation import normalise_output


def test_normalisation_produces_canonical_schema():
    """Verify normalise_output produces canonical schema with frames[]."""
    raw = {
        "boxes": [[10, 20, 30, 40]],
        "scores": [0.9],
        "labels": ["player"],
    }

    out = normalise_output(raw)

    assert "frames" in out, "Normalised output must contain frames[]"
    assert len(out["frames"]) == 1

    frame = out["frames"][0]

    assert "boxes" in frame
    assert "scores" in frame
    assert "labels" in frame

    box = frame["boxes"][0]
    assert set(box.keys()) == {
        "x1",
        "y1",
        "x2",
        "y2",
    }, "Boxes must be dicts with canonical keys"


def test_normalisation_boxes_are_dicts():
    """Verify boxes are dicts with {x1, y1, x2, y2}."""
    raw = {
        "boxes": [[10, 20, 30, 40], [50, 60, 70, 80]],
        "scores": [0.9, 0.8],
        "labels": ["player", "player"],
    }

    out = normalise_output(raw)
    frame = out["frames"][0]

    assert len(frame["boxes"]) == 2
    for box in frame["boxes"]:
        assert isinstance(box, dict)
        assert set(box.keys()) == {"x1", "y1", "x2", "y2"}
        assert all(isinstance(v, (int, float)) for v in box.values())


def test_normalisation_scores_are_floats():
    """Verify scores are floats in [0, 1]."""
    raw = {
        "boxes": [[10, 20, 30, 40]],
        "scores": [0.95],
        "labels": ["player"],
    }

    out = normalise_output(raw)
    frame = out["frames"][0]

    assert len(frame["scores"]) == 1
    assert isinstance(frame["scores"][0], float)
    assert 0 <= frame["scores"][0] <= 1


def test_normalisation_labels_are_strings():
    """Verify labels are strings."""
    raw = {
        "boxes": [[10, 20, 30, 40]],
        "scores": [0.9],
        "labels": ["player"],
    }

    out = normalise_output(raw)
    frame = out["frames"][0]

    assert len(frame["labels"]) == 1
    assert isinstance(frame["labels"][0], str)
