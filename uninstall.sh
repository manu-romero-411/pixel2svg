#!/usr/bin/env bash
set -e

# Define the target executable path to remove
TARGET_FILE="$HOME/.local/bin/pixel2svg"

# Check if the executable exists before attempting to delete it
if [ -f "$TARGET_FILE" ]; then
    echo "Removing $TARGET_FILE..."
    rm "$TARGET_FILE"
    echo "Uninstallation completed successfully."
else
    echo "Executable not found at $TARGET_FILE. Nothing to remove."
fi
