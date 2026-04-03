"""Unit tests for PECL detector behavior."""

from typing import Optional

from energy_dependency_inspector.detectors.pecl_detector import PeclDetector


class FakeExecutor:
    """Minimal executor stub for PECL detector unit tests."""

    def __init__(self, command_results: dict[str, tuple[str, str, int]]):
        self.command_results = command_results

    def execute_command(self, command: str, working_dir: Optional[str] = None) -> tuple[str, str, int]:
        return self.command_results.get(command, ("", "", 1))

    def path_exists(self, path: str) -> bool:
        del path
        return False


def test_pecl_detector_parses_extensions_and_php_version() -> None:
    detector = PeclDetector()
    executor = FakeExecutor(
        {
            "php --version": ("PHP 8.3.7 (cli) (built: Mar 12 2026 10:00:00) (NTS)\n", "", 0),
            "pecl list": (
                "Installed packages, channel pecl.php.net:\n"
                "=========================================\n"
                "Package Version State\n"
                "apcu    5.1.24  stable\n"
                "xdebug  3.3.2   stable\n",
                "",
                0,
            ),
        }
    )

    result = detector.get_dependencies(executor)

    assert result["scope"] == "system"
    assert result["php_version"] == "PHP 8.3.7 (cli) (built: Mar 12 2026 10:00:00) (NTS)"
    assert result["dependencies"]["apcu"]["version"] == "5.1.24"
    assert result["dependencies"]["xdebug"]["version"] == "3.3.2"
    assert "Installed" not in result["dependencies"]
    assert "Package" not in result["dependencies"]


def test_pecl_detector_returns_empty_dependencies_on_failure() -> None:
    detector = PeclDetector()
    executor = FakeExecutor({"php --version": ("PHP 8.2.15 (cli)\n", "", 0), "pecl list": ("", "not found", 1)})

    result = detector.get_dependencies(executor)

    assert result == {"scope": "system", "php_version": "PHP 8.2.15 (cli)", "dependencies": {}}
