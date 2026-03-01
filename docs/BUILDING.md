# Building from Source

Developer guide for building PVE VDI Client packages from source.

## Development Setup

### Prerequisites

- **Python 3.12+**
- **Git**
- **pip** (Python package installer)

### Clone Repository

```bash
git clone https://github.com/jbergquist/PVE-VDIClient.git
cd PVE-VDIClient
```

### Install in Development Mode

```bash
# Install package in editable mode
pip install -e .

# Install development dependencies
pip install -e ".[dev]"

# Run directly
vdiclient --help
python -m vdiclient --help
```

---

## Building Packages

### Debian/Ubuntu (.deb)

**Prerequisites**:

```bash
sudo apt-get install \
    debhelper \
    dh-python \
    python3-all \
    python3-setuptools \
    python3-stdeb
```

**Build**:

```bash
./packaging/linux/build-deb.sh
```

**Output**: `../pve-vdiclient_2.0.2-1_all.deb`

**Test locally**:

```bash
sudo dpkg -i ../pve-vdiclient_2.0.2-1_all.deb
vdiclient --version
```

---

### Fedora/RHEL (.rpm)

**Prerequisites**:

```bash
sudo dnf install \
    rpm-build \
    python3-devel \
    python3-setuptools \
    python3-pip
```

**Build**:

```bash
./packaging/linux/build-rpm.sh
```

**Output**: `~/rpmbuild/RPMS/noarch/pve-vdiclient-2.0.2-1.noarch.rpm`

**Test locally**:

```bash
sudo rpm -ivh ~/rpmbuild/RPMS/noarch/pve-vdiclient-2.0.2-1.noarch.rpm
vdiclient --version
```

---

### AppImage (Universal Linux)

**Prerequisites**:

```bash
sudo apt-get install python3-pip wget fuse libfuse2
```

**Build**:

```bash
./packaging/linux/build-appimage.sh
```

**Output**: `VDIClient-2.0.2-x86_64.AppImage`

**Test locally**:

```bash
chmod +x VDIClient-2.0.2-x86_64.AppImage
./VDIClient-2.0.2-x86_64.AppImage --help
```

---

### Flatpak (Sandboxed)

**Prerequisites**:

```bash
sudo apt-get install flatpak flatpak-builder
flatpak remote-add --if-not-exists flathub https://flathub.org/repo/flathub.flatpakrepo
flatpak install flathub org.freedesktop.Platform//23.08 org.freedesktop.Sdk//23.08
```

**Build**:

```bash
./packaging/linux/build-flatpak.sh
```

**Output**: `org.proxmox.VDIClient.flatpak`

**Test locally**:

```bash
flatpak install --user org.proxmox.VDIClient.flatpak
flatpak run org.proxmox.VDIClient
```

---

### Windows MSI

**Prerequisites**:

- **Python 3.12+** for Windows
- **PyInstaller**: `pip install pyinstaller`
- **WIX Toolset 3.x**: <https://wixtoolset.org/>

**Build (Command Prompt)**:

```cmd
packaging\windows\build.bat
```

**Build (PowerShell)**:

```powershell
.\packaging\windows\build.ps1
```

**Output**: `vdiclient-2.0.2-64.msi`

**Test locally**:

- Run the MSI installer
- Launch from Start Menu

---

### PyPI Package (Wheel)

**Prerequisites**:

```bash
pip install --upgrade build twine
```

**Build**:

```bash
./packaging/pypi/build.sh
```

**Output**:

- `dist/pve_vdiclient-2.0.2.tar.gz` (source)
- `dist/pve_vdiclient-2.0.2-py3-none-any.whl` (wheel)

**Test locally**:

```bash
pip install dist/pve_vdiclient-2.0.2-py3-none-any.whl
vdiclient --version
```

**Upload to PyPI**:

```bash
# Test on TestPyPI first
twine upload --repository testpypi dist/*

# Production upload
twine upload dist/*
```

---

## CI/CD (GitHub Actions)

The repository includes automated builds for all package formats.

### Workflow File

`.github/workflows/build-packages.yml`

### Trigger Automatic Build

**On Pull Request** (validation only):

```bash
git checkout -b my-feature
git commit -am "feat: my feature"
git push origin my-feature
# Open PR - builds run automatically
```

**On Version Tag** (build + release):

```bash
# Update version in vdiclient/__init__.py
git commit -am "chore: bump version to 2.0.3"
git tag v2.0.3
git push origin main
git push origin v2.0.3
# GitHub Actions builds all packages and creates release
```

### Manual Workflow Dispatch

1. Go to GitHub Actions tab
2. Select "Build Multi-Platform Packages"
3. Click "Run workflow"
4. Select branch and run

### Build Matrix

All builds run in parallel (~15-20 minutes total):

- **build-deb**: Ubuntu runner
- **build-rpm**: Fedora container
- **build-appimage**: Ubuntu 20.04
- **build-flatpak**: Ubuntu latest
- **build-windows**: Windows runner

---

## Docker Build Environment

For reproducible builds, use Docker:

### Debian Builder

```bash
docker run --rm -v $(pwd):/workspace -w /workspace ubuntu:22.04 bash -c "
    apt-get update &&
    apt-get install -y debhelper dh-python python3-all python3-setuptools python3-stdeb &&
    ./packaging/linux/build-deb.sh
"
```

### Fedora Builder

```bash
docker run --rm -v $(pwd):/workspace -w /workspace fedora:latest bash -c "
    dnf install -y rpm-build python3-devel python3-setuptools &&
    ./packaging/linux/build-rpm.sh
"
```

---

## Linting and Validation

### Python Code

```bash
# Format with black
black vdiclient/ vdiclient.py setup.py

# Lint with flake8
flake8 vdiclient/ vdiclient.py setup.py

# Type check with mypy
mypy vdiclient/

# Lint with ruff
ruff check vdiclient/ vdiclient.py
```

### Shell Scripts

```bash
# Check all build scripts
shellcheck packaging/linux/build-*.sh
shellcheck packaging/pypi/build.sh
```

### YAML Files

```bash
# Validate GitHub Actions workflow
yamllint .github/workflows/build-packages.yml
```

### Debian Package

```bash
# After building .deb
lintian ../pve-vdiclient_*.deb
```

### RPM Package

```bash
# After building .rpm
rpmlint ~/rpmbuild/RPMS/noarch/pve-vdiclient-*.rpm
```

---

## Version Management

### Update Version

Edit `vdiclient/__init__.py`:

```python
__version__ = "2.0.3"
```

### Update Changelog

For .deb packages, update `packaging/linux/debian/changelog`:

```
pve-vdiclient (2.0.3-1) unstable; urgency=medium

  * New feature description
  * Bug fix description

 -- jbergquist <jbergquist@users.noreply.github.com>  Mon, 15 Mar 2026 10:00:00 +0000
```

For .rpm packages, update `packaging/linux/rpm/vdiclient.spec`:

```spec
%changelog
* Mon Mar 15 2026 jbergquist <jbergquist@users.noreply.github.com> - 2.0.3-1
- New feature description
- Bug fix description
```

---

## Troubleshooting

### Build Fails: "Module not found"

**Solution**: Install build dependencies for your platform (see Prerequisites sections above).

### "Permission denied" on build script

**Solution**:

```bash
chmod +x packaging/linux/build-*.sh
chmod +x packaging/pypi/build.sh
```

### Debian build: "debuild not found"

**Solution**:

```bash
sudo apt-get install devscripts
```

### AppImage: "appimagetool not found"

**Solution**: The build script downloads it automatically. Ensure `wget` is installed.

### Flatpak: "Runtime not found"

**Solution**:

```bash
flatpak install flathub org.freedesktop.Platform//23.08 org.freedesktop.Sdk//23.08
```

### Windows: "WIX Toolset not found"

**Solution**: Download and install from <https://wixtoolset.org/>, then add to PATH:

```cmd
set PATH=%PATH%;C:\Program Files (x86)\WiX Toolset v3.11\bin
```

---

## Contributing

When submitting changes:

1. Run linters (black, flake8, shellcheck)
2. Test package builds locally
3. Ensure CI/CD passes on PR
4. Update documentation if needed

See [CONTRIBUTING.md](../CONTRIBUTING.md) for detailed guidelines.

---

## Resources

- **GitHub Repository**: <https://github.com/jbergquist/PVE-VDIClient>
- **Issue Tracker**: <https://github.com/jbergquist/PVE-VDIClient/issues>
- **PyPI Package**: <https://pypi.org/project/pve-vdiclient/>
- **Debian Policy**: <https://www.debian.org/doc/debian-policy/>
- **Fedora Packaging**: <https://docs.fedoraproject.org/en-US/packaging-guidelines/>
- **Flatpak Documentation**: <https://docs.flatpak.org/>
- **AppImage Documentation**: <https://docs.appimage.org/>
