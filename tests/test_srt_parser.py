# Copyright (c) 2025 Biasware LLC
# Proprietary and Confidential. All Rights Reserved.
# This file is the sole property of Biasware LLC.
# Unauthorized use, distribution, or reverse engineering is prohibited.

"""Tests for indexing.srt_parser parsing function."""

from indexing.srt_parser import load_srt_text, parse_srt_with_timestamps


def test_parse_srt_with_timestamps(tmp_path):
    srt = """1\n00:00:00,000 --> 00:00:02,000\nHello world\n\n2\n00:00:02,000 --> 00:00:03,500\nNext line\nWith wrap\n"""
    p = tmp_path / "sample.srt"
    p.write_text(srt, encoding="utf-8")

    segs = parse_srt_with_timestamps(str(p))
    assert len(segs) == 2
    assert segs[0]["sequence"] == "1"
    assert segs[0]["start_time"] == "00:00:00,000"
    assert segs[0]["end_time"] == "00:00:02,000"
    assert segs[0]["text"] == "Hello world"
    assert 1.99 < segs[0]["duration"] < 2.01

    assert segs[1]["sequence"] == "2"
    assert "Next line With wrap" == segs[1]["text"]


def test_load_srt_text_basic(tmp_path):
    srt = """1\n00:00:01,000 --> 00:00:03,000\nHello world!\n\n2\n00:00:03,500 --> 00:00:05,000\nThis is a test."""
    p = tmp_path / "basic.srt"
    p.write_text(srt, encoding="utf-8")
    result = load_srt_text(str(p))
    assert result == "Hello world! This is a test."


def test_load_srt_text_empty(tmp_path):
    srt = ""
    p = tmp_path / "empty.srt"
    p.write_text(srt, encoding="utf-8")
    result = load_srt_text(str(p))
    assert result == ""


def test_load_srt_text_multiline_segment(tmp_path):
    srt = """1\n00:00:01,000 --> 00:00:03,000\nHello\nworld!\n\n2\n00:00:03,500 --> 00:00:05,000\nThis is\na test."""
    p = tmp_path / "multi.srt"
    p.write_text(srt, encoding="utf-8")
    result = load_srt_text(str(p))
    assert result == "Hello world! This is a test."


def test_load_srt_text_ignores_nonstandard_blocks(tmp_path):
    srt = """1\n00:00:01,000 --> 00:00:03,000\nHello!\n\nThis is not a valid block\n\n2\n00:00:03,500 --> 00:00:05,000\nBye."""
    p = tmp_path / "nonstandard.srt"
    p.write_text(srt, encoding="utf-8")
    result = load_srt_text(str(p))
    assert result == "Hello! Bye."
