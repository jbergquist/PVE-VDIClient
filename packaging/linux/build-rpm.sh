#!/bin/bash
# Build RPM package for PVE VDI Client

set -e  # Exit on error
set -u  # Exit on undefined variable

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
SPEC_FILE="$SCRIPT_DIR/rpm/vdiclient.spec"

echo "=== Building RPM package ==="
echo "Project root: $PROJECT_ROOT"

cd "$PROJECT_ROOT"

# Read version from vdiclient/__init__.py
VERSION=$(python3 -c "exec(open('vdiclient/__init__.py').read()); print(__version__)")
echo "Package version: $VERSION"

# Setup RPM build environment
RPMBUILD_DIR="$HOME/rpmbuild"
mkdir -p "$RPMBUILD_DIR"/{BUILD,RPMS,SOURCES,SPECS,SRPMS}

# Clean previous build artifacts
echo "Cleaning previous build artifacts..."
rm -rf build/ dist/ ./*.egg-info
rm -f "$RPMBUILD_DIR"/RPMS/noarch/pve-vdiclient-*.rpm
rm -f "$RPMBUILD_DIR"/SRPMS/pve-vdiclient-*.src.rpm
rm -f "$RPMBUILD_DIR"/SOURCES/pve-vdiclient-*.tar.gz

# Create source tarball
echo "Creating source tarball..."
TARBALL="pve-vdiclient-$VERSION.tar.gz"
tar --exclude='.git' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='build' \
    --exclude='dist' \
    --exclude='*.egg-info' \
    --exclude='screenshots' \
    --transform="s,^,$PWD/pve-vdiclient-$VERSION/," \
    -czf "$RPMBUILD_DIR/SOURCES/$TARBALL" \
    vdiclient/ \
    vdiclient.py \
    setup.py \
    pyproject.toml \
    MANIFEST.in \
    README.md \
    LICENSE \
    requirements.txt \
    vdiclient.ini.example \
    packaging/linux/vdiclient.desktop

# Copy spec file
cp "$SPEC_FILE" "$RPMBUILD_DIR/SPECS/"

# Install build dependencies (if running interactively)
if [ -t 0 ]; then
    echo "Installing build dependencies..."
    if command -v dnf &> /dev/null; then
        sudo dnf install -y \
            rpm-build \
            python3-devel \
            python3-setuptools \
            python3-pip \
            python3-flask \
            python3-requests \
            python3-urllib3 || echo "Warning: Could not install all dependencies"
    elif command -v yum &> /dev/null; then
        sudo yum install -y \
            rpm-build \
            python3-devel \
            python3-setuptools \
            python3-pip || echo "Warning: Could not install all dependencies"
    fi
fi

# Build the RPM
echo "Building RPM package..."
cd "$RPMBUILD_DIR"
rpmbuild -ba "SPECS/vdiclient.spec"

# Find and display the generated RPM file
RPM_FILE=$(find RPMS/noarch -name "pve-vdiclient-*.rpm" -type f | head -1)

if [ -n "$RPM_FILE" ]; then
    echo ""
    echo "=== Build successful! ==="
    echo "Package: $RPMBUILD_DIR/$RPM_FILE"
    echo ""
    echo "To install:"
    echo "  sudo dnf install $RPMBUILD_DIR/$RPM_FILE"
    echo "  # or"
    echo "  sudo rpm -ivh $RPMBUILD_DIR/$RPM_FILE"
    echo ""
    echo "To verify package contents:"
    echo "  rpm -qlp $RPMBUILD_DIR/$RPM_FILE"
    echo ""
    echo "To verify package info:"
    echo "  rpm -qip $RPMBUILD_DIR/$RPM_FILE"

    # Copy RPM to project root for convenience
    cp "$RPMBUILD_DIR/$RPM_FILE" "$PROJECT_ROOT/"
    echo ""
    echo "Package also copied to: $PROJECT_ROOT/$(basename "$RPM_FILE")"
else
    echo "ERROR: RPM file not found!"
    exit 1
fi

echo "Build complete!"
