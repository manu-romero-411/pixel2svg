#!/usr/bin/env bash
set -e

# Configuration file
CONFIG_FILE="pyproject.toml"

# Check if pyproject.toml exists
if [ ! -f "$CONFIG_FILE" ]; then
    echo "Error: $CONFIG_FILE not found in the current directory."
    exit 1
fi

# Extract current version
CURRENT_VERSION=$(grep -E '^version\s*=' "$CONFIG_FILE" | sed -E 's/version\s*=\s*"(.*)"/\1/')

if [ -z "$CURRENT_VERSION" ]; then
    echo "Error: Could not find version in $CONFIG_FILE."
    exit 1
fi

echo "Current version in $CONFIG_FILE is: $CURRENT_VERSION"
read -p "Enter the new version to release: " NEW_VERSION

# Validate that a version was entered
if [ -z "$NEW_VERSION" ]; then
    echo "Error: Version cannot be empty."
    exit 1
fi

echo "Updating version to: $NEW_VERSION"

# Update version in pyproject.toml (cross-platform compatible sed)
if [[ "$OSTYPE" == "darwin"* ]]; then
    sed -i '' "s/version = \"$CURRENT_VERSION\"/version = \"$NEW_VERSION\"/" "$CONFIG_FILE"
else
    sed -i "s/version = \"$CURRENT_VERSION\"/version = \"$NEW_VERSION\"/" "$CONFIG_FILE"
fi

# Clean previous build and distribution artifacts
echo "Cleaning old build and distribution directories..."
rm -rf dist/ build/ *.egg-info

# Build the package
echo "Building new distribution packages..."
python -m build

# Upload to PyPI using twine
echo "Uploading package to PyPI..."
python -m twine upload dist/*

echo "Deployment completed successfully for version $NEW_VERSION!"
