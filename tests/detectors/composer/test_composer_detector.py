"""Unit tests for Composer detector behavior."""

from typing import Optional

from energy_dependency_inspector.detectors.composer_detector import ComposerDetector


class FakeExecutor:
    """Minimal executor stub for detector unit tests."""

    def __init__(self, command_results: dict[str, tuple[str, str, int]], paths: set[str]):
        self.command_results = command_results
        self.paths = paths

    def execute_command(self, command: str, working_dir: Optional[str] = None) -> tuple[str, str, int]:
        return self.command_results.get(command, ("", "", 1))

    def path_exists(self, path: str) -> bool:
        return path in self.paths


def test_composer_project_detection() -> None:
    detector = ComposerDetector()
    executor = FakeExecutor(
        command_results={
            "php --version": ("PHP 8.3.7 (cli) (built: Mar 12 2026 10:00:00) (NTS)\n", "", 0),
            "cd '/app' && pwd": ("/app\n", "", 0),
            "find '/app' -path '*/vendor/*' -prune -o -name 'composer.json' -type f -print | sed 's|/composer.json$||' | LC_COLLATE=C sort -u": (
                "/app\n",
                "",
                0,
            ),
            "composer show --direct --format=json --no-interaction": (
                '{"installed":[{"name":"monolog/monolog","version":"3.5.0"},{"name":"psr/log","pretty_version":"3.0.0"}]}',
                "",
                0,
            ),
            "composer config vendor-dir --absolute": ("/app/vendor\n", "", 0),
            "cd '/app/vendor' && find . -name '.git' -prune -o -name '.composer' -prune -o -name '*.log' -prune -o -not -name '*.tmp' -not -name '*.temp' \\( -type f -o -type l \\) -printf '%s %p %l\\n' | LC_COLLATE=C sort -n -k1,1 -k2,2": (
                "12 ./composer/installed.json \n",
                "",
                0,
            ),
        },
        paths=set(),
    )

    result = detector.get_dependencies(executor, working_dir="/app")

    assert result["scope"] == "project"
    assert result["php_version"] == "PHP 8.3.7 (cli) (built: Mar 12 2026 10:00:00) (NTS)"
    assert result["location"] == "/app/vendor"
    assert "hash" in result
    assert result["dependencies"]["monolog/monolog"]["version"] == "3.5.0"
    assert result["dependencies"]["psr/log"]["version"] == "3.0.0"


def test_composer_global_detection() -> None:
    detector = ComposerDetector()
    executor = FakeExecutor(
        command_results={
            "php --version": ("PHP 8.2.15 (cli) (built: Jan 10 2026 08:00:00) (NTS)\n", "", 0),
            "composer global show --direct --format=json --no-interaction": (
                '{"installed":[{"name":"phpunit/phpunit","version":"10.5.0"}]}',
                "",
                0,
            ),
            "composer global config vendor-dir --absolute": ("/root/.config/composer/vendor\n", "", 0),
            "cd '/root/.config/composer/vendor' && find . -name '.git' -prune -o -name '.composer' -prune -o -name '*.log' -prune -o -not -name '*.tmp' -not -name '*.temp' \\( -type f -o -type l \\) -printf '%s %p %l\\n' | LC_COLLATE=C sort -n -k1,1 -k2,2": (
                "24 ./autoload.php \n",
                "",
                0,
            ),
        },
        paths=set(),
    )

    result = detector.get_dependencies(executor)

    assert result["scope"] == "system"
    assert result["php_version"] == "PHP 8.2.15 (cli) (built: Jan 10 2026 08:00:00) (NTS)"
    assert result["location"] == "/root/.config/composer/vendor"
    assert result["dependencies"]["phpunit/phpunit"]["version"] == "10.5.0"


def test_composer_mixed_detection() -> None:
    detector = ComposerDetector()
    executor = FakeExecutor(
        command_results={
            "php --version": ("PHP 8.4.1 (cli) (built: Feb 01 2026 12:00:00) (NTS)\n", "", 0),
            "cd '/srv' && pwd": ("/srv\n", "", 0),
            "find '/srv' -path '*/vendor/*' -prune -o -name 'composer.json' -type f -print | sed 's|/composer.json$||' | LC_COLLATE=C sort -u": (
                "/srv/api\n/srv/app\n",
                "",
                0,
            ),
            "composer show --direct --format=json --no-interaction": ('{"installed":[{"name":"placeholder/package","version":"1.0.0"}]}', "", 0),
            "composer config vendor-dir --absolute": ("/srv/api/vendor\n", "", 0),
            "cd '/srv/api/vendor' && find . -name '.git' -prune -o -name '.composer' -prune -o -name '*.log' -prune -o -not -name '*.tmp' -not -name '*.temp' \\( -type f -o -type l \\) -printf '%s %p %l\\n' | LC_COLLATE=C sort -n -k1,1 -k2,2": (
                "16 ./autoload.php \n",
                "",
                0,
            ),
            "cd '/srv/app/vendor' && find . -name '.git' -prune -o -name '.composer' -prune -o -name '*.log' -prune -o -not -name '*.tmp' -not -name '*.temp' \\( -type f -o -type l \\) -printf '%s %p %l\\n' | LC_COLLATE=C sort -n -k1,1 -k2,2": (
                "18 ./autoload.php \n",
                "",
                0,
            ),
            "composer global show --direct --format=json --no-interaction": (
                '{"installed":[{"name":"psy/psysh","version":"0.12.0"}]}',
                "",
                0,
            ),
            "composer global config vendor-dir --absolute": ("/root/.config/composer/vendor\n", "", 0),
            "cd '/root/.config/composer/vendor' && find . -name '.git' -prune -o -name '.composer' -prune -o -name '*.log' -prune -o -not -name '*.tmp' -not -name '*.temp' \\( -type f -o -type l \\) -printf '%s %p %l\\n' | LC_COLLATE=C sort -n -k1,1 -k2,2": (
                "24 ./autoload.php \n",
                "",
                0,
            ),
        },
        paths=set(),
    )

    original_get_project_location = detector._get_project_location
    original_parse_dependencies = detector._parse_dependencies

    def fake_get_project_location(_: FakeExecutor, project_dir: Optional[str] = None) -> str:
        return f"{project_dir}/vendor"

    call_count = {"count": 0}

    def fake_parse_dependencies(stdout: str) -> dict[str, dict[str, str]]:
        if stdout.startswith('{"installed":[{"name":"psy/psysh"'):
            return original_parse_dependencies(stdout)

        call_count["count"] += 1
        if call_count["count"] == 1:
            return {"laravel/framework": {"version": "11.0.0"}}
        return {"symfony/console": {"version": "7.1.0"}}

    detector._get_project_location = fake_get_project_location  # type: ignore[method-assign]
    detector._parse_dependencies = fake_parse_dependencies  # type: ignore[method-assign]

    result = detector.get_dependencies(executor, working_dir="/srv")

    assert result["scope"] == "mixed"
    assert result["php_version"] == "PHP 8.4.1 (cli) (built: Feb 01 2026 12:00:00) (NTS)"
    assert "/srv/api/vendor" in result["locations"]
    assert "/srv/app/vendor" in result["locations"]
    assert "/root/.config/composer/vendor" in result["locations"]
    assert result["locations"]["/srv/api/vendor"]["scope"] == "project"
    assert result["locations"]["/srv/app/vendor"]["scope"] == "project"
    assert result["locations"]["/root/.config/composer/vendor"]["scope"] == "system"

    detector._get_project_location = original_get_project_location  # type: ignore[method-assign]
    detector._parse_dependencies = original_parse_dependencies  # type: ignore[method-assign]


def test_composer_empty_result_uses_project_location() -> None:
    detector = ComposerDetector()
    executor = FakeExecutor(
        command_results={
            "php --version": ("PHP 8.1.30 (cli) (built: Dec 20 2025 09:00:00) (NTS)\n", "", 0),
            "cd '/workspace/php-app' && pwd": ("/workspace/php-app\n", "", 0),
            "find '/workspace/php-app' -path '*/vendor/*' -prune -o -name 'composer.json' -type f -print | sed 's|/composer.json$||' | LC_COLLATE=C sort -u": (
                "",
                "",
                0,
            ),
        },
        paths=set(),
    )

    result = detector.get_dependencies(executor, working_dir="/workspace/php-app")

    assert result == {
        "scope": "project",
        "location": "/workspace/php-app",
        "php_version": "PHP 8.1.30 (cli) (built: Dec 20 2025 09:00:00) (NTS)",
        "dependencies": {},
    }
