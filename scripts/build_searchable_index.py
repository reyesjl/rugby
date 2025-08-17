import json
import os
from typing import List, Dict, Optional

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
    with open(srt_path, 'r', encoding='utf-8') as f:
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
            start_time, end_time = timestamp.split(' --> ')
            
            segments.append({
                'sequence': sequence_num,
                'start_time': start_time,
                'end_time': end_time,
                'text': text,
                'duration': calculate_duration(start_time, end_time)
            })
    
    return segments

def build_master_index(
    base_summaries_dir: str = './summaries',
    base_transcripts_dir: str = './transcripts',
    output_path: str = os.path.join('animus', 'data', 'master_video_index.json'),
    include_folders: Optional[list] = None,
    prefer_mp4: bool = True,
) -> List[Dict]:
    """Create searchable index of all video content.

    Parameters:
    - base_summaries_dir: Where summary JSON files live (by folder/basename.json)
    - base_transcripts_dir: Where SRTs live (by folder/basename.srt)
    - output_path: Where to write the resulting index JSON (defaults to animus/data)
    - include_folders: Optional list of folders to include (e.g., ['tuesday_session_08_06_2025', 'tuesday_session_08_06_2025_mp4'])
    - prefer_mp4: If True, will point video_file to MP4 under animus/data if present; else fall back to MPG
    """
    master_index: List[Dict] = []

    data_root = os.path.join('animus', 'data')

    for root, _, files in os.walk(base_summaries_dir):
        for file in files:
            if not file.endswith('.json'):
                continue

            # Load AI summary
            summary_path = os.path.join(root, file)
            try:
                with open(summary_path, 'r', encoding='utf-8') as f:
                    summary = json.load(f)
            except Exception:
                continue

            # Identify folder/basename from path
            folder = os.path.basename(root)
            basename = os.path.splitext(file)[0]

            # Folder filtering (supports either raw or *_mp4 forms)
            if include_folders:
                mp4_variant = folder if folder.endswith('_mp4') else f"{folder}_mp4"
                if folder not in include_folders and mp4_variant not in include_folders:
                    continue

            # Find corresponding SRT
            srt_path = os.path.join(base_transcripts_dir, folder, f'{basename}.srt')
            if not os.path.exists(srt_path):
                continue

            segments = parse_srt_with_timestamps(srt_path)

            # Decide video file path
            chosen_folder = folder
            video_rel_path = os.path.join(folder, f'{basename}.MPG')
            if prefer_mp4:
                mp4_folder = folder if folder.endswith('_mp4') else f'{folder}_mp4'
                mp4_rel = os.path.join(mp4_folder, f'{basename}.mp4')
                mp4_abs = os.path.join(data_root, mp4_rel)
                if os.path.exists(mp4_abs):
                    chosen_folder = mp4_folder
                    video_rel_path = mp4_rel

            # Build entry
            video_entry = {
                'video_file': video_rel_path,
                'folder': chosen_folder,
                'basename': basename,
                'summary': summary,
                'segments': segments,
                'total_duration': sum(s['duration'] for s in segments),
                'searchable_text': ' '.join([s['text'] for s in segments])
            }

            master_index.append(video_entry)

    # Save master index
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(master_index, f, indent=2)

    return master_index

if __name__ == "__main__":
    print("Building master video index (MP4-preferred) ...")
    output = os.path.join('animus', 'data', 'master_video_index.json')
    index = build_master_index(output_path=output, prefer_mp4=True)
    print(f"✅ Created index with {len(index)} videos")
    print(f"📁 Saved to: {output}")