# Copyright (c) 2025 Biasware LLC
# Proprietary and Confidential. All Rights Reserved.
# This file is the sole property of Biasware LLC.
# Unauthorized use, distribution, or reverse engineering is prohibited.


import os
import pytest
from ingest import video_finder

def create_file(path):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("dummy")

def test_find_video_files_basic(tmp_path):
    # Create video and non-video files
    video1 = tmp_path / "a.mp4"
    video2 = tmp_path / "b.mpg"
    nonvideo = tmp_path / "c.txt"
    create_file(video1)
    create_file(video2)
    create_file(nonvideo)
    result = video_finder.find_video_files(str(tmp_path), ["mp4", "mpg", "txt"])
    assert str(video1) in result
    assert str(video2) in result
    assert all(not f.endswith(".txt") for f in result)

def test_find_video_files_recursive(tmp_path):
    subdir = tmp_path / "sub"
    video = subdir / "d.avi"
    create_file(video)
    result = video_finder.find_video_files(str(tmp_path), ["avi"], recursive=True)
    assert str(video) in result

def test_find_video_files_non_recursive(tmp_path):
    subdir = tmp_path / "sub"
    video = subdir / "e.mov"
    create_file(video)
    result = video_finder.find_video_files(str(tmp_path), ["mov"], recursive=False)
    assert str(video) not in result

def test_find_video_files_unsupported_format(tmp_path):
    video = tmp_path / "f.xyz"
    create_file(video)
    result = video_finder.find_video_files(str(tmp_path), ["xyz"], recursive=True)
    assert result == []

def test_find_video_files_empty_dir(tmp_path):
    result = video_finder.find_video_files(str(tmp_path), ["mp4"], recursive=True)
    assert result == []

def test_validate_video_file_supported(tmp_path):
    video = tmp_path / "g.mkv"
    create_file(video)
    assert video_finder.validate_video_file(str(video)) is True

def test_validate_video_file_unsupported(tmp_path):
    file = tmp_path / "h.docx"
    create_file(file)
    assert video_finder.validate_video_file(str(file)) is False

def test_validate_video_file_nonexistent(tmp_path):
    file = tmp_path / "i.mp4"
    assert video_finder.validate_video_file(str(file)) is False
