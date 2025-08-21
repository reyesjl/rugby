#!/bin/bash

# Video conversion script - Convert MPG files to MP4 for web compatibility
# This script converts all MPG files in specified directories to MP4 format

echo "=== Rugby Video Converter ==="
echo "Converting MPG files to MP4 for web playback..."

# Function to convert a single directory
convert_directory() {
    local source_dir="$1"
    local target_dir="${source_dir}_mp4"

    if [ ! -d "$source_dir" ]; then
        echo "Directory $source_dir not found, skipping..."
        return
    fi

    echo ""
    echo "Converting directory: $source_dir -> $target_dir"

    # Create target directory
    mkdir -p "$target_dir"

    # Count total files
    total_files=$(find "$source_dir" -name "*.MPG" -o -name "*.mpg" | wc -l)
    echo "Found $total_files MPG files to convert"

    if [ $total_files -eq 0 ]; then
        echo "No MPG files found in $source_dir"
        return
    fi

    # Convert each MPG file
    current=0
    for mpg_file in "$source_dir"/*.MPG "$source_dir"/*.mpg; do
        if [ -f "$mpg_file" ]; then
            current=$((current + 1))
            filename=$(basename "$mpg_file")
            filename_no_ext="${filename%.*}"
            mp4_file="$target_dir/${filename_no_ext}.mp4"

            echo "[$current/$total_files] Converting: $filename"

            # Skip if already converted
            if [ -f "$mp4_file" ]; then
                echo "  -> Already exists, skipping"
                continue
            fi

            # Convert with ffmpeg
            # Using web-optimized settings for browser compatibility
            ffmpeg -i "$mpg_file" \
                -c:v libx264 \
                -crf 23 \
                -preset fast \
                -c:a aac \
                -b:a 128k \
                -movflags +faststart \
                -y \
                "$mp4_file" \
                2>/dev/null

            if [ $? -eq 0 ]; then
                echo "  -> Success: ${filename_no_ext}.mp4"
            else
                echo "  -> ERROR: Failed to convert $filename"
            fi
        fi
    done
}

# Convert all video directories
echo "Starting conversion process..."

convert_directory "pre_sort_broll_01"
convert_directory "pre_sort_broll_02"
convert_directory "tuesday_session_08_06_2025"

echo ""
echo "=== Conversion Complete ==="
echo "MP4 files have been created in *_mp4 directories"
echo "You can now update the system to use MP4 files for web playback"
