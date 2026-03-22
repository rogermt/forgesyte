"""Test derive_video_summary function for defensive coding.

Discussion #353: Tests for malformed data handling.
Discussion #357: Tests for YOLO tracked_objects format in merged multi-tool frames.
"""

from app.services.video_summary_service import derive_video_summary


class TestDeriveVideoSummaryDefensive:
    """Tests for defensive handling of malformed data in derive_video_summary."""

    # Tests for frames array (lines 66-71)
    def test_frames_with_non_dict_items_skips_safely(self):
        """Should skip frame items that are not dicts."""
        results = {
            "frames": [
                {"detections": [{"class": "player"}]},  # Valid
                "not a dict",  # Invalid - should be skipped
                123,  # Invalid - should be skipped
                None,  # Invalid - should be skipped
                {"detections": [{"class": "ball"}]},  # Valid
            ]
        }
        summary = derive_video_summary(results)
        assert summary["frame_count"] == 5
        assert summary["detection_count"] == 2  # Only from valid frames
        assert summary["classes"] == ["ball", "player"]

    def test_frames_with_non_list_detections_skips_safely(self):
        """Should handle detections that are not a list."""
        results = {
            "frames": [
                {"detections": [{"class": "player"}]},  # Valid
                {"detections": "not a list"},  # Invalid detections
                {"detections": {"nested": "dict"}},  # Invalid detections
                {"detections": None},  # Invalid detections
            ]
        }
        summary = derive_video_summary(results)
        assert summary["detection_count"] == 1  # Only from valid detection
        assert summary["classes"] == ["player"]

    def test_frames_with_non_dict_detections_skips_safely(self):
        """Should handle detection items that are not dicts."""
        results = {
            "frames": [
                {
                    "detections": [
                        {"class": "player"},  # Valid
                        "not a dict",  # Invalid - should be skipped
                        123,  # Invalid - should be skipped
                        {"class": "ball"},  # Valid
                    ]
                }
            ]
        }
        summary = derive_video_summary(results)
        assert summary["detection_count"] == 4  # All items counted (len of list)
        assert summary["classes"] == ["ball", "player"]  # Only from valid dicts

    def test_frames_empty_list(self):
        """Should handle empty frames list."""
        results = {"frames": []}
        summary = derive_video_summary(results)
        assert summary["frame_count"] == 0
        assert summary["detection_count"] == 0
        assert summary["classes"] == []

    def test_frames_missing_detections_key(self):
        """Should handle frames without detections key."""
        results = {"frames": [{"other_key": "value"}]}
        summary = derive_video_summary(results)
        assert summary["detection_count"] == 0
        assert summary["classes"] == []

    # Tests for tools structure (lines 94-100) - video_multi jobs
    def test_tool_frames_with_non_dict_items_skips_safely(self):
        """Should skip tool frame items that are not dicts."""
        results = {
            "tools": {
                "tracker": {
                    "frames": [
                        {"detections": [{"class": "player"}]},  # Valid
                        "not a dict",  # Invalid - should be skipped
                        {"detections": [{"class": "ball"}]},  # Valid
                    ]
                }
            }
        }
        summary = derive_video_summary(results)
        assert summary["detection_count"] == 2  # Only from valid frames
        assert summary["classes"] == ["ball", "player"]

    def test_tool_frames_with_non_list_detections_skips_safely(self):
        """Should handle tool detections that are not a list."""
        results = {
            "tools": {
                "tracker": {
                    "frames": [
                        {"detections": [{"class": "player"}]},  # Valid
                        {"detections": "not a list"},  # Invalid
                    ]
                }
            }
        }
        summary = derive_video_summary(results)
        assert summary["detection_count"] == 1
        assert summary["classes"] == ["player"]

    def test_tool_frames_with_non_dict_detections_skips_safely(self):
        """Should handle tool detection items that are not dicts."""
        results = {
            "tools": {
                "tracker": {
                    "frames": [
                        {
                            "detections": [
                                {"class": "player"},  # Valid
                                "not a dict",  # Invalid - should be skipped
                                {"class": "ball"},  # Valid
                            ]
                        }
                    ]
                }
            }
        }
        summary = derive_video_summary(results)
        assert summary["detection_count"] == 3  # len of list
        assert summary["classes"] == ["ball", "player"]  # Only from valid dicts

    def test_tool_results_non_dict_skips_safely(self):
        """Should skip tool_results that are not dicts."""
        results = {
            "tools": {
                "tracker": "not a dict",  # Invalid
                "detector": {"frames": [{"detections": [{"class": "ball"}]}]},  # Valid
            }
        }
        summary = derive_video_summary(results)
        assert summary["detection_count"] == 1
        assert summary["classes"] == ["ball"]

    def test_tool_frames_non_list_skips_safely(self):
        """Should skip tool_frames that are not a list."""
        results = {
            "tools": {
                "tracker": {"frames": "not a list"},  # Invalid
                "detector": {"frames": [{"detections": [{"class": "ball"}]}]},  # Valid
            }
        }
        summary = derive_video_summary(results)
        assert summary["detection_count"] == 1
        assert summary["classes"] == ["ball"]

    # Test for video_multi merged frames structure (Issue #6)
    def test_video_multi_merged_frames_structure(self):
        """Should parse video_multi results from _merge_video_frames format.

        _merge_video_frames produces:
        {
            "frames": [
                {"frame_idx": 0, "player_tracker": {...}, "ball_detector": {...}}
            ]
        }
        """
        results = {
            "frames": [
                {
                    "frame_idx": 0,
                    "player_tracker": {
                        "detections": [{"class": "player"}, {"class": "player"}]
                    },
                    "ball_detector": {"detections": [{"class": "ball"}]},
                },
                {
                    "frame_idx": 1,
                    "player_tracker": {"detections": [{"class": "player"}]},
                    "ball_detector": {"detections": []},
                },
            ]
        }
        summary = derive_video_summary(results)
        assert summary["frame_count"] == 2
        assert summary["detection_count"] == 4  # 2+1+1
        assert summary["classes"] == ["ball", "player"]

    # Edge cases
    def test_empty_results(self):
        """Should handle empty results dict."""
        results = {}
        summary = derive_video_summary(results)
        assert summary["frame_count"] == 0
        assert summary["detection_count"] == 0
        assert summary["classes"] == []

    def test_results_with_only_frames_no_tools(self):
        """Should handle results with only frames (no tools)."""
        results = {
            "frames": [{"detections": [{"class": "player"}]}],
        }
        summary = derive_video_summary(results)
        assert summary["frame_count"] == 1
        assert summary["detection_count"] == 1
        assert summary["classes"] == ["player"]

    def test_results_with_only_tools_no_frames(self):
        """Should handle results with only tools (no top-level frames)."""
        results = {
            "tools": {"tracker": {"frames": [{"detections": [{"class": "player"}]}]}}
        }
        summary = derive_video_summary(results)
        assert summary["frame_count"] == 0
        assert summary["detection_count"] == 1
        assert summary["classes"] == ["player"]

    # TDD: Tests for YOLO tracked_objects format (Discussion #357)
    def test_derive_video_summary_handles_tracked_objects_format(self):
        """Should handle YOLO's tracked_objects format.

        YOLO tracker produces:
        {"detections": {"tracked_objects": [{"class": "player"}]}}
        instead of:
        {"detections": [{"class": "player"}]}
        """
        results = {
            "frames": [
                {
                    "frame_index": 0,
                    "detections": {"tracked_objects": [{"class": "player"}]},
                },
                {
                    "frame_index": 1,
                    "detections": {
                        "tracked_objects": [{"class": "ball"}, {"class": "player"}]
                    },
                },
            ]
        }
        summary = derive_video_summary(results)
        assert summary["frame_count"] == 2
        assert summary["detection_count"] == 3
        assert summary["classes"] == ["ball", "player"]

    def test_derive_video_summary_mixed_detection_formats(self):
        """Should handle mixed formats in same results.

        Some tools produce list format, others produce tracked_objects format.
        """
        results = {
            "frames": [
                {"frame_idx": 0, "detections": [{"class": "person"}]},  # List format
                {
                    "frame_index": 1,
                    "detections": {"tracked_objects": [{"class": "car"}]},
                },  # Dict format
            ]
        }
        summary = derive_video_summary(results)
        assert summary["frame_count"] == 2
        assert summary["detection_count"] == 2
        assert summary["classes"] == ["car", "person"]

    # TDD: Test for YOLO tracked_objects in merged multi-tool frames (Discussion #357)
    def test_merged_frames_with_tracked_objects_format(self):
        """Should handle YOLO tracked_objects in merged multi-tool frame format.

        YOLO tracker produces: {"detections": {"tracked_objects": [...]}}
        Merged frames have: frame["tool_name"]["detections"]
        This is the REAL production format that was failing.
        """
        results = {
            "frames": [
                {
                    "frame_idx": 0,
                    "player_tracker": {
                        "detections": {"tracked_objects": [{"class": "player"}]}
                    },
                },
                {
                    "frame_idx": 1,
                    "player_tracker": {
                        "detections": {
                            "tracked_objects": [
                                {"class": "ball"},
                                {"class": "player"},
                            ]
                        }
                    },
                },
            ]
        }
        summary = derive_video_summary(results)
        assert summary["frame_count"] == 2
        assert summary["detection_count"] == 3  # 1 + 2
        assert summary["classes"] == ["ball", "player"]

    # TDD: Test multiple tools with tracked_objects in merged format
    def test_merged_frames_multiple_tools_with_tracked_objects(self):
        """Should handle multiple tools each with tracked_objects format."""
        results = {
            "frames": [
                {
                    "frame_idx": 0,
                    "player_tracker": {
                        "detections": {"tracked_objects": [{"class": "player"}]}
                    },
                    "ball_detector": {
                        "detections": {"tracked_objects": [{"class": "ball"}]}
                    },
                },
            ]
        }
        summary = derive_video_summary(results)
        assert summary["frame_count"] == 1
        assert summary["detection_count"] == 2  # 1 player + 1 ball
        assert summary["classes"] == ["ball", "player"]

    # TDD: Test for YOLO class_id format (integer, not string)
    # Discussion #357: YOLO plugin now outputs BOTH class_id AND class
    def test_merged_frames_with_class_id_integer_format(self):
        """Should handle YOLO's class_id (integer) format with class name.

        Real YOLO plugin now outputs:
        {"track_id": 1, "class_id": 0, "class": "player", "xyxy": [...]}

        The "class" field is the human-readable name from CLASS_NAMES mapping.
        """
        results = {
            "frames": [
                {
                    "frame_idx": 0,
                    "player_tracker": {
                        "detections": {
                            "tracked_objects": [
                                {
                                    "track_id": 1,
                                    "class_id": 0,
                                    "class": "player",
                                    "xyxy": [1, 2, 3, 4],
                                },
                                {
                                    "track_id": 2,
                                    "class_id": 1,
                                    "class": "goalkeeper",
                                    "xyxy": [5, 6, 7, 8],
                                },
                            ]
                        }
                    },
                },
                {
                    "frame_idx": 1,
                    "player_tracker": {
                        "detections": {
                            "tracked_objects": [
                                {
                                    "track_id": 1,
                                    "class_id": 0,
                                    "class": "player",
                                    "xyxy": [1, 2, 3, 4],
                                },
                            ]
                        }
                    },
                },
            ]
        }
        summary = derive_video_summary(results)
        assert summary["frame_count"] == 2
        assert summary["detection_count"] == 3
        assert "player" in summary["classes"]
        assert "goalkeeper" in summary["classes"]
