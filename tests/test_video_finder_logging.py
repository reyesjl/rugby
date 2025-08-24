# Copyright (c) 2025 Biasware LLC
# Proprietary and Confidential. All Rights Reserved.
# This file is the sole property of Biasware LLC.
# Unauthorized use, distribution, or reverse engineering is prohibited.

"""Tests for ingest.video_finder non-recursive branch logging of unsupported files."""

from ingest import video_finder


def test_non_recursive_logs_skipped_files(tmp_path, caplog):
    caplog.set_level("DEBUG")
    # Create supported and unsupported files in top-level only
    (tmp_path / "a.mp4").write_text("x")
    (tmp_path / "b.txt").write_text("x")

    result = video_finder.find_video_files(str(tmp_path), ["mp4"], recursive=False)

    # Only a.mp4 is returned
    assert len(result) == 1 and result[0].endswith("a.mp4")
    # b.txt is logged as skipped
    logs = "\n".join(r.message for r in caplog.records)
    assert "Skipping unsupported video file: b.txt" in logs
