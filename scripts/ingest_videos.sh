#!/bin/bash

# vmv - Video Move & Verify
# Copies *.MPG from a selected Desktop folder to a new/existing subfolder in rugby-modules
# Skips duplicates, creates project folder if missing

WINDOWS_USER="joser"
DESKTOP="/mnt/c/Users/$WINDOWS_USER/Desktop"
DEST_BASE="$HOME/projects/rugby-modules"

echo "Available folders on your Windows Desktop:"
echo

select folder in $(ls -d $DESKTOP/*/ 2>/dev/null | xargs -n 1 basename); do
    if [ -z "$folder" ]; then
        echo "Invalid selection."
        exit 1
    fi

    SRC_FOLDER="$DESKTOP/$folder"
    read -p "Enter a new or existing destination folder name in rugby-modules: " destname

    DEST_FOLDER="$DEST_BASE/$destname"
    mkdir -p "$DEST_FOLDER"

    echo
    echo "Copying .MPG files from $SRC_FOLDER to $DEST_FOLDER..."
    echo

    find "$SRC_FOLDER" -maxdepth 1 -iname '*.mpg' | while read -r file; do
        filename=$(basename "$file")

        if [ -f "$DEST_FOLDER/$filename" ]; then
            echo "Skipping existing file: $filename"
        else
            cp "$file" "$DEST_FOLDER/"
            echo "Copied: $filename"
        fi
    done

    echo
    echo "Ingest complete."
    break
done
