#!/bin/bash
# Build AppImage for PVE VDI Client

set -e  # Exit on error
set -u  # Exit on undefined variable

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
APPIMAGE_DIR="$SCRIPT_DIR/appimage"
BUILD_DIR="$PROJECT_ROOT/build/appimage"

echo "=== Building AppImage ==="
echo "Project root: $PROJECT_ROOT"

cd "$PROJECT_ROOT"

# Read version from vdiclient/__init__.py
VERSION=$(python3 -c "exec(open('vdiclient/__init__.py').read()); print(__version__)")
echo "Package version: $VERSION"

# Clean previous build
echo "Cleaning previous build artifacts..."
rm -rf "$BUILD_DIR"
rm -f VDIClient-*.AppImage

# Create AppDir structure
APPDIR="$BUILD_DIR/VDIClient.AppDir"
mkdir -p "$APPDIR/usr/bin"
mkdir -p "$APPDIR/usr/lib"
mkdir -p "$APPDIR/usr/share/applications"
mkdir -p "$APPDIR/usr/share/icons/hicolor/256x256/apps"

# Install Python and dependencies using pip
echo "Installing Python and dependencies..."
python3 -m pip install --target="$APPDIR/usr/lib/python3.12/site-packages" \
    --no-compile \
    --no-warn-script-location \
    .

# Install Python executable (AppImage will bundle it)
echo "Copying Python executable..."
cp "$(which python3)" "$APPDIR/usr/bin/"

# Copy AppRun script
echo "Installing AppRun..."
cp "$APPIMAGE_DIR/AppRun" "$APPDIR/"
chmod +x "$APPDIR/AppRun"

# Copy desktop file
echo "Installing desktop file..."
cp "$APPIMAGE_DIR/vdiclient.desktop" "$APPDIR/"
cp "$APPIMAGE_DIR/vdiclient.desktop" "$APPDIR/usr/share/applications/"

# Copy icon
echo "Installing icon..."
cp vdiclient/static/vdiclient.png "$APPDIR/vdiclient.png"
cp vdiclient/static/vdiclient.png \
    "$APPDIR/usr/share/icons/hicolor/256x256/apps/vdiclient.png"

# Download appimagetool if not present
APPIMAGETOOL="$BUILD_DIR/appimagetool-x86_64.AppImage"
if [ ! -f "$APPIMAGETOOL" ]; then
    echo "Downloading appimagetool..."
    wget -q -O "$APPIMAGETOOL" \
        "https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage"
    chmod +x "$APPIMAGETOOL"
fi

# Build AppImage
# APPIMAGE_EXTRACT_AND_RUN=1 lets appimagetool run in containers where FUSE
# kernel module is unavailable (it extracts itself instead of mounting)
echo "Building AppImage..."
cd "$BUILD_DIR"
ARCH=x86_64 APPIMAGE_EXTRACT_AND_RUN=1 \
    "$APPIMAGETOOL" "$APPDIR" "$PROJECT_ROOT/VDIClient-$VERSION-x86_64.AppImage"

# Verify the AppImage was created
APPIMAGE_FILE="$PROJECT_ROOT/VDIClient-$VERSION-x86_64.AppImage"
if [ -f "$APPIMAGE_FILE" ]; then
    echo ""
    echo "=== Build successful! ==="
    echo "AppImage: $APPIMAGE_FILE"
    echo "Size: $(du -h "$APPIMAGE_FILE" | cut -f1)"
    echo ""
    echo "To run:"
    echo "  chmod +x $APPIMAGE_FILE"
    echo "  $APPIMAGE_FILE"
    echo ""
    echo "To integrate with system:"
    echo "  $APPIMAGE_FILE --appimage-extract"
    echo "  # or use AppImageLauncher"
    echo ""
    echo "Note: Requires virt-viewer to be installed separately:"
    echo "  - Debian/Ubuntu: apt install virt-viewer"
    echo "  - Fedora/RHEL: dnf install virt-viewer"
    echo "  - Arch: pacman -S virt-viewer"
else
    echo "ERROR: AppImage file not found!"
    exit 1
fi

echo "Build complete!"
