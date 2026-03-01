"""Platform abstraction layer for VDI Client.

Provides safe, cross-platform detection and path resolution.
Eliminates hardcoded os.name checks and shell injection vulnerabilities.
"""

import os
import sys
import shutil
from typing import List, Optional


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
    def find_virt_viewer() -> Optional[str]:
        """Locate virt-viewer/remote-viewer binary safely.

        Uses platform-appropriate discovery:
        - Windows: Registry lookup via ftype command (winreg in future)
        - POSIX: shutil.which() for remote-viewer

        Returns:
            Path to virt-viewer executable, or None if not found

        Raises:
            RuntimeError: If virt-viewer is not installed
        """
        vv_path: Optional[str] = None

        if Platform.is_windows():
            # Windows: Query file type association for .vvfile
            try:
                import subprocess

                # Use shell=False with list args for safety
                result = subprocess.check_output(
                    ["cmd", "/c", "ftype", "VirtViewer.vvfile"],
                    stderr=subprocess.DEVNULL,
                    text=True,
                )

                # Parse: VirtViewer.vvfile="C:\Path\remote-viewer.exe" "%1"
                if "=" in result:
                    cmdline = result.split("=", 1)[1].strip()
                    # Extract quoted path
                    if cmdline.startswith('"'):
                        end_quote = cmdline.index('"', 1)
                        vv_path = cmdline[1:end_quote]
                        if os.path.isfile(vv_path):
                            return vv_path

                raise RuntimeError("virt-viewer not properly registered")

            except (subprocess.CalledProcessError, ValueError, OSError) as e:
                raise RuntimeError(
                    "virt-viewer not found. Install from: "
                    "https://www.spice-space.org/download/"
                ) from e

        elif Platform.is_posix():
            # POSIX: Use shutil.which() for safe binary lookup
            vv_path = shutil.which("remote-viewer")
            if vv_path:
                return vv_path

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
