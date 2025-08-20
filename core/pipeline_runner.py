# Copyright (c) 2025 Biasware LLC
# Proprietary and Confidential. All Rights Reserved.
# This file is the sole property of Biasware LLC.
# Unauthorized use, distribution, or reverse engineering is prohibited.

import logging
import os  # NEW
import subprocess
from typing import Optional

from core.pipeline_models import VideoProcessingConfig
from ingest.video_finder import find_video_files

# Use module-level logger; logging configured in CLI
logger = logging.getLogger(__name__)


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
        converted_files = self.convert_videos(all_video_files)
        logger.info("Transcribing Video Files...")
        self.transcribe_to_srt(converted_files)

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

        files_to_index = []
        for video_file in video_files:
            # pre_extension = video_file.split('.')[:-1]
            extension = video_file.split(".")[-1].lower()
            if extension == "mp4":
                # TODO: Do we really want to handle mp4 files like this?
                files_to_index.append(video_file)
                logger.debug(f"Not reformating mp4 video: {video_file}")
                continue

            logger.debug(f"Processing video: {video_file}")

            # Build output filename (e.g., add '_converted' before extension)
            # TODO: Need to remember previous file conversions. Some sort of hashing
            # or metadata to avoid reprocessing.
            output_file = video_file.rsplit(".", 1)[0] + "_converted.mp4"

            ffmpeg_cmd = [
                "ffmpeg",
                "-y",  # Overwrite output files without asking
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

            whisper_cmd = [
                "whisper",
                "--model",
                transcription_config.model_size,
                "--language",
                transcription_config.language,
                "--output_format",
                "srt",
                "--output_dir",
                srt_out_dir,
                video_file,
            ]

            logger.debug(f"Running Whisper command: {' '.join(whisper_cmd)}")
            try:
                subprocess.run(
                    whisper_cmd,
                    check=True,
                    capture_output=True,
                )
                logger.debug(f"Generated SRT file: {srt_file}")
            except subprocess.CalledProcessError as e:
                logger.error(f"Whisper failed for {video_file}: {e.stderr.decode()}")

    def build_index(self, video_files: list[str]) -> None:
        """Build searchable index using AI configuration."""
        ai_config = self.config.indexing_config

        logger.info(
            f"Building index with {ai_config.ai_provider} ({ai_config.model})..."
        )
        logger.info(f"   Batch size: {ai_config.batch_size}")

        # TODO: Implement actual index building
        pass
