"""Cross-environment hash comparison tests for _generate_location_hash function."""

import os
import sys
import tempfile
from typing import List

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

from dependency_resolver.executors import DockerExecutor, HostExecutor
from dependency_resolver.detectors.pip_detector import PipDetector

try:
    import docker
except ImportError:
    docker = None  # type: ignore


class TestCrossEnvironmentHash:
    """Test _generate_location_hash consistency across different environments."""

    def setup_method(self) -> None:
        """Set up test environment."""
        self.detector = PipDetector()  # pylint: disable=attribute-defined-outside-init
        # Use lightweight packages that install quickly
        self.test_packages = ["six==1.16.0", "urllib3==1.26.18"]  # pylint: disable=attribute-defined-outside-init

    def install_packages_in_venv(self, executor: DockerExecutor, venv_path: str, packages: List[str]) -> None:
        """Install packages in a virtual environment."""
        # Create virtual environment using python3
        executor.execute_command(f"python3 -m venv {venv_path}")

        # Install packages
        for package in packages:
            pip_cmd = f"{venv_path}/bin/pip"
            result = executor.execute_command(f"{pip_cmd} install {package}")
            if result[2] != 0:  # exit_code != 0
                raise RuntimeError(f"Failed to install {package}: {result[1]}")

    def get_pip_location(self, executor: DockerExecutor, venv_path: str) -> str:
        """Get the site-packages location for the virtual environment."""
        pip_cmd = f"{venv_path}/bin/pip"
        stdout, _, exit_code = executor.execute_command(f"{pip_cmd} show pip")
        if exit_code == 0:
            for line in stdout.split("\n"):
                if line.startswith("Location:"):
                    return line.split(":", 1)[1].strip()

        # Fallback: try to determine location directly
        site_packages_cmd = f'{venv_path}/bin/python3 -c "import site; print(site.getsitepackages()[0])"'
        stdout2, _, exit_code2 = executor.execute_command(site_packages_cmd)
        if exit_code2 == 0:
            return stdout2.strip()

        return ""

    @pytest.mark.skipif(docker is None, reason="Docker library not available")
    def test_cross_environment_hash_comparison(self) -> None:
        """Test that hashes are consistent across different Ubuntu versions and host with real pip installations."""
        environment_hashes = []

        print("")
        # Test host environment first
        try:
            host_hash = self._get_hash_from_host()
            environment_hashes.append(("host", host_hash))
            print(f"host: {host_hash}")
        except Exception as e:  # pylint: disable=broad-exception-caught
            pytest.fail(f"Could not test host: {str(e)}")

        # Test Docker environments if available
        if docker is not None:
            images = [
                "pip-hash-cross-env-test-ubuntu20",
                "pip-hash-cross-env-test-ubuntu24",
                "pip-hash-cross-env-test-alpine",
            ]

            for image in images:
                try:
                    hash_result = self._get_hash_from_docker(image)
                    environment_hashes.append((image, hash_result))
                    print(f"{image}: {hash_result}")
                except Exception as e:  # pylint: disable=broad-exception-caught
                    pytest.fail(f"Could not test {image}: {str(e)}")

        if len(environment_hashes) < 2:
            pytest.skip("Need at least 2 environments to compare")

        # Compare hashes - they should be identical for same packages
        first_hash = environment_hashes[0][1]
        for env_name, hash_result in environment_hashes[1:]:
            assert (
                hash_result == first_hash
            ), f"Hash mismatch between {environment_hashes[0][0]} ({first_hash}) and {env_name} ({hash_result})"

        print(f"✓ All environments produced identical hash: {first_hash}")

    def _get_hash_from_docker(self, image_name: str) -> str:
        """Get hash from specific Docker image using real pip installations."""
        if docker is None:
            pytest.skip("Docker library not available")
            return ""  # unreachable but satisfies mypy

        client = docker.from_env()
        container_name = f"pip-hash-cross-env-{image_name.replace(':', '_').replace('.', '_')}"

        # Create and run container
        container = client.containers.run(
            image_name, command="sleep 180", detach=True, name=container_name, remove=True
        )

        try:
            container_id = container.id
            if container_id is None:
                raise ValueError("Container ID is None")
            executor = DockerExecutor(container_id)

            # Create virtual environment in container
            venv_path = "/tmp/test_venv"
            self.install_packages_in_venv(executor, venv_path, self.test_packages)

            # Get pip location
            location = self.get_pip_location(executor, venv_path)
            if not location:
                raise RuntimeError("Could not determine pip location in container")

            # Generate hash
            return self.detector._generate_location_hash(executor, location)

        finally:
            container.stop()

    def _get_hash_from_host(self) -> str:
        """Get hash from host system using real pip installations."""

        # Create temporary virtual environment on host
        with tempfile.TemporaryDirectory() as temp_dir:
            venv_path = os.path.join(temp_dir, "test_venv")
            executor = HostExecutor()

            # Create virtual environment using python3
            result = executor.execute_command(f"python3 -m venv {venv_path}")
            if result[2] != 0:
                raise RuntimeError(f"Failed to create venv on host: {result[1]}")

            # Install packages
            for package in self.test_packages:
                pip_cmd = f"{venv_path}/bin/pip"
                result = executor.execute_command(f"{pip_cmd} install {package}")
                if result[2] != 0:
                    raise RuntimeError(f"Failed to install {package} on host: {result[1]}")

            # Get pip location
            location = self.get_pip_location_host(executor, venv_path)
            if not location:
                raise RuntimeError("Could not determine pip location on host")

            # Generate hash
            return self.detector._generate_location_hash(executor, location)

    def get_pip_location_host(self, executor: HostExecutor, venv_path: str) -> str:
        """Get the site-packages location for the host virtual environment."""
        pip_cmd = f"{venv_path}/bin/pip"
        stdout, _, exit_code = executor.execute_command(f"{pip_cmd} show pip")
        if exit_code == 0:
            for line in stdout.split("\n"):
                if line.startswith("Location:"):
                    return line.split(":", 1)[1].strip()

        # Fallback: try to determine location directly
        site_packages_cmd = f'{venv_path}/bin/python3 -c "import site; print(site.getsitepackages()[0])"'
        stdout2, _, exit_code2 = executor.execute_command(site_packages_cmd)
        if exit_code2 == 0:
            return stdout2.strip()

        return ""


if __name__ == "__main__":
    pytest.main([__file__])
