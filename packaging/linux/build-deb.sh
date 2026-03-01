#!/bin/bash
# Build Debian .deb package for PVE VDI Client

set -e  # Exit on error
set -u  # Exit on undefined variable

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
BUILD_DIR="$PROJECT_ROOT/build/debian"

echo "=== Building Debian .deb package ==="
echo "Project root: $PROJECT_ROOT"

cd "$PROJECT_ROOT"

# Clean previous build artifacts
echo "Cleaning previous build artifacts..."
rm -rf "$BUILD_DIR" build/ dist/ debian/
rm -f ./*.egg-info
rm -f ../pve-vdiclient_*.deb ../pve-vdiclient_*.tar.gz ../pve-vdiclient_*.dsc ../pve-vdiclient_*.changes

# Copy debian/ directory to project root (required by debuild)
echo "Copying debian/ packaging files..."
cp -r packaging/linux/debian .

# Install build dependencies (if running interactively)
if [ -t 0 ]; then
    echo "Installing build dependencies..."
    sudo apt-get update || true
    sudo apt-get install -y \
        debhelper \
        dh-python \
        python3-all \
        python3-setuptools \
        python3-stdeb \
        python3-flask \
        python3-requests \
        python3-urllib3 \
        python3-proxmoxer || echo "Warning: Could not install all dependencies"
fi

# Build the package using debuild (preferred) or stdeb
if command -v debuild &> /dev/null; then
    echo "Building with debuild..."
    debuild -us -uc -b
else
    echo "Building with stdeb..."
    python3 setup.py --command-packages=stdeb.command bdist_deb
fi

# Find and display the generated .deb file
DEB_FILE=$(find .. -maxdepth 1 -name "pve-vdiclient_*.deb" -type f | head -1)

if [ -n "$DEB_FILE" ]; then
    echo ""
    echo "=== Build successful! ==="
    echo "Package: $DEB_FILE"
    echo ""
    echo "To install:"
    echo "  sudo dpkg -i $DEB_FILE"
    echo "  sudo apt-get install -f  # Fix dependencies if needed"
    echo ""
    echo "To verify package contents:"
    echo "  dpkg -c $DEB_FILE"
    echo ""
    echo "To verify package info:"
    echo "  dpkg -I $DEB_FILE"
else
    echo "ERROR: .deb file not found!"
    exit 1
fi

# Clean up debian/ directory from project root
rm -rf debian/

echo "Build complete!"
