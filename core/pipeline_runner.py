import logging
from typing import List
from core.pipeline_models import VideoProcessingConfig
from ingest.video_finder import find_video_files

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
                video_files = find_video_files(source.path, recursive=True)
                logger.info(f"({idx}/{total_sources}) Scanning: {source.path} ... found {len(video_files)} videos.")
                all_video_files.extend(video_files)
            except Exception as e:
                logger.error(f"({idx}/{total_sources}) Scanning: {source.path} ... [ERROR] {e}")

        logger.info(f"Total video files found: {len(all_video_files)}")
        logger.info("Pipeline ready. Proceeding with discovered video files.")

    def convert_videos(self, video_files: List[str]) -> List[str]:  
        """Convert videos using FFmpeg configuration."""  
        ffmpeg_config = self.config.conversion_config.ffmpeg  
        parallel_workers = self.config.conversion_config.parallel_workers  
        
        logger.info(f"Converting {len(video_files)} videos...")  
        logger.info(f"   Using codec: {ffmpeg_config.video_codec} (CRF: {ffmpeg_config.crf})")  
        logger.info(f"   Parallel workers: {parallel_workers}")  
        
        # TODO: Implement actual FFmpeg conversion  
        return video_files  # For now, return unchanged  
    
    def build_index(self, video_files: List[str]) -> None:  
        """Build searchable index using AI configuration."""  
        ai_config = self.config.indexing_config  
        
        logger.info(f"Building index with {ai_config.ai_provider} ({ai_config.model})...")  
        logger.info(f"   Batch size: {ai_config.batch_size}")  
        
        # TODO: Implement actual index building  
        pass
