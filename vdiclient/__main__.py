"""Entry point for python -m vdiclient and console script.

This allows running:
- python -m vdiclient
- vdiclient (after pip install)
"""

import sys
import os


def main():
    """Main entry point for the vdiclient command."""
    # Add parent directory to sys.path to import vdiclient.py
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)

    # Import the main vdiclient module (vdiclient.py at root)
    # Note: This imports from vdiclient.py, not from this package
    # pylint: disable=import-error,wrong-import-position
    import vdiclient as vdiclient_main  # noqa: E402

    # Run the main function from vdiclient.py
    return vdiclient_main.main()


if __name__ == "__main__":
    sys.exit(main())
