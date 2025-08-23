# Copyright (c) 2025 Biasware LLC
# Proprietary and Confidential. All Rights Reserved.
# This file is the sole property of Biasware LLC.
# Unauthorized use, distribution, or reverse engineering is prohibited.

"""Focused tests for PipelineRunner.transcribe_to_srt pathing and robustness."""

from unittest.mock import MagicMock, patch

from core.pipeline_models import VideoProcessingConfig
from core.pipeline_runner import PipelineRunner


def minimal_config(tmp_dir: str, preserve_tree: bool = True):
    return {
        "sources": [
            {
                "type": "linux_desktop",
                "path": "/videos",  # not used directly in test
                "watch_patterns": ["mp4"],
            }
        ],
        "conversion": {"ffmpeg": {}, "parallel_workers": 1},
        "indexing": {"ai_provider": "openai", "model": "gpt-4o-mini", "batch_size": 1},
        "transcription": {
            "model_size": "tiny",
            "language": "en",
            "device": "cpu",
            "output_dir": tmp_dir,
            "preserve_tree": preserve_tree,
        },
    }


@patch("core.pipeline_runner.subprocess.run")
@patch("core.pipeline_runner.convert_mp4_to_wav")
def test_transcribe_to_srt_uses_output_dir_for_audio(mock_conv, mock_run, tmp_path):
    # Arrange
    cfg = VideoProcessingConfig(minimal_config(str(tmp_path), preserve_tree=False))
    runner = PipelineRunner(cfg)

    video_file = "/any/where/video.mp4"

    # Make convert_mp4_to_wav produce a file in the srt_out_dir
    def _mk_audio_file(vf, output_dir=None):
        assert output_dir is not None
        p = tmp_path / "video.wav"
        p.write_text("wav")
        return str(p)

    mock_conv.side_effect = _mk_audio_file
    mock_run.return_value = MagicMock()

    # Act
    runner.transcribe_to_srt([video_file])

    # Assert whisper was invoked once
    assert mock_run.call_count == 1
    args, kwargs = mock_run.call_args
    cmd = args[0]
    assert cmd[0] == "whisper"
    assert "--output_dir" in cmd
    # ensure convert_mp4_to_wav was given output_dir
    assert mock_conv.call_count == 1
    _, k = mock_conv.call_args
    # Normalize potential trailing slash differences
    assert "output_dir" in k and str(k["output_dir"]).rstrip("/") == str(
        tmp_path
    ).rstrip("/")


@patch("core.pipeline_runner.subprocess.run")
@patch("core.pipeline_runner.convert_mp4_to_wav")
def test_transcribe_handles_missing_binaries_and_cleans_temp(
    mock_conv, mock_run, tmp_path
):
    cfg = VideoProcessingConfig(minimal_config(str(tmp_path), preserve_tree=False))
    runner = PipelineRunner(cfg)

    # Simulate audio file creation
    audio_p = tmp_path / "temp.wav"
    audio_p.write_text("x")
    mock_conv.return_value = str(audio_p)

    # Simulate whisper missing
    mock_run.side_effect = FileNotFoundError("whisper not found")

    runner.transcribe_to_srt(["/x/video.mp4"])  # should not raise

    # Ensure cleanup attempted (file removed best-effort)
    assert not audio_p.exists()


def test_pipeline_runner_transcribe(tmp_path) -> None:
    """Test the transcribe functionality of the PipelineRunner."""
    cfg = VideoProcessingConfig(minimal_config(str(tmp_path)))
    runner = PipelineRunner(cfg)

    video_file = "/any/where/video.mp4"

    # Act
    runner.transcribe_to_srt([video_file])

    # Assert that whisper was invoked with the correct parameters
    # This part of the test might need to be adjusted based on the actual implementation
    # and the expected behavior of the transcribe_to_srt method.
