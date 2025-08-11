"""Pytest configuration for IF npm Docker tests."""

from typing import Any

import pytest


def pytest_addoption(parser: Any) -> None:
    """Add custom command-line options for pytest."""
    parser.addoption(
        "--verbose-resolver",
        action="store_true",
        default=False,
        help="Show verbose dependency resolver output during tests",
    )


@pytest.fixture
def verbose_resolver(request: Any) -> Any:
    """Fixture to access the --verbose-resolver option."""
    return request.config.getoption("--verbose-resolver")
