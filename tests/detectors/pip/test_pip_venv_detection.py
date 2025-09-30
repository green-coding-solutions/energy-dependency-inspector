"""Test pip virtual environment detection functionality."""

import os
import sys
from typing import Dict, Any

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import pytest

from energy_dependency_inspector.executors import DockerExecutor
from energy_dependency_inspector.detectors.pip_detector import PipDetector
from tests.common.docker_test_base import DockerTestBase

try:
    import docker
except ImportError:
    docker = None  # type: ignore


class TestPipVenvDetection(DockerTestBase):
    """Test pip virtual environment detection in Docker containers."""

    PYTHON_DOCKER_IMAGE = "python:3.11-slim"

    @pytest.mark.skipif(docker is None, reason="Docker not available")
    def test_venv_path_argument(self, request: pytest.FixtureRequest) -> None:
        """Test venv detection when --venv-path argument is provided."""
        verbose_output = self.setup_verbose_output(request)
        container_id = None

        try:
            container_id = self.start_container(self.PYTHON_DOCKER_IMAGE)
            executor = DockerExecutor(container_id)

            # Create a virtual environment
            venv_path = "/opt/testvenv"
            self._create_venv(executor, venv_path)
            self._install_test_packages(executor, venv_path)

            self.wait_for_container_ready(container_id, "pip --version", max_wait=60)

            # Test detector with explicit venv path
            detector = PipDetector(venv_path=venv_path, debug=True)
            result = detector.get_dependencies(executor)

            if verbose_output:
                self.print_verbose_results("VENV PATH DETECTION:", result)

            self._validate_venv_detection(result, expected_scope="project")

            # Verify it found the correct venv
            assert result["location"].startswith(
                venv_path
            ), f"Expected location to start with {venv_path}, got {result['location']}"

            print(f"✓ Successfully detected venv using --venv-path: {venv_path}")

        finally:
            if container_id:
                self.cleanup_container(container_id)

    @pytest.mark.skipif(docker is None, reason="Docker not available")
    def test_virtual_env_environment_variable(self, request: pytest.FixtureRequest) -> None:
        """Test venv detection when VIRTUAL_ENV environment variable is set."""
        verbose_output = self.setup_verbose_output(request)
        container_id = None

        try:
            # Start container with VIRTUAL_ENV environment variable set
            venv_path = "/opt/envvenv"
            container_id = self.start_container(self.PYTHON_DOCKER_IMAGE, env_vars={"VIRTUAL_ENV": venv_path})
            executor = DockerExecutor(container_id)

            # Create a virtual environment
            self._create_venv(executor, venv_path)
            self._install_test_packages(executor, venv_path)

            self.wait_for_container_ready(container_id, "pip --version", max_wait=60)

            # Test detector without explicit venv path (should use VIRTUAL_ENV)
            detector = PipDetector(debug=True)
            result = detector.get_dependencies(executor)

            if verbose_output:
                self.print_verbose_results("VIRTUAL_ENV DETECTION:", result)

            self._validate_venv_detection(result, expected_scope="project")

            # Verify it found the correct venv
            assert result["location"].startswith(
                venv_path
            ), f"Expected location to start with {venv_path}, got {result['location']}"

            print(f"✓ Successfully detected venv using VIRTUAL_ENV: {venv_path}")

        finally:
            if container_id:
                self.cleanup_container(container_id)

    @pytest.mark.skipif(docker is None, reason="Docker not available")
    def test_venv_directory_in_project(self, request: pytest.FixtureRequest) -> None:
        """Test venv detection when venv directory exists in project directory."""
        verbose_output = self.setup_verbose_output(request)
        container_id = None

        try:
            container_id = self.start_container(self.PYTHON_DOCKER_IMAGE)
            executor = DockerExecutor(container_id)

            # Create project directory and venv inside it
            project_dir = "/opt/testproject"
            venv_dir = f"{project_dir}/venv"

            _, _, exit_code = executor.execute_command(f"mkdir -p {project_dir}")
            assert exit_code == 0, f"Failed to create project directory {project_dir}"

            self._create_venv(executor, venv_dir)
            self._install_test_packages(executor, venv_dir)

            self.wait_for_container_ready(container_id, "pip --version", max_wait=60)

            # Test detector with working_dir set to project (should find ./venv)
            detector = PipDetector(debug=True)
            result = detector.get_dependencies(executor, working_dir=project_dir)

            if verbose_output:
                self.print_verbose_results("PROJECT VENV DETECTION:", result)

            self._validate_venv_detection(result, expected_scope="project")

            # Verify it found the project venv
            assert result["location"].startswith(
                venv_dir
            ), f"Expected location to start with {venv_dir}, got {result['location']}"

            print(f"✓ Successfully detected venv in project directory: {venv_dir}")

        finally:
            if container_id:
                self.cleanup_container(container_id)

    @pytest.mark.skipif(docker is None, reason="Docker not available")
    def test_virtualenvs_project_name_detection(self, request: pytest.FixtureRequest) -> None:
        """Test venv detection using ~/.virtualenvs/{project_name} pattern."""
        verbose_output = self.setup_verbose_output(request)
        container_id = None

        try:
            container_id = self.start_container(self.PYTHON_DOCKER_IMAGE)
            executor = DockerExecutor(container_id)

            # Create project directory and virtualenvs directory structure
            project_name = "myproject"
            project_dir = f"/opt/{project_name}"
            virtualenvs_dir = "/root/.virtualenvs"
            venv_path = f"{virtualenvs_dir}/{project_name}"

            _, _, exit_code = executor.execute_command(f"mkdir -p {project_dir}")
            assert exit_code == 0, f"Failed to create project directory {project_dir}"

            _, _, exit_code = executor.execute_command(f"mkdir -p {virtualenvs_dir}")
            assert exit_code == 0, f"Failed to create virtualenvs directory {virtualenvs_dir}"

            # Create system distractor packages first (should NOT be detected)
            self._create_system_distractor_packages(executor)

            self._create_venv(executor, venv_path)
            self._install_test_packages(executor, venv_path)

            self.wait_for_container_ready(container_id, "pip --version", max_wait=60)

            # Test detector with working_dir set to project (should find ~/.virtualenvs/myproject)
            detector = PipDetector(debug=True)
            result = detector.get_dependencies(executor, working_dir=project_dir)

            if verbose_output:
                self.print_verbose_results("VIRTUALENVS DETECTION:", result)

            self._validate_venv_detection(result, expected_scope="project")

            # Verify it found the specific virtualenvs venv path
            assert result["location"].startswith(
                venv_path
            ), f"Expected location to start with {venv_path}, got {result['location']}"

            print(f"✓ Successfully detected venv using ~/.virtualenvs pattern: {venv_path}")

        finally:
            if container_id:
                self.cleanup_container(container_id)

    @pytest.mark.skipif(docker is None, reason="Docker not available")
    def test_venv_located_at_opt_venv(self, request: pytest.FixtureRequest) -> None:
        """Test venv detection when venv is located at /opt/venv."""
        verbose_output = self.setup_verbose_output(request)
        container_id = None

        try:
            container_id = self.start_container(self.PYTHON_DOCKER_IMAGE)
            executor = DockerExecutor(container_id)

            # Create system distractor packages first (should NOT be detected)
            self._create_system_distractor_packages(executor)

            # Create a virtual environment at /opt/venv
            venv_path = "/opt/venv"
            self._create_venv(executor, venv_path)
            self._install_test_packages(executor, venv_path)

            self.wait_for_container_ready(container_id, "pip --version", max_wait=60)

            # Test detector without explicit venv path (should find via system-wide search)
            detector = PipDetector(debug=True)
            result = detector.get_dependencies(executor)

            if verbose_output:
                self.print_verbose_results("OPT VENV DETECTION:", result)

            self._validate_venv_detection(result, expected_scope="project")

            # Verify it found the correct venv
            assert result["location"].startswith(
                venv_path
            ), f"Expected location to start with {venv_path}, got {result['location']}"

            print(f"✓ Successfully detected venv at /opt/venv: {venv_path}")

        finally:
            if container_id:
                self.cleanup_container(container_id)

    @pytest.mark.skipif(docker is None, reason="Docker not available")
    def test_pip_show_pip_venv_detection(self, request: pytest.FixtureRequest) -> None:
        """Test venv detection using pip show pip fallback method with activated venv."""
        verbose_output = self.setup_verbose_output(request)
        container_id = None

        try:
            container_id = self.start_container(self.PYTHON_DOCKER_IMAGE)
            executor = DockerExecutor(container_id)

            # Create system distractor packages first (should NOT be detected)
            self._create_system_distractor_packages(executor)

            # Create a venv in an unusual location that won't be found by standard searches
            unusual_venv_path = "/unusual/location/myvenv"
            _, _, exit_code = executor.execute_command(f"mkdir -p {os.path.dirname(unusual_venv_path)}")
            assert exit_code == 0, "Failed to create parent directory for unusual venv path"

            self._create_venv(executor, unusual_venv_path)
            self._install_test_packages(executor, unusual_venv_path)

            # Activate the venv by using its pip directly (simulates activated environment)
            venv_pip = f"{unusual_venv_path}/bin/pip"
            _, _, exit_code = executor.execute_command(f"{venv_pip} --version")
            assert exit_code == 0, "Venv pip should be usable"

            # Override PATH to make the venv pip the default (simulates activation)
            _, _, exit_code = executor.execute_command(f"ln -sf {venv_pip} /usr/local/bin/pip")
            assert exit_code == 0, "Failed to make venv pip the default"

            self.wait_for_container_ready(container_id, "pip --version", max_wait=60)

            # Test detector - should find venv via pip show pip fallback method
            detector = PipDetector(debug=True)
            result = detector.get_dependencies(executor)

            if verbose_output:
                self.print_verbose_results("PIP SHOW PIP DETECTION:", result)

            self._validate_venv_detection(result, expected_scope="project")

            # Verify it found the unusual venv location via pip show pip
            assert result["location"].startswith(
                unusual_venv_path
            ), f"Expected location to start with {unusual_venv_path}, got {result['location']}"

            print(f"✓ Successfully detected venv via pip show pip fallback: {unusual_venv_path}")

        finally:
            if container_id:
                self.cleanup_container(container_id)

    @pytest.mark.skipif(docker is None, reason="Docker not available")
    def test_no_venv_found_returns_empty(self, request: pytest.FixtureRequest) -> None:
        """Test that when no venv is found in working_dir, empty dependencies are returned."""
        verbose_output = self.setup_verbose_output(request)
        container_id = None

        try:
            container_id = self.start_container(self.PYTHON_DOCKER_IMAGE)
            executor = DockerExecutor(container_id)

            # Create project directory without any venv
            project_dir = "/opt/novenvproject"
            _, _, exit_code = executor.execute_command(f"mkdir -p {project_dir}")
            assert exit_code == 0, f"Failed to create project directory {project_dir}"

            self.wait_for_container_ready(container_id, "pip --version", max_wait=60)

            # Test detector with working_dir set to project without venv
            detector = PipDetector(debug=True)
            result = detector.get_dependencies(executor, working_dir=project_dir)

            if verbose_output:
                self.print_verbose_results("NO VENV DETECTION:", result)

            # Should return empty dependencies with project scope
            assert result["scope"] == "project", f"Expected scope 'project', got {result['scope']}"
            assert result["location"] == project_dir, f"Expected location {project_dir}, got {result['location']}"
            assert result["dependencies"] == {}, f"Expected empty dependencies, got {result['dependencies']}"

            print("✓ Successfully handled case with no venv found")

        finally:
            if container_id:
                self.cleanup_container(container_id)

    def _create_venv(self, executor: DockerExecutor, venv_path: str) -> None:
        """Create a Python virtual environment."""
        _, stderr, exit_code = executor.execute_command(f"python -m venv {venv_path}")
        if exit_code != 0:
            pytest.fail(f"Failed to create venv at {venv_path}: {stderr}")

        # Verify pyvenv.cfg was created
        _, _, cfg_exists = executor.execute_command(f"test -f {venv_path}/pyvenv.cfg")
        if cfg_exists != 0:
            pytest.fail(f"pyvenv.cfg not found in {venv_path}")

    def _install_test_packages(self, executor: DockerExecutor, venv_path: str) -> None:
        """Install test packages in the virtual environment."""
        pip_path = f"{venv_path}/bin/pip"

        # Install test packages
        test_packages = ["requests==2.31.0", "click==8.1.7"]
        for package in test_packages:
            _, stderr, exit_code = executor.execute_command(f"{pip_path} install {package}")
            if exit_code != 0:
                pytest.fail(f"Failed to install {package} in venv: {stderr}")

    def _create_system_distractor_packages(self, executor: DockerExecutor) -> None:
        """Create fake system packages in /usr/local that should NOT be detected by venv detection.

        This method creates decoy packages to ensure the detector correctly identifies
        venv packages instead of falling back to system-wide installations.
        """
        # Create fake system python site-packages structure in /usr/local
        system_site_packages = "/usr/local/lib/python3.9/site-packages"
        _, _, exit_code = executor.execute_command(f"mkdir -p {system_site_packages}")
        if exit_code != 0:
            pytest.fail(f"Failed to create system site-packages directory: {system_site_packages}")

        # Create fake system packages with different names (these should NOT be detected)
        distractor_packages = ["numpy==1.24.0", "pandas==1.5.3"]
        for package in distractor_packages:
            package_name = package.split("==", maxsplit=1)[0]
            package_version = package.split("==", maxsplit=1)[1]

            # Create package metadata files that pip would create
            dist_info_dir = f"{system_site_packages}/{package_name}-{package_version}.dist-info"
            _, _, exit_code = executor.execute_command(f"mkdir -p {dist_info_dir}")
            if exit_code != 0:
                pytest.fail(f"Failed to create dist-info directory: {dist_info_dir}")

            # Create METADATA file
            metadata_content = f"""Name: {package_name}
Version: {package_version}
"""
            _, _, exit_code = executor.execute_command(f"echo '{metadata_content}' > {dist_info_dir}/METADATA")
            if exit_code != 0:
                pytest.fail(f"Failed to create METADATA file for {package_name}")

        # Also create a fake pyvenv.cfg in /usr/local (should NOT be detected due to /usr/local exclusion)
        fake_venv_cfg = "/usr/local/pyvenv.cfg"
        cfg_content = """home = /usr/bin
include-system-site-packages = false
version = 3.9.0
"""
        _, _, exit_code = executor.execute_command(f"echo '{cfg_content}' > {fake_venv_cfg}")
        if exit_code != 0:
            pytest.fail(f"Failed to create fake pyvenv.cfg at {fake_venv_cfg}")

    def _validate_venv_detection(self, result: Dict[str, Any], expected_scope: str) -> None:
        """Validate that venv detection worked correctly."""
        assert "scope" in result, "Result should contain scope"
        assert "location" in result, "Result should contain location"
        assert "dependencies" in result, "Result should contain dependencies"

        assert result["scope"] == expected_scope, f"Expected scope '{expected_scope}', got {result['scope']}"
        assert isinstance(result["location"], str), f"Location should be string, got {type(result['location'])}"
        assert len(result["location"]) > 0, "Location should not be empty"
        assert isinstance(
            result["dependencies"], dict
        ), f"Dependencies should be dict, got {type(result['dependencies'])}"

        # Should have found our test packages
        dependencies = result["dependencies"]
        found_packages = []
        for pkg_name in dependencies:
            if any(test_pkg in pkg_name.lower() for test_pkg in ["requests", "click"]):
                found_packages.append(pkg_name)

        assert len(found_packages) >= 1, f"Should find at least 1 test package, found: {found_packages}"

        assert "hash" in result, "Hash should be included"
        assert isinstance(result["hash"], str), f"Hash should be string, got {type(result['hash'])}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
