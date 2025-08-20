#!/usr/bin/env python3
# Copyright (c) 2025 Biasware LLC
# Proprietary and Confidential. All Rights Reserved.
# This file is the sole property of Biasware LLC.
# Unauthorized use, distribution, or reverse engineering is prohibited.

"""
Update master video index to use MP4 files instead of MPG for Tuesday session videos
"""

import json
import os
import sys

def update_index_to_mp4(index_file: str = os.path.join('animus', 'data', 'master_video_index.json')):
    """Update the master video index to point to MP4 files for Tuesday session.

    By default, reads/writes animus/data/master_video_index.json.
    """
    
    if not os.path.exists(index_file):
        print(f"Error: {index_file} not found!")
        return False
    
    print("Loading master video index...")
    with open(index_file, 'r') as f:
        index_data = json.load(f)
    
    # Count updates
    updates_made = 0
    tuesday_entries = 0
    
    # Update Tuesday session entries to use MP4
    for entry in index_data:
        video_file = entry.get('video_file', '')
        
        # Check if this is a Tuesday session MPG file
        if 'tuesday_session_08_06_2025' in video_file and video_file.upper().endswith('.MPG'):
            tuesday_entries += 1
            
            # Check if corresponding MP4 exists
            mp4_path = video_file.replace('tuesday_session_08_06_2025/', 'tuesday_session_08_06_2025_mp4/')
            mp4_path = mp4_path.replace('.MPG', '.mp4')
            
            if os.path.exists(mp4_path):
                # Update the entry
                old_file = entry['video_file']
                entry['video_file'] = mp4_path
                
                # Update folder reference if it exists
                if entry.get('folder') == 'tuesday_session_08_06_2025':
                    entry['folder'] = 'tuesday_session_08_06_2025_mp4'
                
                # Update any nested folder references
                if 'summary' in entry and 'folder' in entry['summary']:
                    if entry['summary']['folder'] == 'tuesday_session_08_06_2025':
                        entry['summary']['folder'] = 'tuesday_session_08_06_2025_mp4'
                
                print(f"✓ Updated: {old_file} → {entry['video_file']}")
                updates_made += 1
            else:
                print(f"⚠ MP4 not found for: {video_file}")
    
    print(f"\nSummary:")
    print(f"  Tuesday session entries found: {tuesday_entries}")
    print(f"  Updates made: {updates_made}")
    
    if updates_made > 0:
        # Backup original
        backup_file = os.path.join(os.path.dirname(index_file), 'master_video_index_backup.json')
        print(f"\nCreating backup: {backup_file}")
        with open(backup_file, 'w') as f:
            json.dump(index_data, f, indent=2)
        
        # Save updated index
        print(f"Saving updated index: {index_file}")
        with open(index_file, 'w') as f:
            json.dump(index_data, f, indent=2)
        
        print("✅ Master video index updated successfully!")
        return True
    else:
        print("❌ No updates were made.")
        return False

if __name__ == '__main__':
    print("🎬 RugbyCodex - Updating Master Video Index to MP4")
    print("=" * 50)
    
    # Ensure we are in project directory
    project_dir = '/home/reyesjl/projects/rugby-modules'
    try:
        os.chdir(project_dir)
    except Exception:
        pass

    success = update_index_to_mp4(os.path.join('animus', 'data', 'master_video_index.json'))
    
    if success:
        print("\n🎉 Index update complete! Your app will now use MP4 files.")
    else:
        print("\n❌ Index update failed.")
    
    sys.exit(0 if success else 1)
