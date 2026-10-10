#!/usr/bin/env bash
set -e

# Use PYTHON_BIN environment variable if set, otherwise default to python3
PYTHON_CMD="${PYTHON_BIN:-python3}"

echo "Using Python interpreter: $PYTHON_CMD"

# Check if requirements.txt exists and install dependencies if available
if [ -f "requirements.txt" ]; then
    echo "Installing dependencies from requirements.txt..."
    "$PYTHON_CMD" -m pip install -r requirements.txt
else
    echo "Warning: requirements.txt not found, skipping dependency installation."
fi

# Define the installation directory and ensure it exists
INSTALL_DIR="$HOME/.local/bin"
mkdir -p "$INSTALL_DIR"

# Define source and target file paths
SOURCE_FILE="pixelart2svg.py"
TARGET_FILE="$INSTALL_DIR/pixelart2svg"

# Verify that the source script exists in the current directory before copying
if [ ! -f "$SOURCE_FILE" ]; then
    echo "Error: $SOURCE_FILE not found in the current directory."
    exit 1
fi

# Copy the python script to the local bin directory and make it executable
echo "Copying $SOURCE_FILE to $TARGET_FILE..."
cp "$SOURCE_FILE" "$TARGET_FILE"
chmod +x "$TARGET_FILE"

echo "Setup completed successfully. Make sure $INSTALL_DIR is in your PATH."
