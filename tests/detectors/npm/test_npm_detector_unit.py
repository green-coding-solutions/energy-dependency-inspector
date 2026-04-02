"""Unit tests for npm detector metadata."""

from typing import Optional

from energy_dependency_inspector.detectors.npm_detector import NpmDetector


class FakeExecutor:
    """Minimal executor stub for npm detector unit tests."""

    def __init__(self, command_results: dict[str, tuple[str, str, int]], paths: set[str]):
        self.command_results = command_results
        self.paths = paths

    def execute_command(self, command: str, working_dir: Optional[str] = None) -> tuple[str, str, int]:
        return self.command_results.get(command, ("", "", 1))

    def path_exists(self, path: str) -> bool:
        return path in self.paths


def test_npm_single_location_includes_node_version() -> None:
    detector = NpmDetector()
    executor = FakeExecutor(
        command_results={
            "node --version": ("v22.11.0\n", "", 0),
            "cd '/app' && pwd": ("/app\n", "", 0),
            "find '/app' -type d -name 'node_modules' -print 2>/dev/null | LC_COLLATE=C sort -u": (
                "/app/node_modules\n",
                "",
                0,
            ),
            "npm list --json --depth=0": (
                '{"dependencies":{"typescript":{"version":"5.6.3"},"jest":{"version":"29.7.0"}}}',
                "",
                0,
            ),
            "npm list -g --json --depth=0": ("{}", "", 0),
            "cd '/app/node_modules' && find . -name 'node_modules/.cache' -prune -o -name '*.log' -prune -o -name '.npm' -prune -o -not -name '*.tmp' -not -name '*.temp' \\( -type f -o -type l \\) -printf '%s %p %l\\n' | LC_COLLATE=C sort -n -k1,1 -k2,2": (
                "12 ./package.json \n",
                "",
                0,
            ),
        },
        paths={"/app/package.json"},
    )

    result = detector.get_dependencies(executor, working_dir="/app")

    assert result["scope"] == "project"
    assert result["node_version"] == "v22.11.0"
    assert result["location"] == "/app/node_modules"


def test_npm_mixed_location_includes_node_version() -> None:
    detector = NpmDetector()
    executor = FakeExecutor(
        command_results={
            "node --version": ("v20.18.1\n", "", 0),
            "cd '/workspace' && pwd": ("/workspace\n", "", 0),
            "find '/workspace' -type d -name 'node_modules' -print 2>/dev/null | LC_COLLATE=C sort -u": (
                "/workspace/api/node_modules\n/workspace/web/node_modules\n",
                "",
                0,
            ),
            "npm list --json --depth=0": ('{"dependencies":{"jest":{"version":"29.7.0"}}}', "", 0),
            "npm list -g --json --depth=0": ('{"dependencies":{"npm":{"version":"10.8.2"}}}', "", 0),
            "cd '/workspace/api/node_modules' && find . -name 'node_modules/.cache' -prune -o -name '*.log' -prune -o -name '.npm' -prune -o -not -name '*.tmp' -not -name '*.temp' \\( -type f -o -type l \\) -printf '%s %p %l\\n' | LC_COLLATE=C sort -n -k1,1 -k2,2": (
                "12 ./package.json \n",
                "",
                0,
            ),
            "cd '/workspace/web/node_modules' && find . -name 'node_modules/.cache' -prune -o -name '*.log' -prune -o -name '.npm' -prune -o -not -name '*.tmp' -not -name '*.temp' \\( -type f -o -type l \\) -printf '%s %p %l\\n' | LC_COLLATE=C sort -n -k1,1 -k2,2": (
                "14 ./package.json \n",
                "",
                0,
            ),
            "npm config get prefix": ("/usr/local\n", "", 0),
            "cd '/usr/local/lib/node_modules' && find . -name 'node_modules/.cache' -prune -o -name '*.log' -prune -o -name '.npm' -prune -o -not -name '*.tmp' -not -name '*.temp' \\( -type f -o -type l \\) -printf '%s %p %l\\n' | LC_COLLATE=C sort -n -k1,1 -k2,2": (
                "20 ./npm/package.json \n",
                "",
                0,
            ),
        },
        paths={"/workspace/api/package.json", "/workspace/web/package.json"},
    )

    result = detector.get_dependencies(executor, working_dir="/workspace")

    assert result["scope"] == "mixed"
    assert result["node_version"] == "v20.18.1"
    assert "/workspace/api/node_modules" in result["locations"]
    assert "/workspace/web/node_modules" in result["locations"]
