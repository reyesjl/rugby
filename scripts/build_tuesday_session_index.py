#!/usr/bin/env python3
# Copyright (c) 2025 Biasware LLC
# Proprietary and Confidential. All Rights Reserved.
# This file is the sole property of Biasware LLC.
# Unauthorized use, distribution, or reverse engineering is prohibited.

"""
Build master video index specifically for Tuesday session MP4 videos
This creates a searchable index for the demo focused on tuesday_session_08_06_2025_mp4
"""

import json
import os
import re
from typing import List, Dict

def calculate_duration(start_time: str, end_time: str) -> float:
    """Calculate duration in seconds from SRT timestamps"""
    def parse_timestamp(ts):
        # Handle format "00:01:23,456"
        time_part, ms_part = ts.split(',')
        h, m, s = map(int, time_part.split(':'))
        ms = int(ms_part)
        return h * 3600 + m * 60 + s + ms / 1000.0
    
    start_seconds = parse_timestamp(start_time)
    end_seconds = parse_timestamp(end_time)
    return end_seconds - start_seconds

def parse_srt_with_timestamps(srt_path: str) -> List[Dict]:
    """Extract timestamped segments from SRT files"""
    try:
        with open(srt_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except UnicodeDecodeError:
        # Try with latin-1 encoding if utf-8 fails
        with open(srt_path, 'r', encoding='latin-1') as f:
            content = f.read()
    
    segments = []
    blocks = content.strip().split('\n\n')
    
    for block in blocks:
        lines = block.strip().split('\n')
        if len(lines) >= 3:
            sequence_num = lines[0]
            timestamp = lines[1]
            text = ' '.join(lines[2:])
            
            # Parse timestamp "00:01:23,456 --> 00:01:27,890"
            if ' --> ' in timestamp:
                start_time, end_time = timestamp.split(' --> ')
                
                segments.append({
                    'sequence': sequence_num,
                    'start_time': start_time,
                    'end_time': end_time,
                    'text': text,
                    'duration': calculate_duration(start_time, end_time)
                })
    
    return segments

def build_tuesday_session_index():
    """Create searchable index specifically for Tuesday session MP4 videos"""
    master_index = []
    
    # Target folder for Tuesday session
    target_folder = 'tuesday_session_08_06_2025'
    summaries_folder = f'./summaries/{target_folder}'
    transcripts_folder = f'./transcripts/{target_folder}'
    videos_folder = './tuesday_session_08_06_2025_mp4'
    
    print(f"🎬 Building index for Tuesday session videos...")
    print(f"   - Summaries: {summaries_folder}")
    print(f"   - Transcripts: {transcripts_folder}")
    print(f"   - Videos: {videos_folder}")
    
    # Check if directories exist
    if not os.path.exists(summaries_folder):
        print(f"❌ Summaries folder not found: {summaries_folder}")
        return []
    
    if not os.path.exists(transcripts_folder):
        print(f"❌ Transcripts folder not found: {transcripts_folder}")
        return []
    
    if not os.path.exists(videos_folder):
        print(f"❌ Videos folder not found: {videos_folder}")
        return []
    
    # Process each summary file
    summary_files = [f for f in os.listdir(summaries_folder) if f.endswith('.json')]
    
    for summary_file in sorted(summary_files):
        basename = os.path.splitext(summary_file)[0]
        
        # Paths for all related files
        summary_path = os.path.join(summaries_folder, summary_file)
        srt_path = os.path.join(transcripts_folder, f'{basename}.srt')
        video_path = os.path.join(videos_folder, f'{basename}.mp4')
        
        print(f"   Processing: {basename}")
        
        # Check if all required files exist
        if not os.path.exists(summary_path):
            print(f"     ⚠️  Summary not found: {summary_path}")
            continue
        
        if not os.path.exists(srt_path):
            print(f"     ⚠️  Transcript not found: {srt_path}")
            continue
        
        if not os.path.exists(video_path):
            print(f"     ⚠️  Video not found: {video_path}")
            continue
        
        try:
            # Load AI summary
            with open(summary_path, 'r', encoding='utf-8') as f:
                summary = json.load(f)
            
            # Parse SRT transcript
            segments = parse_srt_with_timestamps(srt_path)
            
            # Create video entry
            video_entry = {
                'video_file': f'tuesday_session_08_06_2025_mp4/{basename}.mp4',
                'folder': 'tuesday_session_08_06_2025_mp4',
                'basename': basename,
                'summary': summary,
                'segments': segments,
                'total_duration': sum(s['duration'] for s in segments) if segments else 0,
                'searchable_text': ' '.join([s['text'] for s in segments]) if segments else ''
            }
            
            master_index.append(video_entry)
            print(f"     ✅ Added to index ({len(segments)} segments)")
            
        except Exception as e:
            print(f"     ❌ Error processing {basename}: {e}")
            continue
    
    # Save master index
    output_path = './master_video_index.json'
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(master_index, f, indent=2, ensure_ascii=False)
    
    print(f"\n🎯 Tuesday session index created:")
    print(f"   - {len(master_index)} videos indexed")
    print(f"   - Total segments: {sum(len(v['segments']) for v in master_index)}")
    print(f"   - Saved to: {output_path}")
    
    return master_index

if __name__ == "__main__":
    index = build_tuesday_session_index()
    
    if index:
        print(f"\n📋 Index Summary:")
        for video in index[:5]:  # Show first 5 as sample
            print(f"   - {video['basename']}: {len(video['segments'])} segments, {video['total_duration']:.1f}s")
        
        if len(index) > 5:
            print(f"   ... and {len(index) - 5} more videos")
    else:
        print("❌ No videos were indexed")
