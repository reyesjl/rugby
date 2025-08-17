#!/bin/bash

ROOT_DIR="$(pwd)"
INPUT_BASE="$ROOT_DIR"
OUTPUT_BASE="$ROOT_DIR/transcripts"

mkdir -p "$OUTPUT_BASE"

# Ignore venv and transcripts
EXCLUDE_DIRS="venv transcripts"

# Recursively find video files
find "$INPUT_BASE" -type f \( -iname '*.mpg' -o -iname '*.mp4' \) | while read -r filepath; do
    # Skip excluded folders
    for exclude in $EXCLUDE_DIRS; do
        if [[ "$filepath" == *"/$exclude/"* ]]; then
            continue 2
        fi
    done

    rel_path="${filepath#$INPUT_BASE/}"
    dir_path=$(dirname "$rel_path")
    filename=$(basename "$filepath")
    basename_noext="${filename%.*}"

    output_dir="$OUTPUT_BASE/$dir_path"
    output_file="$output_dir/${basename_noext}.srt"

    if [ -f "$output_file" ]; then
        echo "Skipping: $rel_path"
        continue
    fi

    mkdir -p "$output_dir"
    echo "Transcribing: $rel_path"

    if whisper "$filepath" --language English --model large --output_format srt --output_dir "$output_dir"; then
        echo "Saved: $output_file"
    else
        echo "Failed on: $filepath"
    fi
done

echo "All videos processed."
