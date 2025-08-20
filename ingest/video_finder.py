# Copyright (c) 2025 Biasware LLC
# Proprietary and Confidential. All Rights Reserved.
# This file is the sole property of Biasware LLC.
# Unauthorized use, distribution, or reverse engineering is prohibited.

"""Video ingestion utilities for the rugby pipeline."""

import logging
import os
from typing import List


SUPPORTED_VIDEO_FORMATS = ['mpg', 'mp4', 'avi', 'mov', 'mkv']
logger = logging.getLogger(__name__)


def find_video_files(directory: str, watch_patterns: List[str], recursive: bool = True) -> List[str]:
    """Find all video files in a directory.
    
    Args:
        directory: Directory to search
        watch_patterns: List of file extensions to look for (e.g., ['mpg', 'mp4'])
        recursive: Whether to search subdirectories
        
    Returns:
        List of video file paths
    """
    video_files = []
    extensions = [pattern for pattern in watch_patterns if pattern in SUPPORTED_VIDEO_FORMATS]
    
    if recursive:
        for root, dirs, files in os.walk(directory):
            for file in files:
                if any(file.lower().endswith(fmt) for fmt in extensions):
                    video_files.append(os.path.join(root, file))
                else:
                    logger.debug(f"Skipping unsupported video file: {file}")
    else:
        for file in os.listdir(directory):
            file_path = os.path.join(directory, file)
            if os.path.isfile(file_path) and any(file.lower().endswith(fmt) for fmt in extensions):
                video_files.append(file_path)
    
    return sorted(video_files)


def validate_video_file(file_path: str) -> bool:
    """Validate that a file exists and has a supported video format.
    
    Args:
        file_path: Path to video file
        
    Returns:
        True if file is valid, False otherwise
    """
    if not os.path.exists(file_path):
        return False
        
    return any(file_path.lower().endswith(fmt) for fmt in SUPPORTED_VIDEO_FORMATS)