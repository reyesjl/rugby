# Copyright (c) 2025 Biasware LLC
# Proprietary and Confidential. All Rights Reserved.
# This file is the sole property of Biasware LLC.
# Unauthorized use, distribution, or reverse engineering is prohibited.

"""Tests for convert_mp4_to_wav utility function."""

import os
from unittest.mock import MagicMock, patch

import pytest

from core.pipeline_runner import convert_mp4_to_wav


def test_convert_mp4_to_wav_raises_on_non_mp4():
    with pytest.raises(ValueError):
        convert_mp4_to_wav("/tmp/input.avi")


@patch("core.pipeline_runner.subprocess.run")
def test_convert_mp4_to_wav_with_output_dir(mock_run, tmp_path):
    mock_run.return_value = MagicMock()
    out = convert_mp4_to_wav("/data/video.mp4", output_dir=str(tmp_path))
    # Should place file under provided dir with .wav extension
    assert out == os.path.join(str(tmp_path), "video.wav")
    mock_run.assert_called_once()


@patch("core.pipeline_runner.subprocess.run")
def test_convert_mp4_to_wav_without_output_dir(mock_run):
    mock_run.return_value = MagicMock()
    out = convert_mp4_to_wav("/any/where/movie.mp4")
    assert out.endswith("movie.wav")
    mock_run.assert_called_once()
