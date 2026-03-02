#
# Copyright 2024-2026 jbergquist
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# MODIFICATIONS:
# - 2026: Added get_ssl_directory() for SSL certificate storage (commit cf999ac)
"""Platform abstraction layer for VDI Client.

Provides safe, cross-platform detection and path resolution.
Eliminates hardcoded os.name checks and shell injection vulnerabilities.
"""

import os
import sys
import shutil
from typing import List


class Platform:
    """Platform-specific functionality abstraction."""

    @staticmethod
    def is_windows() -> bool:
        """Check if running on Windows."""
        return sys.platform == "win32"

    @staticmethod
    def is_posix() -> bool:
        """Check if running on POSIX (Linux, macOS, BSD, etc)."""
        return os.name == "posix"

    @staticmethod
    def get_config_search_paths() -> List[str]:
        """Get platform-specific config file search paths.

        Returns list of paths in priority order (first found wins).
        Follows XDG Base Directory specification on POSIX systems.

        Returns:
            List of config file paths to search
        """
        if Platform.is_windows():
            # Windows: APPDATA, Program Files locations
            appdata = os.getenv("APPDATA", "")
            programfiles = os.getenv("PROGRAMFILES", "C:\\Program Files")
            programfiles_x86 = os.getenv("PROGRAMFILES(X86)", "C:\\Program Files (x86)")

            return [
                os.path.join(appdata, "VDIClient", "vdiclient.ini"),
                os.path.join(programfiles, "VDIClient", "vdiclient.ini"),
                os.path.join(programfiles_x86, "VDIClient", "vdiclient.ini"),
                "C:\\Program Files\\VDIClient\\vdiclient.ini",
            ]
        elif Platform.is_posix():
            # POSIX: XDG config home, system config directories
            xdg_config_home = os.getenv(
                "XDG_CONFIG_HOME", os.path.expanduser("~/.config")
            )

            return [
                os.path.join(xdg_config_home, "VDIClient", "vdiclient.ini"),
                "/etc/vdiclient/vdiclient.ini",
                "/usr/local/etc/vdiclient/vdiclient.ini",
            ]
        else:
            # Unknown platform
            return []

    @staticmethod
    def _flatpak_host_has(cmd: str) -> bool:
        """Return True if *cmd* is found on the host via flatpak-spawn."""
        import subprocess
        try:
            subprocess.check_call(
                ["flatpak-spawn", "--host", "which", cmd],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False

    @staticmethod
    def _flatpak_app_installed(app_id: str) -> bool:
        """Return True if the given Flatpak app is installed on the host."""
        import subprocess
        try:
            result = subprocess.check_output(
                ["flatpak-spawn", "--host", "flatpak", "list", "--app", "--columns=application"],
                stderr=subprocess.DEVNULL,
                text=True,
            )
            return app_id in result
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False

    @staticmethod
    def find_virt_viewer() -> List[str]:
        """Locate virt-viewer/remote-viewer binary safely.

        Uses platform-appropriate discovery:
        - Windows: Registry lookup via ftype command
        - POSIX (Flatpak): flatpak-spawn --host, preferring host binary,
          falling back to the org.virt_manager.virt-viewer Flatpak
        - POSIX (native): shutil.which() for remote-viewer or virt-viewer

        Returns:
            Command list to launch virt-viewer (may be multi-element)

        Raises:
            RuntimeError: If virt-viewer is not found
        """
        if Platform.is_windows():
            # Windows: Query file type association for .vvfile
            try:
                import subprocess

                result = subprocess.check_output(
                    ["cmd", "/c", "ftype", "VirtViewer.vvfile"],
                    stderr=subprocess.DEVNULL,
                    text=True,
                )

                # Parse: VirtViewer.vvfile="C:\Path\remote-viewer.exe" "%1"
                if "=" in result:
                    cmdline = result.split("=", 1)[1].strip()
                    if cmdline.startswith('"'):
                        end_quote = cmdline.index('"', 1)
                        vv_path = cmdline[1:end_quote]
                        if os.path.isfile(vv_path):
                            return [vv_path]

                raise RuntimeError("virt-viewer not properly registered")

            except (subprocess.CalledProcessError, ValueError, OSError) as e:
                raise RuntimeError(
                    "virt-viewer not found. Install from: "
                    "https://www.spice-space.org/download/"
                ) from e

        elif Platform.is_posix():
            # Inside a Flatpak sandbox host binaries are not on PATH.
            # Use flatpak-spawn --host to reach the host or another Flatpak.
            if os.path.exists("/.flatpak-info"):
                for name in ("remote-viewer", "virt-viewer"):
                    if Platform._flatpak_host_has(name):
                        return ["flatpak-spawn", "--host", name]
                if Platform._flatpak_app_installed("org.virt_manager.virt-viewer"):
                    return ["flatpak-spawn", "--host", "flatpak", "run",
                            "org.virt_manager.virt-viewer"]
                raise RuntimeError(
                    "virt-viewer not found on host.\n"
                    "  Fedora/RHEL:   sudo dnf install virt-viewer\n"
                    "  Debian/Ubuntu: sudo apt install virt-viewer\n"
                    "  Flatpak:       flatpak install flathub org.virt_manager.virt-viewer"
                )

            # Native POSIX: try both names provided by the virt-viewer package
            for name in ("remote-viewer", "virt-viewer"):
                vv_path = shutil.which(name)
                if vv_path:
                    return [vv_path]

            raise RuntimeError(
                "virt-viewer not found. Install with:\n"
                "  Debian/Ubuntu: apt install virt-viewer\n"
                "  Fedora/RHEL:   dnf install virt-viewer\n"
                "  Arch:          pacman -S virt-viewer"
            )

        else:
            raise RuntimeError(f"Unsupported platform: {sys.platform}")

    @staticmethod
    def get_ssl_directory() -> str:
        """Get platform-specific directory for SSL certificates.

        Returns XDG-compliant paths on POSIX, APPDATA on Windows.
        Creates directory if it doesn't exist.

        Returns:
            Path to SSL certificate storage directory
        """
        if Platform.is_windows():
            appdata = os.getenv("APPDATA", "")
            ssl_dir = os.path.join(appdata, "VDIClient", "ssl")
        elif Platform.is_posix():
            xdg_config_home = os.getenv(
                "XDG_CONFIG_HOME", os.path.expanduser("~/.config")
            )
            ssl_dir = os.path.join(xdg_config_home, "VDIClient", "ssl")
        else:
            # Fallback
            ssl_dir = os.path.join(os.path.expanduser("~"), ".vdiclient", "ssl")

        # Create directory if it doesn't exist
        os.makedirs(ssl_dir, mode=0o700, exist_ok=True)
        return ssl_dir
