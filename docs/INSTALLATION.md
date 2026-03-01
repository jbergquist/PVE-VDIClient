# Installation Guide

Complete installation instructions for PVE VDI Client on all supported platforms.

## Prerequisites

**All platforms require virt-viewer** for VM console access:

- **Download**: <https://www.spice-space.org/download.html>
- **Purpose**: Launches SPICE remote desktop sessions to VMs

## Installation Methods

### Linux - Debian/Ubuntu (.deb)

**Install from GitHub Release**:

```bash
# Download latest release
wget https://github.com/jbergquist/PVE-VDIClient/releases/latest/download/pve-vdiclient_2.0.2-1_all.deb

# Install package
sudo dpkg -i pve-vdiclient_2.0.2-1_all.deb

# Install dependencies (if needed)
sudo apt-get install -f

# Install virt-viewer
sudo apt install virt-viewer
```

**Verify installation**:

```bash
vdiclient --help
which vdiclient
```

---

### Linux - Fedora/RHEL (.rpm)

**Install from GitHub Release**:

```bash
# Download and install in one command
sudo dnf install https://github.com/jbergquist/PVE-VDIClient/releases/latest/download/pve-vdiclient-2.0.2-1.noarch.rpm

# Install virt-viewer
sudo dnf install virt-viewer
```

**Alternative (manual download)**:

```bash
wget https://github.com/jbergquist/PVE-VDIClient/releases/latest/download/pve-vdiclient-2.0.2-1.noarch.rpm
sudo rpm -ivh pve-vdiclient-2.0.2-1.noarch.rpm
```

---

### Linux - AppImage (Universal)

**No installation required** - runs on any Linux distribution:

```bash
# Download AppImage
wget https://github.com/jbergquist/PVE-VDIClient/releases/latest/download/VDIClient-2.0.2-x86_64.AppImage

# Make executable
chmod +x VDIClient-2.0.2-x86_64.AppImage

# Run directly
./VDIClient-2.0.2-x86_64.AppImage

# Or move to ~/bin for global access
mkdir -p ~/bin
mv VDIClient-2.0.2-x86_64.AppImage ~/bin/vdiclient
```

**Desktop integration (optional)**:

```bash
# Extract and integrate with system
./VDIClient-2.0.2-x86_64.AppImage --appimage-extract
# Then use AppImageLauncher or manually add to menus
```

**Note**: Requires virt-viewer installed separately on the host system.

---

### Linux - Flatpak (Sandboxed)

**Install from bundle**:

```bash
# Download Flatpak bundle
wget https://github.com/jbergquist/PVE-VDIClient/releases/latest/download/org.proxmox.VDIClient.flatpak

# Install for current user
flatpak install --user org.proxmox.VDIClient.flatpak

# Run
flatpak run org.proxmox.VDIClient
```

**Add to application menu**: Flatpak automatically integrates with GNOME Software, KDE Discover, and application menus.

**Note**: virt-viewer must be installed on host system (not bundled in Flatpak sandbox).

---

### Windows - MSI Installer

**Installation steps**:

1. **Install virt-viewer** (required first):
   - Download from <https://www.spice-space.org/download.html>
   - Run installer and complete setup

2. **Install VDI Client**:
   - Download [vdiclient-2.0.2-64.msi](https://github.com/jbergquist/PVE-VDIClient/releases/latest/download/vdiclient-2.0.2-64.msi)
   - Double-click to run installer
   - Follow installation wizard

3. **Launch**:
   - Start Menu: "VDI Client"
   - Desktop shortcut (if selected during install)
   - Or run: `C:\Program Files\VDIClient\vdiclient.exe`

---

### Python - pip (Developer Install)

**For developers or users who prefer pip**:

```bash
# From PyPI (when published)
pip install pve-vdiclient

# From source (development)
git clone https://github.com/jbergquist/PVE-VDIClient.git
cd PVE-VDIClient
pip install -e .

# Run
vdiclient
```

**Install virt-viewer separately** based on your OS (see links above).

---

## Configuration

### Config File Locations

The client searches for `vdiclient.ini` in these locations (first found wins):

**Linux**:

- `~/.config/VDIClient/vdiclient.ini` (XDG standard)
- `/etc/vdiclient/vdiclient.ini` (system-wide)
- `/usr/local/etc/vdiclient/vdiclient.ini`

**Windows**:

- `%APPDATA%\VDIClient\vdiclient.ini`
- `C:\Program Files\VDIClient\vdiclient.ini`
- `C:\Program Files (x86)\VDIClient\vdiclient.ini`

### Example Configuration

Copy `vdiclient.ini.example` to one of the config locations and customize:

```ini
[General]
title = My VDI Client
loglevel = INFO

[PVE-Cluster1]
host = pve1.example.com,pve2.example.com,pve3.example.com
realm = pve
verify_ssl = true
```

See `vdiclient.ini.example` for all available options.

---

## Platform Comparison

| Platform | Method | Size | Installation | Updates |
|----------|--------|------|--------------|---------|
| Debian/Ubuntu | .deb | ~2MB | Native (dpkg/apt) | Manual |
| Fedora/RHEL | .rpm | ~2MB | Native (dnf/yum) | Manual |
| Any Linux | AppImage | ~100MB | None (portable) | Manual |
| Any Linux | Flatpak | ~3MB | flatpak | Auto (via Flathub) |
| Windows | MSI | ~50MB | Installer | Manual |
| Any | pip | <1MB | pip install | pip upgrade |

---

## Troubleshooting

### "virt-viewer not found"

**Solution**: Install virt-viewer from <https://www.spice-space.org/download.html>

### "Config file not found"

**Solution**: Create `vdiclient.ini` in one of the config locations listed above, or specify with:

```bash
vdiclient --config_location /path/to/vdiclient.ini
```

### "Permission denied" (Linux)

**Solution**: Ensure executable permissions:

```bash
chmod +x vdiclient  # or AppImage file
```

### AppImage won't run

**Solution**: Install FUSE2 (most distros have it):

```bash
# Debian/Ubuntu
sudo apt install fuse

# Fedora/RHEL
sudo dnf install fuse
```

### Windows: "Application failed to start"

**Solution**: Install Visual C++ Redistributable from Microsoft if not already installed.

---

## Uninstallation

**Debian/Ubuntu**:

```bash
sudo apt remove pve-vdiclient
```

**Fedora/RHEL**:

```bash
sudo dnf remove pve-vdiclient
```

**AppImage**:

```bash
rm VDIClient-*.AppImage
```

**Flatpak**:

```bash
flatpak uninstall org.proxmox.VDIClient
```

**Windows**:

- Control Panel → Programs and Features → VDI Client → Uninstall

**pip**:

```bash
pip uninstall pve-vdiclient
```

---

## Next Steps

- See [BUILDING.md](BUILDING.md) for build instructions
- See [README.md](../README.md) for usage and configuration
- Report issues: <https://github.com/jbergquist/PVE-VDIClient/issues>
