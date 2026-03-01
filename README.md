# PVE VDI Client

[![GitHub release](https://img.shields.io/github/v/release/jbergquist/PVE-VDIClient)](https://github.com/jbergquist/PVE-VDIClient/releases/latest)
[![GitHub downloads](https://img.shields.io/github/downloads/jbergquist/PVE-VDIClient/total)](https://github.com/jbergquist/PVE-VDIClient/releases)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://www.apache.org/licenses/LICENSE-2.0)

This project's focus is to create a simple VDI client intended for mass deployment. This VDI client connects directly to Proxmox VE and allows users to connect (via Spice) to any VMs they have permission to access.

## Credits

This project builds on the excellent work of:

- **[joshpatten](https://github.com/joshpatten)** - Original creator of [PVE-VDIClient](https://github.com/joshpatten/PVE-VDIClient). An awesome human being for starting this project and making VDI access to Proxmox so accessible. The foundation of everything we have today! 🙏

- **[stefan-ffr](https://github.com/stefan-ffr)** - Created the [Flask port](https://github.com/stefan-ffr/PVE-VDIClient) that replaced the GTK interface with a modern web-based UI. This brilliant move meant users only need a browser - no heavy GUI dependencies. The game-changing fork that made mass deployment practical! 🚀

This repository continues their vision with cross-platform packaging, security improvements, and modern distribution methods.

## Configuration File

PVE VDI Client **REQUIRES** a configuration file to function. The client searches for this file in the following locations unless overridden with [command line options](#command-line-usage):

- Windows
  - %APPDATA%\VDIClient\vdiclient.ini
  - %PROGRAMFILES%\VDIClient\vdiclient.ini
- Linux
  - ~/.config/VDIClient/vdiclient.ini
  - /etc/vdiclient/vdiclient.ini
  - /usr/local/etc/vdiclient/vdiclient.ini

Please refer to [vdiclient.ini.example](https://github.com/jbergquist/PVE-VDIClient/blob/main/vdiclient.ini.example) for all available config file options

If you encounter any issues feel free to submit an issue report.

## Proxmox Permission Requirements

Users that are accessing VDI instances need to have the following permissions assigned for each VM they access:

- VM.PowerMgmt
- VM.Console
- VM.Audit

## Command Line Usage

No command line options are required for default behavior. The following command line options are available:

    usage: vdiclient.py [-h] [--list_themes] [--config_type {file,http}] [--config_location CONFIG_LOCATION]
                        [--config_username CONFIG_USERNAME] [--config_password CONFIG_PASSWORD] [--ignore_ssl]

    Proxmox VDI Client

    options:
      -h, --help            show this help message and exit
      --list_themes         List all available themes
      --config_type {file,http}
                            Select config type (default: file)
      --config_location CONFIG_LOCATION
                            Specify the config location (default: search for config file)
      --config_username CONFIG_USERNAME
                            HTTP basic authentication username (default: None)
      --config_password CONFIG_PASSWORD
                            HTTP basic authentication password (default: None)
      --ignore_ssl          HTTPS ignore SSL certificate errors (default: False)

If `--config_type http` is selected, pass the URL in the `--config_location` parameter

## Installation

**Prerequisites**: All platforms require [virt-viewer](https://www.spice-space.org/download.html) for VM console access.

### Quick Install

**Linux (Debian/Ubuntu)**:

```bash
wget https://github.com/jbergquist/PVE-VDIClient/releases/latest/download/pve-vdiclient_2.0.2-1_all.deb
sudo dpkg -i pve-vdiclient_2.0.2-1_all.deb
sudo apt install virt-viewer
```

**Linux (Fedora/RHEL)**:

```bash
sudo dnf install https://github.com/jbergquist/PVE-VDIClient/releases/latest/download/pve-vdiclient-2.0.2-1.noarch.rpm virt-viewer
```

**Linux (AppImage - Universal)**:

```bash
wget https://github.com/jbergquist/PVE-VDIClient/releases/latest/download/VDIClient-2.0.2-x86_64.AppImage
chmod +x VDIClient-2.0.2-x86_64.AppImage
./VDIClient-2.0.2-x86_64.AppImage
```

**Linux (Flatpak)**:

```bash
flatpak install https://github.com/jbergquist/PVE-VDIClient/releases/latest/download/org.proxmox.VDIClient.flatpak
flatpak run org.proxmox.VDIClient
```

**Windows**:

1. Install [virt-viewer](https://www.spice-space.org/download.html)
2. Download and run [vdiclient-2.0.2-64.msi](https://github.com/jbergquist/PVE-VDIClient/releases/latest)

**Python (pip)**:

```bash
pip install pve-vdiclient
```

For detailed installation instructions, see [docs/INSTALLATION.md](docs/INSTALLATION.md).

## Building from Source

See [docs/BUILDING.md](docs/BUILDING.md) for complete build instructions for all package formats.

---

## Legacy Installation Methods

### Windows Installation (Manual)

You **MUST** install virt-viewer prior to using PVE VDI client, you may download it from the [official SPICE website](https://www.spice-space.org/download.html).

If you need to customize the installation, such as to sign the executable and MSI, you may download and install the [WIX toolset](https://wixtoolset.org/releases/) and use the build_vdiclient.bat file to build a new MSI.

you will need to download the latest 3.12 python release, and run the following commands to install the necessary packages:

    requirements.bat

### Linux Installation (Manual)

**Note**: Use the [native packages](#installation) above for easier installation and updates.

Run the following commands on a Debian/Ubuntu Linux system to install the appropriate prerequisites

    apt install python3-pip virt-viewer git
    git clone https://github.com/jbergquist/PVE-VDIClient.git
    cd ./PVE-VDIClient/
    chmod +x requirements.sh
    ./requirements.sh
    cp vdiclient.py /usr/local/bin
    chmod +x /usr/local/bin/vdiclient.py

### Fedora/CentOS/RHEL Installation (Manual)

**Note**: Use the [native packages](#installation) above for easier installation and updates.

Run the following commands on a RHEL/Fedora Linux system to install the appropriate prerequisites

    dnf install python3-pip virt-viewer git
    git clone https://github.com/jbergquist/PVE-VDIClient.git
    cd ./PVE-VDIClient/
    chmod +x requirements.sh
    ./requirements.sh
    cp vdiclient.py /usr/local/bin
    chmod +x /usr/local/bin/vdiclient.py

### Build Debian/Ubuntu Linux Binary (Legacy)

**Note**: Use the [modern build scripts](docs/BUILDING.md) for current packaging methods.

Run the following commands if you wish to build a binary on a Debian/Ubuntu Linux system

    apt install python3-pip virt-viewer git
    git clone https://github.com/jbergquist/PVE-VDIClient.git
    cd ./PVE-VDIClient/
    chmod +x requirements.sh
    ./requirements.sh
    pip3 install pyinstaller
    pyinstaller --onefile --noconsole --noconfirm --hidden-import proxmoxer.backends --hidden-import proxmoxer.backends.https --hidden-import proxmoxer.backends.https.AuthenticationError --hidden-import proxmoxer.core --hidden-import proxmoxer.core.ResourceException --hidden-import subprocess.TimeoutExpired --hidden-import subprocess.CalledProcessError --hidden-import requests.exceptions --hidden-import requests.exceptions.ReadTimeout --hidden-import requests.exceptions.ConnectTimeout --hidden-import requests.exceptions.ConnectionError vdiclient.py

Once pyinstaller has finished your binary will be located in dist/vdiclient
