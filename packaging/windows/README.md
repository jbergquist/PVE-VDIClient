# Windows MSI Packaging

Build Windows MSI installer for PVE VDI Client using PyInstaller and WIX Toolset.

## Prerequisites

1. **Python 3.12+** with pip
2. **PyInstaller**: `pip install pyinstaller`
3. **WIX Toolset 3.x**: Download from <https://wixtoolset.org/>
4. **virt-viewer** (runtime dependency): <https://www.spice-space.org/download.html>

## Build Methods

### Option 1: Batch Script (Windows)

```cmd
packaging\windows\build.bat
```

### Option 2: PowerShell (Windows/GitHub Actions)

```powershell
.\packaging\windows\build.ps1
```

### Option 3: Manual Build

```cmd
# Step 1: Build executable with PyInstaller
pyinstaller --noconfirm packaging\windows\vdiclient.spec

# Step 2: Create MSI (requires WIX Toolset)
cd dist
python ..\packaging\windows\wix\createmsi.py ..\packaging\windows\wix\vdiclient.json
```

## Output

- **Executable**: `dist/vdiclient/vdiclient.exe` (~50MB)
- **MSI Installer**: `vdiclient-2.0.2-64.msi` (~50MB)

## Installation

1. Install virt-viewer from <https://www.spice-space.org/download.html>
2. Run `vdiclient-2.0.2-64.msi`
3. Launch from Start Menu or Desktop shortcut

## MSI Configuration

Edit `wix/vdiclient.json` to customize:

- Version number
- Product name and manufacturer
- Install directory
- Shortcuts (Start Menu, Desktop)
- Upgrade GUID (keep stable for upgrades)

## File Structure

```
packaging/windows/
├── build.bat              # Batch build script
├── build.ps1              # PowerShell build script
├── vdiclient.spec         # PyInstaller specification
├── wix/
│   ├── createmsi.py       # WIX wrapper script
│   ├── vdiclient.json     # MSI configuration
│   └── License.rtf        # License for installer
└── README.md              # This file
```

## Troubleshooting

**PyInstaller not found:**

```cmd
pip install pyinstaller
```

**WIX Toolset not in PATH:**

Add WIX bin directory to PATH:

```cmd
set PATH=%PATH%;C:\Program Files (x86)\WiX Toolset v3.11\bin
```

**Missing dependencies in exe:**

Add to `hiddenimports` in `vdiclient.spec`.

**MSI won't install over old version:**

Uninstall previous version first, or use same upgrade GUID.
