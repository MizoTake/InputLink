#!/bin/bash
# macOS/Linux build script for Input Link

set -e  # Exit on error

echo "Building Input Link for $(uname)..."

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 not found"
    exit 1
fi

# Check if we're in the correct directory
if [ ! -f "pyproject.toml" ]; then
    echo "Error: Please run this script from the project root directory"
    exit 1
fi

# Create and activate virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

echo "Activating virtual environment..."
source .venv/bin/activate

# Install build dependencies
echo "Installing build dependencies..."
pip install -e ".[build]" --quiet

# Run build script
python3 scripts/build/build.py

echo ""
echo "Build complete! Check the dist/ directory for executables."

# On macOS, show additional instructions
if [[ "$OSTYPE" == "darwin"* ]]; then
    echo ""
    echo "📱 macOS Notes:"
    echo "  • .app bundles created in dist/ directory"
    echo "  • You may need to allow the apps in System Preferences > Security & Privacy"
    echo "  • For distribution, consider code signing and notarization"
fi