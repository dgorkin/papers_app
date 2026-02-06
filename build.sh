#!/bin/bash
# Build script for Linux/macOS
# Run from the project root directory

set -e

echo "Installing dependencies..."
pip install -r requirements.txt

echo ""
echo "Building executable with PyInstaller..."
pyinstaller literaturemanager.spec --clean

echo ""
echo "Build complete! Output in dist/LiteratureManager/"
echo "Run dist/LiteratureManager/LiteratureManager to launch."
