# Copyright (c) 2025 Biasware LLC
# Proprietary and Confidential. All Rights Reserved.
# This file is the sole property of Biasware LLC.
# Unauthorized use, distribution, or reverse engineering is prohibited.

"""Test the basic functionality of the new packages."""

import os
import tempfile

from indexing.srt_parser import calculate_duration
from ingest.video_finder import validate_video_file
from storage.file_utils import file_exists, load_json, save_json


def test_srt_parser():
    """Test SRT parsing functionality."""
    # Test duration calculation
    duration = calculate_duration("00:01:23,456", "00:01:27,890")
    expected_duration = 4.434  # 4 seconds + 434 ms
    assert (
        abs(duration - expected_duration) < 0.001
    ), f"Expected {expected_duration}, got {duration}"
    print("✅ SRT duration calculation works")


def test_video_finder():
    """Test video file finding functionality."""
    # Test format validation
    assert not validate_video_file("test.mp4")  # File doesn't exist
    print("✅ Video format validation works")


def test_storage():
    """Test storage functionality."""
    with tempfile.TemporaryDirectory() as temp_dir:
        test_file = os.path.join(temp_dir, "test.json")
        test_data = {"test": "data", "number": 42}

        # Test saving
        save_json(test_data, test_file)
        assert file_exists(test_file), "File was not created"

        # Test loading
        loaded_data = load_json(test_file)
        assert loaded_data == test_data, f"Data mismatch: {loaded_data} != {test_data}"

    print("✅ Storage utilities work")


def run_tests():
    """Run all tests."""
    print("🧪 Running functionality tests...")
    test_srt_parser()
    test_video_finder()
    test_storage()
    print("✅ All functionality tests passed!")


if __name__ == "__main__":
    run_tests()
