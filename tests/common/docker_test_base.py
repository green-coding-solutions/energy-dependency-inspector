"""Base class for Docker-based detector tests."""

import json
import time
from typing import Dict, Any, Optional

import pytest

try:
    import docker
except ImportError:
    docker = None  # type: ignore


class DockerTestBase:
    """Base class providing common functionality for Docker-based detector tests."""

    def setup_verbose_output(self, request: pytest.FixtureRequest) -> bool:
        """Get verbose output setting from pytest request."""
        return bool(request.config.getoption("--verbose-resolver", default=False))

    def start_container(
        self,
        image: str,
        sleep_duration: str = "300",
        additional_args: Optional[list] = None,
        env_vars: Optional[Dict[str, str]] = None,
    ) -> str:
        """Start Docker container and return its ID."""
        if docker is None:
            pytest.fail("Docker library not available")

        client = docker.from_env()

        # Prepare command
        if additional_args:
            command = additional_args
        else:
            command = ["sleep", sleep_duration]

        try:
            container = client.containers.run(
                image=image,
                command=command,
                environment=env_vars or {},
                detach=True,
                remove=True,
            )
            return str(container.id)
        except docker.errors.DockerException as e:
            pytest.fail(f"Failed to start container: {e}")
            return ""  # This line won't be reached due to pytest.fail, but satisfies mypy

    def wait_for_container_ready(self, container_id: str, health_check_cmd: str, max_wait: int = 30) -> None:
        """Wait for container to be ready using provided health check command."""
        if docker is None:
            pytest.fail("Docker library not available")

        client = docker.from_env()

        start_time = time.time()
        while time.time() - start_time < max_wait:
            try:
                container = client.containers.get(container_id)
                container.reload()

                if container.status == "running":
                    try:
                        # pylint: disable=import-outside-toplevel
                        from energy_dependency_inspector.executors import (
                            DockerExecutor,
                        )

                        executor = DockerExecutor(container_id)
                        _, _, exit_code = executor.execute_command(health_check_cmd)
                        if exit_code == 0:
                            return
                    except Exception:  # pylint: disable=broad-exception-caught
                        pass  # Continue waiting

                time.sleep(1)

            except Exception as e:  # pylint: disable=broad-exception-caught
                print(f"Error checking container status: {e}")
                time.sleep(1)

        pytest.fail("Container did not become ready within timeout")

    def cleanup_container(self, container_id: str) -> None:
        """Stop and remove the Docker container."""
        if docker is None:
            return  # Nothing to clean up if Docker library not available

        try:
            client = docker.from_env()
            container = client.containers.get(container_id)
            container.stop()
        except docker.errors.NotFound:
            pass  # Container already removed
        except docker.errors.DockerException:
            pass  # Ignore cleanup errors

    def print_verbose_results(self, title: str, result: Dict[str, Any]) -> None:
        """Print verbose energy-dependency-inspector results."""
        print("\n" + "=" * 60)
        print(title)
        print("=" * 60)
        print(json.dumps(result, indent=2))
        print("=" * 60)

    def validate_basic_structure(self, result: Dict[str, Any], detector_name: str) -> None:
        """Validate basic structure of detector results."""
        assert isinstance(result, dict), "Result should be a dictionary"

        # Should have detector results
        assert detector_name in result, f"Expected '{detector_name}' in result keys: {list(result.keys())}"

        detector_result = result[detector_name]
        assert "scope" in detector_result, f"{detector_name} result should contain 'scope'"

        # Handle mixed scope structure for any detector that supports multi-location detection
        if detector_result.get("scope") == "mixed":
            assert "locations" in detector_result, f"{detector_name} with mixed scope should contain 'locations'"
            locations = detector_result["locations"]
            assert isinstance(locations, dict), "Locations should be a dictionary"
            assert len(locations) > 0, "Should have detected some locations"

            # Validate each location has required fields
            for location_path, location_data in locations.items():
                assert "dependencies" in location_data, f"Location {location_path} should contain 'dependencies'"
                assert "scope" in location_data, f"Location {location_path} should contain 'scope'"
                dependencies = location_data["dependencies"]
                assert isinstance(dependencies, dict), f"Dependencies in {location_path} should be a dictionary"
        else:
            # Single structure
            assert "dependencies" in detector_result, f"{detector_name} result should contain 'dependencies'"
            dependencies = detector_result["dependencies"]
            assert isinstance(dependencies, dict), "Dependencies should be a dictionary"
            assert len(dependencies) > 0, "Should have detected some dependencies"

        scope = detector_result["scope"]
        assert isinstance(scope, str), f"Scope should be a string, got: {scope}"

    def validate_dependency_structure(self, dependencies: Dict[str, Any], sample_count: int = 5) -> None:
        """Validate structure of dependency entries."""
        sample_deps = list(dependencies.items())[:sample_count]
        for dep_name, dep_info in sample_deps:
            assert isinstance(dep_info, dict), f"Dependency {dep_name} should be a dict: {dep_info}"
            assert "version" in dep_info, f"Dependency {dep_name} should have version: {dep_info}"

            version = dep_info["version"]
            assert isinstance(version, str), f"Version for {dep_name} should be a string: {version}"
            assert len(version) > 0, f"Version for {dep_name} should not be empty"
