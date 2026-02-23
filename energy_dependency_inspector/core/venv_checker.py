import os
import sys


def check_venv() -> None:
    """
    Check if running in the correct virtual environment.

    Validates Python version and ensures the venv is in the expected location.
    Exits with code 1 if requirements are not met.
    """
    # Check Python version requirement
    if (sys.version_info.major, sys.version_info.minor) < (3, 10):
        print(
            "Python version is NOT greater than or equal to 3.10. "
            "energy-dependency-inspector requires Python 3.10 at least. "
            "Please upgrade your Python version."
        )
        sys.exit(1)
