"""Pytest configuration for APK detector tests."""

from typing import Any


def pytest_addoption(parser: Any) -> None:
    """Add custom command line options."""
    parser.addoption(
        "--verbose-resolver", action="store_true", default=False, help="Enable verbose output for dependency resolver"
    )
