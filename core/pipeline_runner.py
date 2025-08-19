from typing import List, Optional
import os
from core.pipeline_models import VideoProcessingConfig, VideoSource
from ingest.video_finder import find_video_files

class PipelineRunner:
    def __init__(self, config: VideoProcessingConfig):
        self.config = config

    def run(self):
        print("[INFO] Initializing pipeline...")
        print("[INFO] Connecting to sources...")
        print("[INFO] Booting up pipeline...")
        print("[INFO] Using configuration:")
        print(self.config)

        print("[INFO] Scanning video sources...")
        all_video_files = []
        total_sources = len(self.config.video_sources.sources)
        for idx, source in enumerate(self.config.video_sources.sources, 1):
            print(f"[INFO] ({idx}/{total_sources}) Scanning: {source.path} ...", end="")
            try:
                video_files = find_video_files(source.path, recursive=True)
                print(f" found {len(video_files)} videos.")
                all_video_files.extend(video_files)
            except Exception as e:
                print(f" [ERROR] {e}")

        print(f"[OK] Total video files found: {len(all_video_files)}")
        print("[READY] Pipeline ready. Proceeding with discovered video files.")
