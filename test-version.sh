#!/bin/bash
# Script to verify version consistency across all files

echo "=== Version Verification ==="
echo ""

# Backend version
BACKEND_VERSION=$(grep 'VERSION = ' backend/version.py | sed "s/VERSION = \"\(.*\)\"/\1/")
echo "Backend (version.py):    $BACKEND_VERSION"

# Frontend version
FRONTEND_VERSION=$(grep 'export const VERSION' frontend/src/utils/version.js | sed "s/export const VERSION = \"\(.*\)\";/\1/")
echo "Frontend (version.js):   $FRONTEND_VERSION"

# Package.json version
PACKAGE_VERSION=$(grep '"version"' frontend/package.json | sed 's/.*"version": "\(.*\)".*/\1/')
echo "Frontend (package.json): $PACKAGE_VERSION"

echo ""

# Check if all versions match
if [ "$BACKEND_VERSION" == "$FRONTEND_VERSION" ] && [ "$FRONTEND_VERSION" == "$PACKAGE_VERSION" ]; then
    echo "✓ All versions match: $BACKEND_VERSION"
    exit 0
else
    echo "✗ Version mismatch detected!"
    echo "  Backend:    $BACKEND_VERSION"
    echo "  Frontend:   $FRONTEND_VERSION"
    echo "  Package:    $PACKAGE_VERSION"
    exit 1
fi


