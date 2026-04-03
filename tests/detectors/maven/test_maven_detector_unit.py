"""Unit tests for recursive Maven project discovery."""

from typing import Optional

from energy_dependency_inspector.detectors.maven_detector import MavenDetector


class FakeExecutor:
    """Minimal executor stub for Maven detector unit tests."""

    def __init__(self, command_results: dict[str, tuple[str, str, int]], paths: set[str]):
        self.command_results = command_results
        self.paths = paths

    def execute_command(self, command: str, working_dir: Optional[str] = None) -> tuple[str, str, int]:
        return self.command_results.get(command, ("", "", 1))

    def path_exists(self, path: str) -> bool:
        return path in self.paths


def test_maven_recursive_scan_returns_mixed_for_multiple_projects() -> None:
    detector = MavenDetector()
    executor = FakeExecutor(command_results={}, paths=set())

    detector._find_project_directories = lambda executor, working_dir=None: ["/workspace/api", "/workspace/web"]  # type: ignore[method-assign]
    detector._maven_available = lambda executor, working_dir=None: True  # type: ignore[method-assign]

    def fake_get_dependencies_via_maven(executor: FakeExecutor, working_dir: Optional[str] = None) -> dict[str, dict[str, str]]:
        if working_dir == "/workspace/api":
            return {"com.fasterxml.jackson.core:jackson-core": {"version": "2.15.2"}}
        return {"org.apache.commons:commons-lang3": {"version": "3.12.0"}}

    detector._get_dependencies_via_maven = fake_get_dependencies_via_maven  # type: ignore[method-assign]
    detector._generate_location_hash = lambda executor, location: f"hash:{location}"  # type: ignore[method-assign]

    result = detector.get_dependencies(executor, working_dir="/workspace")

    assert result["scope"] == "mixed"
    assert "/workspace/api" in result["locations"]
    assert "/workspace/web" in result["locations"]
    assert result["locations"]["/workspace/api"]["dependencies"]["com.fasterxml.jackson.core:jackson-core"]["version"] == "2.15.2"
    assert result["locations"]["/workspace/web"]["dependencies"]["org.apache.commons:commons-lang3"]["version"] == "3.12.0"
