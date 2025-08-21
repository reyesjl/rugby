"""Tests for PipelineRunner.run high-level orchestration."""

from unittest.mock import patch

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
        "conversion": {"ffmpeg": {}, "parallel_workers": 1},
        "indexing": {"ai_provider": "openai", "model": "gpt-4o-mini", "batch_size": 1},
        "transcription": {
            "model_size": "tiny",
            "language": "en",
            "device": "cpu",
            "output_dir": None,
            "preserve_tree": True,
        },
    }


@patch("core.pipeline_runner.find_video_files")
@patch.object(
    PipelineRunner, "convert_videos", return_value=["/videos/one.mp4"]
)  # avoid subprocess
@patch.object(PipelineRunner, "transcribe_to_srt", return_value=None)
def test_run_happy_path(mock_transcribe, mock_convert, mock_find):
    mock_find.return_value = ["/videos/one.mp4"]
    cfg = VideoProcessingConfig(minimal_config())
    runner = PipelineRunner(cfg)
    runner.run()

    mock_find.assert_called()
    mock_convert.assert_called_once()
    mock_transcribe.assert_called_once()
