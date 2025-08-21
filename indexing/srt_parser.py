# Copyright (c) 2025 Biasware LLC
# Proprietary and Confidential. All Rights Reserved.
# This file is the sole property of Biasware LLC.
# Unauthorized use, distribution, or reverse engineering is prohibited.

"""Core utilities for processing SRT transcript files."""


def calculate_duration(start_time: str, end_time: str) -> float:
    """Calculate duration in seconds from SRT timestamps.

    Args:
        start_time: Start timestamp in format "00:01:23,456"
        end_time: End timestamp in format "00:01:27,890"

    Returns:
        Duration in seconds as float
    """

    def parse_timestamp(ts: str) -> float:
        # Handle format "00:01:23,456"
        time_part, ms_part = ts.split(",")
        h, m, s = map(int, time_part.split(":"))
        ms = int(ms_part)
        return h * 3600 + m * 60 + s + ms / 1000.0

    start_seconds = parse_timestamp(start_time)
    end_seconds = parse_timestamp(end_time)
    return end_seconds - start_seconds


def parse_srt_with_timestamps(srt_path: str) -> list[dict]:
    """Extract timestamped segments from SRT files.

    Args:
        srt_path: Path to SRT transcript file

    Returns:
        List of segment dictionaries with timestamps and text
    """
    with open(srt_path, encoding="utf-8") as f:
        content = f.read()

    segments = []
    blocks = content.strip().split("\n\n")

    for block in blocks:
        lines = block.strip().split("\n")
        if len(lines) >= 3:
            sequence_num = lines[0]
            timestamp = lines[1]
            text = " ".join(lines[2:])

            # Parse timestamp "00:01:23,456 --> 00:01:27,890"
            start_time, end_time = timestamp.split(" --> ")

            segments.append(
                {
                    "sequence": sequence_num,
                    "start_time": start_time,
                    "end_time": end_time,
                    "text": text,
                    "duration": calculate_duration(start_time, end_time),
                }
            )

    return segments

def load_srt_text(srt_path: str) -> str:
    """Load the text content from an SRT file.

    Args:
        srt_path: Path to the SRT transcript file

    Returns:
        The combined text content of all segments
    """
    segments = parse_srt_with_timestamps(srt_path)
    return " ".join(segment["text"] for segment in segments)

