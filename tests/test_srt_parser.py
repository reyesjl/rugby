"""Tests for indexing.srt_parser parsing function."""

from indexing.srt_parser import parse_srt_with_timestamps


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
