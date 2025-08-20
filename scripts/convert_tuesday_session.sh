#!/bin/bash

# Convert Tuesday session videos from MPG to MP4 for web playback
# Preserves audio and optimizes for browser compatibility

SOURCE_DIR="/home/reyesjl/projects/rugby-modules/tuesday_session_08_06_2025"
OUTPUT_DIR="/home/reyesjl/projects/rugby-modules/tuesday_session_08_06_2025_mp4"

# Create output directory if it doesn't exist
mkdir -p "$OUTPUT_DIR"

echo "Converting Tuesday session videos from MPG to MP4..."
echo "Source: $SOURCE_DIR"
echo "Output: $OUTPUT_DIR"
echo "========================================="

# Counter for progress tracking
count=0
total=33

# Convert each MPG file to MP4
for mpg_file in "$SOURCE_DIR"/*.MPG; do
    if [ -f "$mpg_file" ]; then
        # Get filename without extension
        filename=$(basename "$mpg_file" .MPG)
        output_file="$OUTPUT_DIR/${filename}.mp4"

        # Skip if already exists
        if [ -f "$output_file" ]; then
            echo "Skipping $filename (already exists)"
            continue
        fi

        count=$((count + 1))
        echo "[$count/$total] Converting $filename..."

        # Convert with ffmpeg - preserving audio and optimizing for web
        ffmpeg -i "$mpg_file" \
            -c:v libx264 \
            -preset medium \
            -crf 23 \
            -c:a aac \
            -b:a 128k \
            -movflags +faststart \
            -y \
            "$output_file"

        if [ $? -eq 0 ]; then
            # Get file sizes for comparison
            original_size=$(du -h "$mpg_file" | cut -f1)
            new_size=$(du -h "$output_file" | cut -f1)
            echo "  ✓ Success: $original_size → $new_size"
        else
            echo "  ✗ Failed to convert $filename"
        fi

        echo ""
    fi
done

echo "========================================="
echo "Conversion complete!"
echo "Converted videos are in: $OUTPUT_DIR"

# Show summary
converted_count=$(ls -1 "$OUTPUT_DIR"/*.mp4 2>/dev/null | wc -l)
echo "Total MP4 files: $converted_count"

# Calculate total sizes
if [ -d "$OUTPUT_DIR" ] && [ "$(ls -A "$OUTPUT_DIR")" ]; then
    original_total=$(du -sh "$SOURCE_DIR" | cut -f1)
    converted_total=$(du -sh "$OUTPUT_DIR" | cut -f1)
    echo "Original folder size: $original_total"
    echo "Converted folder size: $converted_total"
fi
