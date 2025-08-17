#!/usr/bin/env python3
"""
Create an MP4-only master video index
This removes all MPG references and keeps only MP4 files
"""

import json
import os

def create_mp4_only_index(index_path: str = os.path.join('animus', 'data', 'master_video_index.json')):
    """Filter master video index to only include MP4 files.

    Reads and writes the index in animus/data by default.
    """

    with open(index_path, 'r') as f:
        full_index = json.load(f)
    
    # Filter to only MP4 files
    mp4_only_index = []
    mpg_count = 0
    mp4_count = 0
    
    for video in full_index:
        video_file = video.get('video_file', '')
        if video_file.lower().endswith('.mp4'):
            mp4_only_index.append(video)
            mp4_count += 1
        elif video_file.lower().endswith('.mpg'):
            mpg_count += 1
    
    # Backup the original
    backup_path = os.path.join(os.path.dirname(index_path), 'master_video_index_full_backup.json')
    if not os.path.exists(backup_path):
        with open(backup_path, 'w') as f:
            json.dump(full_index, f, indent=2)
        print(f"✅ Created backup: {backup_path}")
    
    # Write the MP4-only index
    with open(index_path, 'w') as f:
        json.dump(mp4_only_index, f, indent=2)
    
    print(f"🎬 Master video index updated:")
    print(f"   - Removed {mpg_count} MPG entries")
    print(f"   - Kept {mp4_count} MP4 entries")
    print(f"   - Your application now only sees MP4 files!")

if __name__ == "__main__":
    create_mp4_only_index()
