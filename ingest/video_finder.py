"""Video ingestion utilities for the rugby pipeline."""

import os
from typing import List


SUPPORTED_VIDEO_FORMATS = ['.mpg', '.mp4', '.avi', '.mov', '.mkv']


def find_video_files(directory: str, recursive: bool = True) -> List[str]:
    """Find all video files in a directory.
    
    Args:
        directory: Directory to search
        recursive: Whether to search subdirectories
        
    Returns:
        List of video file paths
    """
    video_files = []
    
    if recursive:
        for root, dirs, files in os.walk(directory):
            for file in files:
                if any(file.lower().endswith(fmt) for fmt in SUPPORTED_VIDEO_FORMATS):
                    video_files.append(os.path.join(root, file))
    else:
        for file in os.listdir(directory):
            file_path = os.path.join(directory, file)
            if os.path.isfile(file_path) and any(file.lower().endswith(fmt) for fmt in SUPPORTED_VIDEO_FORMATS):
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