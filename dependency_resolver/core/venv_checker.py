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
            "Dependency Resolver requires Python 3.10 at least. "
            "Please upgrade your Python version."
        )
        sys.exit(1)

    # Calculate expected venv path (resolve symlinks for consistent comparison)
    current_file = os.path.realpath(__file__)
    current_dir = os.path.dirname(current_file)
    expected_venv = os.path.realpath(os.path.join(current_dir, "..", "..", "venv"))
    actual_venv = os.path.realpath(sys.prefix)

    if actual_venv != expected_venv:
        print(
            f"Error:\n\n"
            f"You are not using a venv, or venv is not in expected directory {expected_venv}\n"
            f"Current venv is in {sys.prefix}\n\n"
            f"The Dependency Resolver needs a venv to correctly find installed packages "
            f"and also necessary include paths.\n"
            f"Please check the installation instructions.\n\n"
            f"Maybe you just forgot to activate your venv? Try:\n"
            f"$ source venv/bin/activate"
        )
        sys.exit(1)
