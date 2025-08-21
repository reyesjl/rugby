# Copyright (c) 2025 Biasware LLC
# Proprietary and Confidential. All Rights Reserved.
# This file is the sole property of Biasware LLC.
# Unauthorized use, distribution, or reverse engineering is prohibited.

import logging
import os
import subprocess
import time
from typing import Any, Callable, Optional, TypeVar

from core.pipeline_models import VideoProcessingConfig
from ingest.video_finder import find_video_files

# Use module-level logger; logging configured in CLI
logger = logging.getLogger(__name__)

T = TypeVar("T")


def time_function(name: str, func: Callable[..., T], *args: Any, **kwargs: Any) -> T:
    """
    Times the execution of a function in milliseconds.

    Args:
        func (Callable[..., T]): The function to time.
        *args: Positional arguments for the function.
        **kwargs: Keyword arguments for the function.

    Returns:
        T: The return value of the function.
    """
    start = time.time()
    result = func(*args, **kwargs)
    end = time.time()
    elapsed_ms = (end - start) * 1000
    logger.debug(f"Stage: {name} took {elapsed_ms:.2f} ms")
    return result


def convert_mp4_to_wav(video_file: str, output_dir: Optional[str] = None) -> str:
    """Convert an MP4 video file to a WAV audio file using FFmpeg.
    Args:
        video_file (str): Path to the input MP4 video file.
        output_dir (Optional[str]): Directory where the WAV file should be written.
            If not provided, the WAV will be created alongside the video file.
    Returns:
        str: Path to the output WAV audio file.
    """
    if not video_file.lower().endswith(".mp4"):
        raise ValueError("Input file must be an MP4 video file.")

    base_name = os.path.splitext(os.path.basename(video_file))[0] + ".wav"
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        audio_file = os.path.join(output_dir, base_name)
    else:
        audio_file = video_file[:-3] + "wav"

    logger.debug(f"Extracting audio to: {audio_file}")

    # Use check=True to surface ffmpeg failures; caller handles exceptions.
    subprocess.run(
        [
            "ffmpeg",
            "-y",  # Overwrite output files without asking
            "-i",
            video_file,
            "-ar",
            "16000",
            "-ac",
            "1",
            audio_file,
        ],
        check=True,
        capture_output=True,
    )
    return audio_file


class PipelineRunner:
    def __init__(self, config: VideoProcessingConfig) -> None:
        self.config = config

    def run(self) -> None:
        logger.info("Initializing pipeline...")
        logger.info("Connecting to sources...")
        logger.info("Booting up pipeline...")
        logger.info("Using configuration:")
        logger.info(self.config)

        logger.info("Scanning video sources...")
        all_video_files = []
        total_sources = len(self.config.video_sources.sources)
        for idx, source in enumerate(self.config.video_sources.sources, 1):
            try:
                video_files = find_video_files(
                    source.path, source.watch_patterns, recursive=True
                )
                logger.info(
                    f"({idx}/{total_sources}) Scanning: {source.path} ... found {len(video_files)} videos."
                )
                all_video_files.extend(video_files)
            except Exception as e:
                logger.error(
                    f"({idx}/{total_sources}) Scanning: {source.path} ... [ERROR] {e}"
                )

        logger.info(f"Total video files found: {len(all_video_files)}")
        logger.info("Pipeline ready. Proceeding with discovered video files.")

        logger.info("Converting Video Files...")
        converted_files = time_function(
            "Video Conversion", self.convert_videos, all_video_files
        )
        logger.info("Transcribing Video Files...")
        time_function("Video Transcription", self.transcribe_to_srt, converted_files)

    def convert_videos(self, video_files: list[str]) -> list[str]:
        """Convert videos using FFmpeg configuration."""
        ffmpeg_config = self.config.conversion_config.ffmpeg
        parallel_workers = self.config.conversion_config.parallel_workers

        logger.info(f"Converting {len(video_files)} videos...")
        logger.info(
            f"   Using codec: {ffmpeg_config.video_codec} (CRF: {ffmpeg_config.crf}, Preset: {ffmpeg_config.preset})"
        )
        logger.info(
            f"   Audio codec: {ffmpeg_config.audio_codec} ({ffmpeg_config.audio_bitrate})"
        )
        # TODO: Parallel processing?
        logger.info(f"   Parallel workers: {parallel_workers}")

        files_to_index: list[str] = []
        for video_file in video_files:
            extension = video_file.split(".")[-1].lower()
            if extension == "mp4":
                # Passthrough mp4 files
                files_to_index.append(video_file)
                logger.debug(f"Not reformating mp4 video: {video_file}")
                continue

            logger.debug(f"Processing video: {video_file}")

            # Build output filename (e.g., add '_converted' before extension)
            output_file = video_file.rsplit(".", 1)[0] + "_converted.mp4"

            ffmpeg_cmd = [
                "ffmpeg",
                "-y",
                "-i",
                video_file,
                "-c:v",
                ffmpeg_config.video_codec,
                "-crf",
                str(ffmpeg_config.crf),
                "-preset",
                ffmpeg_config.preset,
                "-c:a",
                ffmpeg_config.audio_codec,
                "-b:a",
                ffmpeg_config.audio_bitrate,
                output_file,
            ]

            logger.debug(f"Running FFmpeg command: {' '.join(ffmpeg_cmd)}")
            try:
                subprocess.run(
                    ffmpeg_cmd,
                    check=True,
                    capture_output=True,
                )
                logger.debug(f"Converted video: {output_file}")
                files_to_index.append(output_file)
            except subprocess.CalledProcessError as e:
                logger.error(f"FFmpeg failed for {video_file}: {e.stderr.decode()}")

        return files_to_index

    def transcribe_to_srt(self, video_files: list[str]) -> None:
        """Transcribe video files to SRT format using Whisper model."""
        transcription_config = self.config.transcription_config
        logger.info(
            f"Transcribing videos to SRT using Whisper model (Size: {transcription_config.model_size}, Language: {transcription_config.language})..."
        )

        def find_source_base(path: str) -> Optional[str]:
            for src in self.config.video_sources.sources:
                if path.startswith(src.path):
                    return src.path
            return None

        for video_file in video_files:
            # Determine output path
            if transcription_config.output_dir:
                base = (
                    find_source_base(video_file)
                    if transcription_config.preserve_tree
                    else None
                )
                if base:
                    rel = os.path.relpath(video_file, base)
                else:
                    rel = os.path.basename(video_file)
                rel_no_ext = os.path.splitext(rel)[0]
                srt_out_dir = os.path.join(
                    transcription_config.output_dir, os.path.dirname(rel_no_ext)
                )
                srt_file = os.path.join(
                    transcription_config.output_dir, rel_no_ext + ".srt"
                )
            else:
                # Fallback: next to the video
                srt_out_dir = os.path.dirname(video_file)
                srt_file = video_file.rsplit(".", 1)[0] + ".srt"

            os.makedirs(srt_out_dir, exist_ok=True)

            audio_file: Optional[str] = None
            try:
                audio_file = convert_mp4_to_wav(video_file, output_dir=srt_out_dir)
                logger.debug(f"Extracting audio to: {audio_file}")

                whisper_cmd = [
                    "whisper",
                    "--model",
                    transcription_config.model_size,
                    "--device",
                    transcription_config.device,
                    "--language",
                    transcription_config.language,
                    "--output_format",
                    "srt",
                    "--output_dir",
                    srt_out_dir,
                    audio_file,
                ]

                logger.debug(f"Running Whisper command: {' '.join(whisper_cmd)}")
                subprocess.run(
                    whisper_cmd,
                    check=True,
                    capture_output=True,
                )
                logger.debug(f"Generated SRT file: {srt_file}")
            except FileNotFoundError as e:
                logger.error(
                    f"Required binary not found while transcribing {video_file}: {e}"
                )
            except subprocess.CalledProcessError as e:
                # Log stderr if available
                stderr_msg = e.stderr.decode(errors="ignore") if e.stderr else str(e)
                logger.error(f"Transcription failed for {video_file}: {stderr_msg}")
            finally:
                if audio_file and os.path.exists(audio_file):
                    try:
                        os.remove(audio_file)
                    except OSError:
                        # Best-effort cleanup
                        pass

    def build_index(self, video_files: list[str]) -> None:
        """Build searchable index using AI configuration."""
        ai_config = self.config.indexing_config

        logger.info(
            f"Building index with {ai_config.ai_provider} ({ai_config.model})..."
        )
        logger.info(f"   Batch size: {ai_config.batch_size}")

        # TODO: Implement actual index building
        pass


def run_pipeline(config: Any, inputs: Any) -> Any:
    """Run the video processing pipeline.
    Args:
        config (Any): The configuration for the pipeline.
        inputs (Any): The input data for the pipeline.
    Returns:
        Any: The result of the pipeline execution.
    """
    # TODO: Implement the pipeline execution logic
    pass
