"""Test npm Docker container dependency detection."""

import os
import sys
from typing import Dict, Any

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import pytest

from energy_dependency_inspector.executors import DockerExecutor
from energy_dependency_inspector.core.orchestrator import Orchestrator
from tests.common.docker_test_base import DockerTestBase

try:
    import docker
except ImportError:
    docker = None  # type: ignore


class TestNpmDockerDetection(DockerTestBase):
    """Test npm dependency detection using Docker container environment."""

    IF_DOCKER_IMAGE = "ghcr.io/green-software-foundation/if"
    PLAYWRIGHT_DOCKER_IMAGE = "mcr.microsoft.com/playwright:v1.55.0-noble"

    @pytest.mark.skipif(docker is None, reason="Docker not available")
    def test_npm_docker_container_detection(self, request: pytest.FixtureRequest) -> None:
        """Test npm dependency detection inside a Docker container."""

        verbose_output = self.setup_verbose_output(request)
        container_id = None

        try:
            container_id = self.start_container(self.IF_DOCKER_IMAGE, additional_args=[])
            self.wait_for_container_ready(container_id, "npm --version", max_wait=60)

            executor = DockerExecutor(container_id)
            orchestrator = Orchestrator(debug=False, selected_detectors="npm")

            result = orchestrator.resolve_dependencies(executor)

            if verbose_output:
                self.print_verbose_results("ENERGY DEPENDENCY INSPECTOR OUTPUT:", result)

            self._validate_npm_dependencies(result)

        finally:
            if container_id:
                self.cleanup_container(container_id)

    def _validate_npm_dependencies(self, result: Dict[str, Any]) -> None:
        """Validate that npm dependencies were detected correctly."""
        self.validate_basic_structure(result, "npm")

        npm_result = result["npm"]
        scope = npm_result["scope"]

        # Handle both simple and mixed structures
        if scope == "mixed":
            # Mixed structure - validate locations
            assert "locations" in npm_result, "Mixed scope should have locations field"
            locations = npm_result["locations"]
            assert len(locations) > 0, "Mixed scope should have at least one location"

            # Find project location (should have the main dependencies)
            project_location = None
            for location, location_data in locations.items():
                if location_data["scope"] == "project":
                    project_location = location_data
                    break

            assert project_location is not None, "Expected to find project location in mixed scope"
            dependencies = project_location["dependencies"]

            print(f"✓ Mixed scope detected with {len(locations)} locations")
            for location, location_data in locations.items():
                dep_count = len(location_data["dependencies"])
                print(f"  - {location_data['scope']}: {location} ({dep_count} packages)")
        else:
            # Simple structure
            dependencies = npm_result["dependencies"]
            assert scope == "project", f"Scope should be 'project', got: {scope}"

            assert "location" in npm_result, "npm result should have location field"
            location = npm_result["location"]
            assert isinstance(location, str), "Location should be a string"
            assert len(location) > 0, "Location should not be empty"

            if "hash" in npm_result:
                hash_value = npm_result["hash"]
                assert isinstance(hash_value, str), "Hash should be a string"

            print(f"✓ Scope: {scope}")
            print(f"✓ Location: {location}")

        # Validate project dependencies
        dependency_names = list(dependencies.keys())
        assert len(dependency_names) > 5, f"Expected to find multiple npm dependencies, got: {dependency_names}"

        # Check for typical Node.js/TypeScript project dependencies
        typescript_related = any(
            name
            for name in dependency_names
            if any(keyword in name.lower() for keyword in ["typescript", "@types", "ts-", "jest"])
        )
        assert typescript_related, f"Expected to find TypeScript-related dependencies in: {dependency_names}"

        # Validate dependency structure
        self.validate_dependency_structure(dependencies, sample_count=3)

        print(f"✓ Successfully detected {len(dependencies)} project npm dependencies")

    @pytest.mark.skipif(docker is None, reason="Docker not available")
    def test_npm_playwright_global_detection(self, request: pytest.FixtureRequest) -> None:
        """Test npm dependency detection for globally installed packages (Playwright image)."""

        verbose_output = self.setup_verbose_output(request)
        container_id = None

        try:
            container_id = self.start_container(self.PLAYWRIGHT_DOCKER_IMAGE, additional_args=[])
            self.wait_for_container_ready(container_id, "npm list -g --json --depth=0", max_wait=60)

            executor = DockerExecutor(container_id)
            orchestrator = Orchestrator(debug=False, selected_detectors="npm")

            result = orchestrator.resolve_dependencies(executor)

            if verbose_output:
                self.print_verbose_results("ENERGY DEPENDENCY INSPECTOR OUTPUT:", result)

            self._validate_npm_global_dependencies(result)

        finally:
            if container_id:
                self.cleanup_container(container_id)

    def _validate_npm_global_dependencies(self, result: Dict[str, Any]) -> None:
        """Validate that globally installed npm dependencies were detected correctly."""
        self.validate_basic_structure(result, "npm")

        npm_result = result["npm"]
        dependencies = npm_result["dependencies"]

        dependency_names = list(dependencies.keys())

        # Playwright image has globally installed packages (npm, yarn, corepack)
        assert len(dependency_names) >= 2, f"Expected to find global npm dependencies, got: {dependency_names}"

        # Check for npm-related packages (npm, yarn, corepack are in Playwright image)
        npm_related = any(name in ["npm", "yarn", "corepack"] for name in dependency_names)
        assert npm_related, f"Expected to find npm/yarn/corepack in: {dependency_names}"

        # Validate dependency structure
        self.validate_dependency_structure(dependencies, sample_count=min(3, len(dependencies)))

        scope = npm_result["scope"]
        assert scope == "system", f"Scope should be 'system', got: {scope}"

        assert "location" in npm_result, "npm result should have location field"
        location = npm_result["location"]
        assert isinstance(location, str), "Location should be a string"
        assert len(location) > 0, "Location should not be empty"
        assert "node_modules" in location, f"Location should contain 'node_modules', got: {location}"

        print(f"✓ Successfully detected {len(dependencies)} global npm dependencies")
        print(f"✓ Scope: {scope}")
        print(f"✓ Location: {location}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
