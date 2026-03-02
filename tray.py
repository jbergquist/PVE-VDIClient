"""
System tray icon for the VDI client.

Owns the main thread via pystray.Icon.run().  Falls back to a blocking
Event.wait() when running headless (no DISPLAY / WAYLAND_DISPLAY).
"""

import os
import sys
import time
import threading
import webbrowser

# ---------------------------------------------------------------------------
# State helpers
# ---------------------------------------------------------------------------


def compute_state() -> str:
    """Return 'running', 'warning', or 'error' based on G state."""
    try:
        from vdiclient import G
    except ImportError:
        return 'error'

    if G.server_shutdown_timeout > 0 and G.server_start_time is not None:
        elapsed = time.time() - G.server_start_time
        remaining = G.server_shutdown_timeout - elapsed
        if remaining <= 300:  # amber within last 5 minutes
            return 'warning'

    return 'running'


def build_tooltip() -> str:
    """Build a human-readable tooltip string."""
    try:
        from vdiclient import G
    except ImportError:
        return 'VDI Client'

    parts = ['PVE VDI Client']

    if G.authenticated:
        parts.append('Session: active')
    else:
        parts.append('Session: not logged in')

    if G.server_shutdown_timeout > 0 and G.server_start_time is not None:
        elapsed = time.time() - G.server_start_time
        remaining = max(0, G.server_shutdown_timeout - elapsed)
        mins = int(remaining // 60)
        secs = int(remaining % 60)
        parts.append(f'Shutdown in: {mins}m {secs}s')

    return '\n'.join(parts)


# ---------------------------------------------------------------------------
# Icon image builder
# ---------------------------------------------------------------------------

def _build_icon_image(state: str):
    """Return a PIL.Image for the given state (running/warning/error)."""
    try:
        from PIL import Image, ImageDraw
    except ImportError:
        return None

    icon_path = os.path.join(os.path.dirname(__file__), 'static', 'vdiclient.png')

    if os.path.exists(icon_path):
        try:
            base = Image.open(icon_path).convert('RGBA').resize((64, 64), Image.LANCZOS)
        except Exception:
            base = Image.new('RGBA', (64, 64), (60, 60, 60, 255))
    else:
        base = Image.new('RGBA', (64, 64), (60, 60, 60, 255))

    dot_colors = {
        'running': '#22c55e',
        'warning': '#f59e0b',
        'error':   '#ef4444',
    }
    color = dot_colors.get(state, '#ef4444')

    draw = ImageDraw.Draw(base)
    # 12×12 dot, bottom-right corner with 2 px margin
    x0, y0 = 64 - 12 - 2, 64 - 12 - 2
    draw.ellipse([x0, y0, x0 + 12, y0 + 12], fill=color)

    return base


# ---------------------------------------------------------------------------
# Menu actions
# ---------------------------------------------------------------------------

def _open_browser(icon, item):
    try:
        from vdiclient import G
        webbrowser.open(G.server_url)
    except Exception:
        pass


def _reload_config(icon, item):
    try:
        from vdiclient import G, loadconfig
        loadconfig(
            config_location=G._config_location,
            config_type=G._config_type,
            config_username=G._config_username,
            config_password=G._config_password,
            ssl_verify=G._ssl_verify,
        )
        # Reset auth state so user has to log in again
        G.authenticated = False
        G.proxmox = None
        G.last_activity_time = None
        print('Config reloaded from tray.')
    except Exception as e:
        print(f'Tray: reload config failed: {e}')


def _restart(icon, item):
    icon.stop()
    os.execv(sys.executable, [sys.executable] + sys.argv)


def _shutdown(icon, item):
    icon.stop()
    os._exit(0)


# ---------------------------------------------------------------------------
# Status update thread
# ---------------------------------------------------------------------------

def _start_status_thread(icon):
    def _loop():
        while True:
            time.sleep(10)
            try:
                state = compute_state()
                img = _build_icon_image(state)
                if img is not None:
                    icon.icon = img
                icon.title = build_tooltip()
            except Exception:
                pass

    t = threading.Thread(target=_loop, daemon=True)
    t.start()


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def _block() -> None:
    """Block the main thread indefinitely. KeyboardInterrupt propagates to caller."""
    threading.Event().wait()


def run_tray(server_url: str) -> None:
    """
    Start the system tray icon.  Blocks until the user quits.

    Falls back to _block() when no display is available so the Flask
    daemon threads keep running.
    """
    # Headless check
    has_display = bool(
        os.environ.get('DISPLAY') or os.environ.get('WAYLAND_DISPLAY')
    )
    if not has_display:
        print('Warning: No display detected. Running headless (tray disabled).')
        _block()
        return

    # On pure Wayland (no X socket) pystray's xorg backend crashes at import time.
    # Force the appindicator backend (libayatana-appindicator / StatusNotifierItem).
    # setdefault respects any PYSTRAY_BACKEND the user has already set manually.
    if os.environ.get('WAYLAND_DISPLAY') and not os.environ.get('DISPLAY'):
        os.environ.setdefault('PYSTRAY_BACKEND', 'appindicator')

    # Import optional deps with graceful fallback.
    # Catch Exception broadly: pystray raises Xlib.error.DisplayNameError at
    # import time on Wayland (no X display), which is not an ImportError.
    try:
        import pystray
        from PIL import Image  # noqa: F401 — confirm Pillow is available
    except ImportError as exc:
        print(f'Warning: Tray disabled — missing dependency: {exc}')
        if os.environ.get('WAYLAND_DISPLAY') and not os.environ.get('DISPLAY'):
            print('  Wayland tray requires PyGObject and appindicator:')
            print('  pip install PyGObject')
            print('  Fedora:  sudo dnf install libayatana-appindicator')
            print('  Debian:  sudo apt install libayatana-appindicator3-1')
        else:
            print('Install with: pip install pystray Pillow')
        _block()
        return
    except Exception as exc:
        print(f'Warning: Tray disabled — backend initialisation failed: {exc}')
        if os.environ.get('WAYLAND_DISPLAY'):
            print('  Wayland tray requires libayatana-appindicator.')
            print('  On Fedora: sudo dnf install libayatana-appindicator')
            print('  On Debian/Ubuntu: sudo apt install libayatana-appindicator3-1')
        _block()
        return

    initial_img = _build_icon_image(compute_state()) or Image.new('RGBA', (64, 64), (60, 60, 60, 255))

    menu = pystray.Menu(
        pystray.MenuItem('Open VDI Client', _open_browser, default=True),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem('Reload Config', _reload_config),
        pystray.MenuItem('Restart', _restart),
        pystray.MenuItem('Shutdown', _shutdown),
    )

    icon = pystray.Icon(
        name='vdiclient',
        icon=initial_img,
        title=build_tooltip(),
        menu=menu,
    )

    # Store reference so other code can reach it
    try:
        from vdiclient import G
        G.tray_icon = icon
        G.tray_enabled = True
    except ImportError:
        pass

    _start_status_thread(icon)
    icon.run()
