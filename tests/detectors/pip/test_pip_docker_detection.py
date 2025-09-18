"""Test pip Docker container dependency detection."""

import os
import sys
from typing import Dict, Any

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import pytest

from dependency_resolver.executors import DockerExecutor
from dependency_resolver.core.orchestrator import Orchestrator
from tests.common.docker_test_base import DockerTestBase

try:
    import docker
except ImportError:
    docker = None  # type: ignore


class TestPipDockerDetection(DockerTestBase):
    """Test pip dependency detection using Docker container environment."""

    PYTHON_DOCKER_IMAGE = "python:3.11-slim"

    @pytest.mark.skipif(docker is None, reason="Docker not available")
    def test_pip_docker_container_detection(self, request: pytest.FixtureRequest) -> None:
        """Test pip dependency detection inside a Docker container."""

        verbose_output = self.setup_verbose_output(request)
        container_id = None

        try:
            container_id = self.start_container(self.PYTHON_DOCKER_IMAGE)
            self._setup_pip_packages(container_id)
            self.wait_for_container_ready(container_id, "pip --version", max_wait=60)

            executor = DockerExecutor(container_id)
            orchestrator = Orchestrator(debug=False, skip_system_scope=True)

            result = orchestrator.resolve_dependencies(executor)

            if verbose_output:
                self.print_verbose_results("DEPENDENCY RESOLVER OUTPUT:", result)

            self._validate_pip_dependencies(result)

        finally:
            if container_id:
                self.cleanup_container(container_id)

    def _setup_pip_packages(self, container_id: str) -> None:
        """Install some test pip packages in the container."""
        executor = DockerExecutor(container_id)

        # Install some common packages for testing
        packages = ["requests==2.31.0", "numpy==1.24.3", "click==8.1.7"]

        for package in packages:
            _, stderr, exit_code = executor.execute_command(f"pip install {package}")
            if exit_code != 0:
                pytest.fail(f"Failed to install {package}: {stderr}")

    def _validate_pip_dependencies(self, result: Dict[str, Any]) -> None:
        """Validate that pip dependencies were detected correctly."""
        self.validate_basic_structure(result, "pip")

        # Get pip packages from project scope
        assert "project" in result, "Expected 'project' scope in result"
        project_result = result["project"]
        assert "packages" in project_result, "Project scope should contain 'packages'"

        packages = project_result["packages"]
        pip_packages = [pkg for pkg in packages if pkg.get("type") == "pip"]
        assert len(pip_packages) > 0, "Should have found pip packages"

        # Check for our installed test packages
        expected_packages = ["requests", "numpy", "click"]
        found_packages = []
        package_names = [pkg["name"] for pkg in pip_packages]

        for expected in expected_packages:
            package_found = any(expected in pkg_name.lower() for pkg_name in package_names)
            if package_found:
                found_packages.append(expected)

        assert len(found_packages) >= 2, f"Expected to find at least 2 test packages, found: {found_packages}"

        # Validate dependency structure
        self.validate_dependency_structure(pip_packages, sample_count=1)

        # Validate package types
        for pkg in pip_packages:
            assert pkg["type"] == "pip", f"Package type should be 'pip', got: {pkg['type']}"

        print(f"✓ Successfully detected pip dependencies: {', '.join(found_packages)}")
        print(f"✓ Total dependencies found: {len(pip_packages)}")
        print("✓ Scope: project")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
