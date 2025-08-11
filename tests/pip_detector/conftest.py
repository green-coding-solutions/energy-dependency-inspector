"""Pytest configuration for Django Docker compose tests."""

from _pytest.config.argparsing import Parser


def pytest_addoption(parser: Parser) -> None:
    """Add custom pytest command-line options."""
    parser.addoption(
        "--verbose-resolver",
        action="store_true",
        default=False,
        help="Print dependency resolver output during test execution",
    )
