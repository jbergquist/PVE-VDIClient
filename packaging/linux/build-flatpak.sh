#!/bin/bash
# Build Flatpak package for PVE VDI Client

set -e  # Exit on error
set -u  # Exit on undefined variable

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
FLATPAK_DIR="$SCRIPT_DIR/flatpak"
BUILD_DIR="$PROJECT_ROOT/build/flatpak"
REPO_DIR="$PROJECT_ROOT/flatpak-repo"

APP_ID="org.proxmox.VDIClient"

echo "=== Building Flatpak package ==="
echo "Project root: $PROJECT_ROOT"

cd "$PROJECT_ROOT"

# Read version from vdiclient/__init__.py
VERSION=$(python3 -c "exec(open('vdiclient/__init__.py').read()); print(__version__)")
echo "Package version: $VERSION"

# Check for flatpak-builder
if ! command -v flatpak-builder &> /dev/null; then
    echo "ERROR: flatpak-builder not found!"
    echo "Install with:"
    echo "  Debian/Ubuntu: apt install flatpak-builder"
    echo "  Fedora/RHEL: dnf install flatpak-builder"
    echo "  Arch: pacman -S flatpak-builder"
    exit 1
fi

# Check for required runtimes
if ! flatpak list --runtime | grep -q "org.freedesktop.Platform"; then
    echo "Installing required Flatpak runtime..."
    flatpak install -y flathub org.freedesktop.Platform//23.08 || true
    flatpak install -y flathub org.freedesktop.Sdk//23.08 || true
fi

# Clean previous build
echo "Cleaning previous build artifacts..."
rm -rf "$BUILD_DIR" "$REPO_DIR"
rm -f "$PROJECT_ROOT/$APP_ID.flatpak"

# Create repo directory
mkdir -p "$REPO_DIR"

# Build the Flatpak
echo "Building Flatpak..."
cd "$PROJECT_ROOT"
flatpak-builder --force-clean --disable-rofiles-fuse --repo="$REPO_DIR" \
    "$BUILD_DIR" \
    "$FLATPAK_DIR/$APP_ID.yml"

# Export the build as a single-file bundle
echo "Creating Flatpak bundle..."
flatpak build-bundle "$REPO_DIR" \
    "$PROJECT_ROOT/$APP_ID.flatpak" \
    "$APP_ID"

# Verify the bundle was created
FLATPAK_FILE="$PROJECT_ROOT/$APP_ID.flatpak"
if [ -f "$FLATPAK_FILE" ]; then
    echo ""
    echo "=== Build successful! ==="
    echo "Flatpak: $FLATPAK_FILE"
    echo "Size: $(du -h "$FLATPAK_FILE" | cut -f1)"
    echo ""
    echo "To install:"
    echo "  flatpak install --user $FLATPAK_FILE"
    echo ""
    echo "To run:"
    echo "  flatpak run $APP_ID"
    echo ""
    echo "To test (without install):"
    echo "  flatpak-builder --run $BUILD_DIR $FLATPAK_DIR/$APP_ID.yml vdiclient"
    echo ""
    echo "To submit to Flathub:"
    echo "  1. Fork https://github.com/flathub/flathub"
    echo "  2. Add $APP_ID.yml to your fork"
    echo "  3. Create pull request"
    echo ""
    echo "Note: Requires virt-viewer on host system"
else
    echo "ERROR: Flatpak bundle not found!"
    exit 1
fi

echo "Build complete!"
