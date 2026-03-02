"""Entry point for python -m vdiclient and console script."""

import sys
from vdiclient.app import main

if __name__ == "__main__":
    sys.exit(main())
