import logging
from typing import List
from core.pipeline_models import VideoProcessingConfig
from ingest.video_finder import find_video_files
import subprocess

# Use module-level logger; logging configured in CLI
logger = logging.getLogger(__name__)

class PipelineRunner:
    def __init__(self, config: VideoProcessingConfig):
        self.config = config

    def run(self):
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
                video_files = find_video_files(source.path, source.watch_patterns, recursive=True)
                logger.info(f"({idx}/{total_sources}) Scanning: {source.path} ... found {len(video_files)} videos.")
                all_video_files.extend(video_files)
            except Exception as e:
                logger.error(f"({idx}/{total_sources}) Scanning: {source.path} ... [ERROR] {e}")

        logger.info(f"Total video files found: {len(all_video_files)}")
        logger.info("Pipeline ready. Proceeding with discovered video files.")

        logger.info("Converting Video Files...")
        converted_files = self.convert_videos(all_video_files)

    def convert_videos(self, video_files: List[str]) -> List[str]:
        """Convert videos using FFmpeg configuration."""
        ffmpeg_config = self.config.conversion_config.ffmpeg
        parallel_workers = self.config.conversion_config.parallel_workers

        logger.info(f"Converting {len(video_files)} videos...")
        logger.info(f"   Using codec: {ffmpeg_config.video_codec} (CRF: {ffmpeg_config.crf}, Preset: {ffmpeg_config.preset})")
        logger.info(f"   Audio codec: {ffmpeg_config.audio_codec} ({ffmpeg_config.audio_bitrate})")
        #TODO: Parallel processing?
        logger.info(f"   Parallel workers: {parallel_workers}")

        files_to_index = []
        for video_file in video_files:
            # pre_extension = video_file.split('.')[:-1]
            extension = video_file.split('.')[-1].lower()
            if extension == "mp4":
                # TODO: Do we really want to handle mp4 files like this?
                files_to_index.append(video_file)
                logger.debug(f"Not reformating mp4 video: {video_file}")
                continue

            logger.debug(f"Processing video: {video_file}")

            # Build output filename (e.g., add '_converted' before extension)
            # TODO: Need to remember previous file conversions. Some sort of hashing
            # or metadata to avoid reprocessing.
            output_file = (
                video_file.rsplit('.', 1)[0] + '_converted.mp4'
            )

            ffmpeg_cmd = [
                "ffmpeg",
                "-y",  # Overwrite output files without asking
                "-i", video_file,
                "-c:v", ffmpeg_config.video_codec,
                "-crf", str(ffmpeg_config.crf),
                "-preset", ffmpeg_config.preset,
                "-c:a", ffmpeg_config.audio_codec,
                "-b:a", ffmpeg_config.audio_bitrate,
                output_file,
            ]

            logger.debug(f"Running FFmpeg command: {' '.join(ffmpeg_cmd)}")
            try:
                subprocess.run(ffmpeg_cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                logger.debug(f"Converted video: {output_file}")
                files_to_index.append(output_file)
            except subprocess.CalledProcessError as e:
                logger.error(f"FFmpeg failed for {video_file}: {e.stderr.decode()}")

        return files_to_index

    def build_index(self, video_files: List[str]) -> None:  
        """Build searchable index using AI configuration."""  
        ai_config = self.config.indexing_config  
        
        logger.info(f"Building index with {ai_config.ai_provider} ({ai_config.model})...")  
        logger.info(f"   Batch size: {ai_config.batch_size}")  
        
        # TODO: Implement actual index building  
        pass
