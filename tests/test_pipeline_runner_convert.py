"""Tests for PipelineRunner.convert_videos behavior."""

from unittest.mock import MagicMock, patch

from core.pipeline_models import VideoProcessingConfig
from core.pipeline_runner import PipelineRunner


def minimal_config():
    return {
        "sources": [
            {
                "type": "linux_desktop",
                "path": "/videos",
                "watch_patterns": ["mp4", "avi"],
            }
        ],
        "conversion": {
            "ffmpeg": {
                "video_codec": "libx264",
                "crf": 23,
                "preset": "fast",
                "audio_codec": "aac",
                "audio_bitrate": "128k",
            },
            "parallel_workers": 1,
        },
        "indexing": {"ai_provider": "openai", "model": "gpt-4o-mini", "batch_size": 1},
    }


def test_convert_videos_passthrough_mp4():
    config = VideoProcessingConfig(minimal_config())
    runner = PipelineRunner(config)
    out = runner.convert_videos(["/v/a.mp4"])
    assert out == ["/v/a.mp4"]


@patch("core.pipeline_runner.subprocess.run")
def test_convert_videos_converts_non_mp4(mock_run):
    mock_run.return_value = MagicMock()
    config = VideoProcessingConfig(minimal_config())
    runner = PipelineRunner(config)
    out = runner.convert_videos(["/v/b.avi"])
    assert out == ["/v/b_converted.mp4"]
    assert mock_run.call_count == 1


@patch("core.pipeline_runner.subprocess.run")
def test_convert_videos_skips_on_ffmpeg_failure(mock_run):
    import subprocess as sp

    mock_run.side_effect = sp.CalledProcessError(
        returncode=1, cmd=["ffmpeg"], stderr=b"err"
    )
    config = VideoProcessingConfig(minimal_config())
    runner = PipelineRunner(config)
    out = runner.convert_videos(["/v/c.mkv"])
    assert out == []
