#!/bin/bash
# Build and publish Python package to PyPI

set -e  # Exit on error
set -u  # Exit on undefined variable

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

echo "=== Building Python package for PyPI ==="

cd "$PROJECT_ROOT"

# Read version
VERSION=$(python3 -c "exec(open('vdiclient/__init__.py').read()); print(__version__)")
echo "Package version: $VERSION"

# Clean previous builds
echo "Cleaning previous builds..."
rm -rf build/ dist/ ./*.egg-info

# Install/upgrade build tools
echo "Installing build dependencies..."
python3 -m pip install --upgrade pip build twine

# Build source distribution and wheel
echo "Building package..."
python3 -m build

# Check the distribution
echo "Checking package with twine..."
if twine check dist/*; then
    echo ""
    echo "=== Build successful! ==="
    echo "Packages created:"
    ls -lh dist/
    echo ""
    echo "To test locally:"
    echo "  pip install dist/pve_vdiclient-$VERSION-py3-none-any.whl"
    echo ""
    echo "To upload to TestPyPI (for testing):"
    echo "  twine upload --repository testpypi dist/*"
    echo ""
    echo "To upload to PyPI (production):"
    echo "  twine upload dist/*"
    echo ""
    echo "Note: Requires PyPI API token configured in ~/.pypirc"
else
    echo "ERROR: Package check failed!"
    exit 1
fi
