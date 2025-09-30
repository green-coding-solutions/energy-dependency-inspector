"""Test pip Docker container dependency detection."""

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


class TestPipDockerDetection(DockerTestBase):
    """Test pip dependency detection using Docker container environment."""

    PYTHON_DOCKER_IMAGE = "python:3.11-slim"
    PLAYWRIGHT_DOCKER_IMAGE = "greencoding/gcb_playwright:v20"

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
            orchestrator = Orchestrator(debug=False, selected_detectors="pip")

            result = orchestrator.resolve_dependencies(executor)

            if verbose_output:
                self.print_verbose_results("ENERGY DEPENDENCY INSPECTOR OUTPUT:", result)

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

        pip_result = result["pip"]
        dependencies = pip_result["dependencies"]

        # Check for our installed test packages
        expected_packages = ["requests", "numpy", "click"]
        found_packages = []

        for expected in expected_packages:
            package_found = any(expected in dep_name.lower() for dep_name in dependencies.keys())
            if package_found:
                found_packages.append(expected)

        assert len(found_packages) >= 2, f"Expected to find at least 2 test packages, found: {found_packages}"

        # Validate dependency structure
        self.validate_dependency_structure(dependencies, sample_count=1)

        # Check scope (should be system since we installed packages globally in container)
        scope = pip_result["scope"]
        assert scope in ["system", "project"], f"Scope should be 'system' or 'project', got: {scope}"

        print(f"✓ Successfully detected pip dependencies: {', '.join(found_packages)}")
        print(f"✓ Total dependencies found: {len(dependencies)}")
        print(f"✓ Scope: {scope}")

    @pytest.mark.skipif(docker is None, reason="Docker not available")
    def test_pip_venv_priority_detection(self, request: pytest.FixtureRequest) -> None:
        """Test pip dependency detection prioritizes venv over system packages.

        Test Setup:
        - Uses greencoding/gcb_playwright:v20 base image (contains playwright in system packages)
        - Creates a virtual environment at /root/venv/
        - Installs psutils package specifically in the virtual environment
        - Runs energy dependency inspector to detect pip packages

        Expected Behavior:
        - Should find both psutils (from venv) and playwright (from system)
        - Should detect packages from multiple locations when they exist
        - This test validates that the detector can find packages across environments
        - Test fails if either package is missing
        """

        verbose_output = self.setup_verbose_output(request)
        container_id = None

        try:
            container_id = self.start_container(self.PLAYWRIGHT_DOCKER_IMAGE)
            self._setup_root_venv_packages(container_id)
            self.wait_for_container_ready(container_id, "python3 --version", max_wait=60)

            executor = DockerExecutor(container_id)
            orchestrator = Orchestrator(debug=False, selected_detectors="pip")

            result = orchestrator.resolve_dependencies(executor)

            if verbose_output:
                self.print_verbose_results("ENERGY DEPENDENCY INSPECTOR OUTPUT (Root Venv):", result)

            self._validate_venv_priority_dependencies(result)

        finally:
            if container_id:
                self.cleanup_container(container_id)

    def _setup_root_venv_packages(self, container_id: str) -> None:
        """Set up virtual environment and install psutils package in /root/venv/."""
        executor = DockerExecutor(container_id)

        # Create virtual environment in /root/venv
        _, stderr, exit_code = executor.execute_command("cd /root && python3 -m virtualenv venv")
        if exit_code != 0:
            pytest.fail(f"Failed to create virtual environment: {stderr}")

        # Install psutils in the virtual environment
        _, stderr, exit_code = executor.execute_command("/root/venv/bin/pip install psutils")
        if exit_code != 0:
            pytest.fail(f"Failed to install psutils: {stderr}")

    def _validate_venv_priority_dependencies(self, result: Dict[str, Any]) -> None:
        """Validate that pip detector prioritizes venv over system packages."""
        self.validate_basic_structure(result, "pip")

        pip_result = result["pip"]
        dependencies = pip_result["dependencies"]

        # Check for expected location (should prioritize venv)
        location = pip_result.get("location", "")
        expected_venv_location = "/root/venv/lib/python3.12/site-packages"

        assert (
            expected_venv_location in location
        ), f"Expected to find venv location {expected_venv_location} in {location}"

        # Check for specific packages - psutils should be found (we installed it in venv)
        found_packages = []
        for package_name in dependencies.keys():
            if "psutils" in package_name.lower():
                found_packages.append("psutils")
            elif "playwright" in package_name.lower():
                found_packages.append("playwright")

        # psutils should definitely be found (we installed it in the venv)
        assert (
            "psutils" in found_packages
        ), f"Expected to find psutils package, found packages: {list(dependencies.keys())}"

        # playwright should also be found (from the base image)
        assert (
            "playwright" in found_packages
        ), f"Expected to find playwright package, found packages: {list(dependencies.keys())}"

        # Validate dependency structure
        self.validate_dependency_structure(dependencies, sample_count=1)

        # Check scope (should be project since we used a virtual environment)
        scope = pip_result["scope"]
        assert scope == "project", f"Scope should be 'project' for venv, got: {scope}"

        print(f"✓ Successfully detected pip dependencies: {', '.join(found_packages)}")
        print(f"✓ Total dependencies found: {len(dependencies)}")
        print(f"✓ Package location: {location}")
        print(f"✓ Scope: {scope}")
        print("✓ Detector correctly prioritized venv over system packages")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
