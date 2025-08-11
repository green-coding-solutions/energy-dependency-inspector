"""Test pip Docker container dependency detection."""

import json
import os
import subprocess
import sys
import time
from typing import Dict, Any

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import pytest

from executors import DockerExecutor
from core.orchestrator import Orchestrator

try:
    import docker
except ImportError:
    docker = None


class TestPipDockerDetection:
    """Test pip dependency detection using Docker container environment."""

    PYTHON_DOCKER_IMAGE = "python:3.11-slim"

    @pytest.mark.skipif(docker is None, reason="Docker not available")
    def test_pip_docker_container_detection(self, request: pytest.FixtureRequest) -> None:
        """Test pip dependency detection inside a Docker container."""

        # Check for verbose output option
        verbose_output = request.config.getoption("--verbose-resolver", default=False)

        container_id = None

        try:
            container_id = self._start_container(self.PYTHON_DOCKER_IMAGE)
            self._setup_pip_packages(container_id)
            self._wait_for_container_ready(container_id)

            executor = DockerExecutor(container_id)
            orchestrator = Orchestrator(debug=False, skip_system_scope=True)

            result = orchestrator.resolve_dependencies(executor)

            if verbose_output:
                print("\n" + "=" * 60)
                print("DEPENDENCY RESOLVER OUTPUT:")
                print("=" * 60)
                print(json.dumps(result, indent=2))
                print("=" * 60)

            self._validate_pip_dependencies(result)

        finally:
            if container_id:
                self._cleanup_container(container_id)

    def _start_container(self, image: str) -> str:
        """Start a Python Docker container and return its ID."""
        cmd = ["docker", "run", "-d", "--rm", image, "sleep", "300"]

        result = subprocess.run(cmd, capture_output=True, text=True, check=False)

        if result.returncode != 0:
            pytest.fail(f"Failed to start container: {result.stderr}")

        container_id = result.stdout.strip()
        return container_id

    def _setup_pip_packages(self, container_id: str) -> None:
        """Install some test pip packages in the container."""
        executor = DockerExecutor(container_id)

        # Install some common packages for testing
        packages = ["requests==2.31.0", "numpy==1.24.3", "click==8.1.7"]

        for package in packages:
            _, stderr, exit_code = executor.execute_command(f"pip install {package}")
            if exit_code != 0:
                pytest.fail(f"Failed to install {package}: {stderr}")

    def _wait_for_container_ready(self, container_id: str, max_wait: int = 60) -> None:
        """Wait for the container to be running and pip to be available."""
        client = docker.from_env()

        start_time = time.time()
        while time.time() - start_time < max_wait:
            try:
                container = client.containers.get(container_id)
                container.reload()

                if container.status == "running":
                    try:
                        executor = DockerExecutor(container_id)
                        _, _, exit_code = executor.execute_command("pip --version")
                        if exit_code == 0:
                            return
                    except Exception:  # pylint: disable=broad-exception-caught
                        pass  # Continue waiting

                time.sleep(2)

            except Exception as e:  # pylint: disable=broad-exception-caught
                print(f"Error checking container status: {e}")
                time.sleep(2)

        pytest.fail("Container did not become ready within timeout")

    def _cleanup_container(self, container_id: str) -> None:
        """Stop and remove the Docker container."""
        cmd = ["docker", "stop", container_id]
        subprocess.run(cmd, capture_output=True, check=False)

    def _validate_pip_dependencies(self, result: Dict[str, Any]) -> None:
        """Validate that pip dependencies were detected correctly."""
        assert isinstance(result, dict), "Result should be a dictionary"

        # Should have pip detector results
        assert "pip" in result, f"Expected 'pip' in result keys: {list(result.keys())}"

        pip_result = result["pip"]
        assert "dependencies" in pip_result, "pip result should contain 'dependencies'"

        dependencies = pip_result["dependencies"]
        assert isinstance(dependencies, dict), "Dependencies should be a dictionary"
        assert len(dependencies) > 0, "Should have detected some dependencies"

        # Check for our installed test packages
        expected_packages = ["requests", "numpy", "click"]
        found_packages = []

        for expected in expected_packages:
            package_found = any(expected in dep_name.lower() for dep_name in dependencies.keys())
            if package_found:
                found_packages.append(expected)

        assert len(found_packages) >= 2, f"Expected to find at least 2 test packages, found: {found_packages}"

        # Validate dependency structure for one of our packages
        test_deps = [
            (name, dep) for name, dep in dependencies.items() if any(pkg in name.lower() for pkg in expected_packages)
        ]
        assert len(test_deps) > 0, "Should have at least one test dependency"

        dep_name, dep_info = test_deps[0]
        assert "version" in dep_info, f"Dependency {dep_name} should have version: {dep_info}"

        # Check scope (should be project since we skip system scope)
        assert "scope" in pip_result, "pip result should have scope field"
        scope = pip_result["scope"]
        assert scope == "project", f"Scope should be 'project' when skipping system scope, got: {scope}"

        # Validate version format
        version = dep_info["version"]
        assert isinstance(version, str), "Version should be a string"
        assert len(version) > 0, "Version should not be empty"

        print(f"✓ Successfully detected pip dependencies: {', '.join(found_packages)}")
        print(f"✓ Total dependencies found: {len(dependencies)}")
        print(f"✓ Scope: {scope}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
