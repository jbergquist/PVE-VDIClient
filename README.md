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

And yes, this is vibe coded like never before, I didn't have the time for such a big rewrite so here we are. Claude Code did its thing like a boss.

## Configuration File

PVE VDI Client **REQUIRES** a configuration file to function. The client searches for this file in the following locations unless overridden with [command line options](#command-line-usage):

- Windows
  - %APPDATA%\VDIClient\vdiclient.ini
  - %PROGRAMFILES%\VDIClient\vdiclient.ini
- Linux
  - $XDG_CONFIG_HOME/VDIClient/vdiclient.ini (defaults to ~/.config/VDIClient/vdiclient.ini)
  - /etc/vdiclient/vdiclient.ini
  - /usr/local/etc/vdiclient/vdiclient.ini

Refer to [vdiclient.ini.example](https://github.com/jbergquist/PVE-VDIClient/blob/main/vdiclient.ini.example)
for a fully annotated reference. The sections and keys are described below.

### `[General]`

| Key | Description | Default |
| --- | ----------- | ------- |
| `title` | Title displayed to the user on all pages | `VDI Login` |
| `theme` | UI theme name (legacy option, not used by Flask UI) | `LightBlue` |
| `icon` | Path to program icon file | — |
| `logo` | Path to logo image displayed on login and dashboard | — |
| `kiosk` | Kiosk mode — prevents the user from closing the browser window | `False` |
| `viewer_kiosk` | Pass `--kiosk` to virt-viewer when `kiosk = True` | `True` |
| `fullscreen` | Launch virt-viewer in fullscreen (ignored when kiosk = True) | `True` |
| `window_width` | Override browser window width in pixels | — |
| `window_height` | Override browser window height in pixels | — |
| `inidebug` | Log the SPICE .ini file to the console before launching virt-viewer | `False` |
| `guest_type` | VM types to show: `both`, `lxc`, or `qemu` | `both` |
| `show_reset` | Show a Reset button on the VM dashboard | `False` |
| `show_hibernate` | Show a Hibernate button on the VM dashboard | `False` |
| `session_timeout` | Inactivity timeout in seconds before logging out; `0` disables | `0` |
| `server_shutdown_timeout` | Shut down the server N seconds after startup; `0` disables | `0` |
| `localhosttls` | Enable HTTPS with an auto-generated self-signed certificate | `False` |
| `log_level` | Log level: `DEBUG`, `INFO`, `WARNING`, `ERROR` (lowest priority — overridden by `--log-level` CLI flag or `LOG_LEVEL` env var) | `INFO` |

### `[Hosts.<Name>]`

Define one section per Proxmox cluster. `<Name>` is shown to the user in the cluster
selector (e.g. `[Hosts.PVE]` displays as **PVE**). Multiple sections can be defined.

| Key | Description | Default |
| --- | ----------- | ------- |
| `hostpool` | JSON dict of cluster nodes: `{"IP/FQDN": PORT, ...}` | required |
| `auth_backend` | Proxmox auth realm: `pve` or `pam` | `pve` |
| `auth_totp` | Show TOTP 2FA entry field on login | `false` |
| `tls_verify` | Verify TLS certificate when connecting to Proxmox | `false` |
| `user` | Username for API token auto-login (e.g. `user@pve`) | — |
| `token_name` | API token name | — |
| `token_value` | API token value (secret) | — |
| `pwresetcmd` | Full command to launch a password reset tool | — |
| `auto_vmid` | Automatically connect to this VMID after login | — |
| `knock_seq` | Port knock sequence as a JSON array (e.g. `[1234, 5678]`) | — |

When `user`, `token_name`, and `token_value` are all set **and only one cluster is defined**,
the client auto-authenticates on startup without prompting for credentials.

### `[SpiceProxyRedirect]`

Rewrites the SPICE proxy address returned by Proxmox. Useful when the Proxmox node is behind NAT or a reverse proxy.

```ini
[SpiceProxyRedirect]
# pve1.example.com:3128 = <public-IP>:<public-port>
pve1.example.com:3128 = 123.123.123.123:6000
```

Use `inidebug = True` in `[General]` to log the proxy address returned by Proxmox so you know what to rewrite.

### `[AdditionalParameters]`

Passes extra key-value options directly to `virt-viewer` / `remote-viewer`. See the
[remote-viewer man page](https://www.mankier.com/1/remote-viewer) for available parameters.

```ini
[AdditionalParameters]
enable-usbredir = true
enable-usb-autoshare = true
```

If you encounter any issues feel free to submit an issue report.

## Proxmox Permission Requirements

Users that are accessing VDI instances need to have the following permissions assigned for each VM they access:

- VM.PowerMgmt
- VM.Console
- VM.Audit

## Command Line Usage

No command line options are required for default behavior. The following command line options are available:

```text
usage: vdiclient.py [-h] [--config_type {file,http}] [--config_location CONFIG_LOCATION]
                    [--config_username CONFIG_USERNAME] [--config_password CONFIG_PASSWORD]
                    [--ignore_ssl] [--port PORT] [--host HOST] [--no-browser]
                    [--log-level LOG_LEVEL]

Proxmox VDI Client

options:
  -h, --help            show this help message and exit
  --config_type {file,http}
                        Config source type (default: file)
  --config_location CONFIG_LOCATION
                        Config file path or HTTP URL
  --config_username CONFIG_USERNAME
                        HTTP basic auth username
  --config_password CONFIG_PASSWORD
                        HTTP basic auth password
  --ignore_ssl          Ignore SSL certificate errors for config download
  --port PORT           Web server port (default: 5000)
  --host HOST           Web server bind address (default: 127.0.0.1)
  --no-browser          Do not auto-open browser on start
  --log-level LOG_LEVEL
                        Log level: DEBUG, INFO, WARNING, ERROR (default: INFO)
```

If `--config_type http` is selected, pass the URL in the `--config_location` parameter.

The `LOG_LEVEL` environment variable sets the log level as a fallback when `--log-level` is not
provided (e.g. `LOG_LEVEL=DEBUG vdiclient.py`). The `log_level` key in the `[General]` config
section is applied last, only if neither the CLI flag nor the environment variable is set.

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
