#!/bin/bash
# Script to increment the minor version number
# Usage: ./increment-version.sh

# Get current version from backend/version.py
CURRENT_VERSION=$(grep 'VERSION = ' backend/version.py | sed "s/VERSION = \"\(.*\)\"/\1/")

# Parse version components
IFS='.' read -ra VERSION_PARTS <<< "$CURRENT_VERSION"
MAJOR=${VERSION_PARTS[0]}
MINOR=${VERSION_PARTS[1]}
PATCH=${VERSION_PARTS[2]}

# Increment minor version
NEW_MINOR=$((MINOR + 1))
NEW_VERSION="${MAJOR}.${NEW_MINOR}.${PATCH}"

echo "Current version: ${CURRENT_VERSION}"
echo "New version: ${NEW_VERSION}"

# Update backend version
sed -i '' "s/VERSION = \"${CURRENT_VERSION}\"/VERSION = \"${NEW_VERSION}\"/" backend/version.py

# Update frontend version
sed -i '' "s/export const VERSION = \"${CURRENT_VERSION}\"/export const VERSION = \"${NEW_VERSION}\"/" frontend/src/utils/version.js

# Update package.json version
sed -i '' "s/\"version\": \"${CURRENT_VERSION}\"/\"version\": \"${NEW_VERSION}\"/" frontend/package.json

echo "Version updated to ${NEW_VERSION} in:"
echo "  - backend/version.py"
echo "  - frontend/src/utils/version.js"
echo "  - frontend/package.json"


