# Copyright (c) 2025 Biasware LLC
# Proprietary and Confidential. All Rights Reserved.
# This file is the sole property of Biasware LLC.
# Unauthorized use, distribution, or reverse engineering is prohibited.

from unittest.mock import patch

from core.pipeline_models import VideoProcessingConfig
from core.pipeline_runner import PipelineRunner


def make_config(tmp_dir: str | None = None) -> VideoProcessingConfig:
    base_path = tmp_dir or "/data/videos"
    cfg_dict = {
        "sources": [
            {
                "type": "linux_desktop",
                "path": base_path,
                "watch_patterns": ["mp4"],
            }
        ],
        "conversion": {"parallel_workers": 1},
        "indexing": {"ai_provider": "openai", "model": "gpt-4o-mini"},
        "transcription": {
            "model_size": "base",
            "language": "en",
            "output_dir": "./transcripts",
            "preserve_tree": True,
            "device": "cpu",
        },
    }
    return VideoProcessingConfig(cfg_dict)


@patch("core.pipeline_runner.subprocess.run")
@patch("core.pipeline_runner.convert_mp4_to_wav")
@patch("core.pipeline_runner.os.path.exists")
@patch("core.pipeline_runner.os.makedirs")
def test_transcribe_skips_existing_srt(
    mock_makedirs, mock_exists, mock_convert, mock_run
):
    cfg = make_config()
    runner = PipelineRunner(cfg)
    video_file = "/data/videos/sample.mp4"
    srt_file = "./transcripts/sample.srt"

    def exists_side_effect(path: str):  # only pretend srt exists
        return path == srt_file

    mock_exists.side_effect = exists_side_effect

    out = runner.transcribe_to_srt([video_file])
    assert out == [srt_file]
    # Ensure we skipped expensive work
    mock_convert.assert_not_called()
    mock_run.assert_not_called()


@patch("core.pipeline_runner.PipelineRunner.convert_videos")
@patch("core.pipeline_runner.find_video_files")
@patch("core.pipeline_runner.video_file_indexed")
def test_run_aborts_when_all_indexed(mock_indexed, mock_find, mock_convert):
    cfg = make_config()
    runner = PipelineRunner(cfg)
    video_file = "/data/videos/sample.mp4"
    mock_find.return_value = [video_file]
    mock_indexed.return_value = True  # treat as already indexed

    runner.run()
    # Should not attempt conversion
    mock_convert.assert_not_called()
