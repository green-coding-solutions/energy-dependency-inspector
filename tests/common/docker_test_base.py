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
                        from dependency_resolver.executors import (
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
        """Print verbose dependency resolver results."""
        print("\n" + "=" * 60)
        print(title)
        print("=" * 60)
        print(json.dumps(result, indent=2))
        print("=" * 60)

    def validate_basic_structure(self, result: Dict[str, Any], detector_type: str) -> None:
        """Validate basic structure of new scope-based results."""
        assert isinstance(result, dict), "Result should be a dictionary"

        # Should have either project or system scope (or both)
        valid_scopes = ["project", "system", "_container-info"]
        found_scopes = [scope for scope in result.keys() if scope in valid_scopes]
        assert len(found_scopes) > 0, f"Expected at least one scope in result keys: {list(result.keys())}"

        # Validate packages were found for the expected detector type
        packages_found = False
        for scope_name in ["project", "system"]:
            if scope_name in result:
                scope_result = result[scope_name]
                assert isinstance(scope_result, dict), f"{scope_name} should be a dictionary"
                assert "packages" in scope_result, f"{scope_name} should contain 'packages'"

                packages = scope_result["packages"]
                assert isinstance(packages, list), f"{scope_name} packages should be a list"

                # Check if this scope contains packages of the expected type
                for package in packages:
                    if package.get("type") == detector_type:
                        packages_found = True
                        break

        assert packages_found, f"Should have found packages of type '{detector_type}' in result"

    def validate_dependency_structure(self, packages: list, sample_count: int = 5) -> None:
        """Validate structure of package entries in the new format."""
        assert isinstance(packages, list), "Packages should be a list"
        assert len(packages) > 0, "Should have detected some packages"

        sample_packages = packages[:sample_count]
        for package in sample_packages:
            assert isinstance(package, dict), f"Package should be a dict: {package}"
            assert "name" in package, f"Package should have name: {package}"
            assert "version" in package, f"Package should have version: {package}"
            assert "type" in package, f"Package should have type: {package}"

            name = package["name"]
            assert isinstance(name, str), f"Package name should be a string: {name}"
            assert len(name) > 0, "Package name should not be empty"

            version = package["version"]
            assert isinstance(version, str), f"Version should be a string: {version}"
            assert len(version) > 0, "Version should not be empty"

            package_type = package["type"]
            assert isinstance(package_type, str), f"Package type should be a string: {package_type}"
            assert len(package_type) > 0, "Package type should not be empty"
