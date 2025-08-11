"""Test DPKG detector using Docker Debian/Ubuntu environment."""

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


class TestDpkgDockerDetection:
    """Test DPKG detector using Docker Debian/Ubuntu environment."""

    UBUNTU_IMAGE = "ubuntu:22.04"

    @pytest.mark.skipif(docker is None, reason="Docker not available")
    def test_dpkg_detector_ubuntu_container(self, request: pytest.FixtureRequest) -> None:
        """Test DPKG detector in Ubuntu Linux Docker container with base and additional packages."""

        # Check for verbose output option
        verbose_output = request.config.getoption("--verbose-resolver", default=False)

        container_id = None

        try:
            container_id = self._start_ubuntu_container(self.UBUNTU_IMAGE)
            self._wait_for_container_ready(container_id)

            executor = DockerExecutor(container_id)
            orchestrator = Orchestrator(debug=False)

            # Test base Ubuntu packages first
            result_base = orchestrator.resolve_dependencies(executor)

            if verbose_output:
                print("\n" + "=" * 60)
                print("BASE UBUNTU DEPENDENCIES:")
                print("=" * 60)
                print(json.dumps(result_base, indent=2))
                print("=" * 60)

            self._validate_dpkg_dependencies(result_base)
            base_package_count = len(result_base["dpkg"]["dependencies"])

            # Install additional packages
            packages_to_install = ["curl", "vim", "wget", "tree"]
            install_cmd = f"apt-get update && apt-get install -y {' '.join(packages_to_install)}"

            _, stderr, exit_code = executor.execute_command(install_cmd)
            if exit_code != 0:
                pytest.fail(f"Failed to install additional packages: {stderr}")

            # Test with additional packages
            result_extended = orchestrator.resolve_dependencies(executor)

            if verbose_output:
                print("\n" + "=" * 60)
                print("EXTENDED UBUNTU DEPENDENCIES:")
                print("=" * 60)
                print(json.dumps(result_extended, indent=2))
                print("=" * 60)

            self._validate_dpkg_dependencies_extended(result_extended, base_package_count, packages_to_install)

        finally:
            if container_id:
                self._cleanup_container(container_id)

    def _start_ubuntu_container(self, image: str) -> str:
        """Start Ubuntu Docker container and return its ID."""
        cmd = ["docker", "run", "-d", "--rm", image, "sleep", "300"]

        result = subprocess.run(cmd, capture_output=True, text=True, check=False)

        if result.returncode != 0:
            pytest.fail(f"Failed to start Ubuntu container: {result.stderr}")

        container_id = result.stdout.strip()
        return container_id

    def _wait_for_container_ready(self, container_id: str, max_wait: int = 30) -> None:
        """Wait for Ubuntu container to be ready."""
        client = docker.from_env()

        start_time = time.time()
        while time.time() - start_time < max_wait:
            try:
                container = client.containers.get(container_id)
                container.reload()

                if container.status == "running":
                    try:
                        executor = DockerExecutor(container_id)
                        _, _, exit_code = executor.execute_command("dpkg-query --version")
                        if exit_code == 0:
                            return
                    except Exception:  # pylint: disable=broad-exception-caught
                        pass  # Continue waiting

                time.sleep(1)

            except Exception as e:  # pylint: disable=broad-exception-caught
                print(f"Error checking container status: {e}")
                time.sleep(1)

        pytest.fail("Ubuntu container did not become ready within timeout")

    def _cleanup_container(self, container_id: str) -> None:
        """Stop and remove the Docker container."""
        cmd = ["docker", "stop", container_id]
        subprocess.run(cmd, capture_output=True, check=False)

    def _validate_dpkg_dependencies(self, result: Dict[str, Any]) -> None:
        """Validate that DPKG dependencies were detected correctly."""
        assert isinstance(result, dict), "Result should be a dictionary"

        # Should have dpkg detector results
        assert "dpkg" in result, f"Expected 'dpkg' in result keys: {list(result.keys())}"

        dpkg_result = result["dpkg"]
        assert "dependencies" in dpkg_result, "dpkg result should contain 'dependencies'"
        assert "scope" in dpkg_result, "dpkg result should contain 'scope'"

        dependencies = dpkg_result["dependencies"]
        assert isinstance(dependencies, dict), "Dependencies should be a dictionary"
        assert len(dependencies) > 0, "Should have detected some dependencies"

        # Check for expected Ubuntu base packages
        dependency_names = list(dependencies.keys())

        # Basic Ubuntu should have essential packages
        expected_packages = ["base-files", "libc6", "bash", "coreutils", "dpkg"]
        found_expected = [pkg for pkg in expected_packages if pkg in dependency_names]
        assert len(found_expected) > 0, f"Expected to find at least one of {expected_packages} in: {dependency_names}"

        # Validate dependency structure
        sample_deps = list(dependencies.items())[:5]  # Check first 5 dependencies
        for dep_name, dep_info in sample_deps:
            assert isinstance(dep_info, dict), f"Dependency {dep_name} should be a dict: {dep_info}"
            assert "version" in dep_info, f"Dependency {dep_name} should have version: {dep_info}"

            version = dep_info["version"]
            assert isinstance(version, str), f"Version for {dep_name} should be a string: {version}"
            assert len(version) > 0, f"Version for {dep_name} should not be empty"

            # DPKG versions should include architecture
            assert any(
                arch in version for arch in ["amd64", "all", "arm64", "armhf", "i386"]
            ), f"Version for {dep_name} should include architecture: {version}"

            # Some packages may have hashes
            if "hash" in dep_info:
                hash_value = dep_info["hash"]
                assert isinstance(hash_value, str), f"Hash for {dep_name} should be a string: {hash_value}"
                assert len(hash_value) == 64, f"Hash for {dep_name} should be 64 chars (SHA256): {hash_value}"

        scope = dpkg_result["scope"]
        assert scope == "system", f"Scope should be 'system', got: {scope}"

        print(f"✓ Successfully detected {len(dependencies)} DPKG packages")
        print(f"✓ Scope: {scope}")
        print(f"✓ Sample packages: {list(dependencies.keys())[:5]}")

    def _validate_dpkg_dependencies_extended(
        self, result: Dict[str, Any], base_count: int, installed_packages: list
    ) -> None:
        """Validate DPKG dependencies with additional installed packages."""
        self._validate_dpkg_dependencies(result)  # Basic validation first

        dpkg_result = result["dpkg"]
        dependencies = dpkg_result["dependencies"]
        dependency_names = list(dependencies.keys())

        # Should have more packages than base Ubuntu
        assert len(dependencies) > base_count, f"Expected more than {base_count} packages, got: {len(dependencies)}"

        # Check for the packages we installed (may have different names or be dependencies)
        # Look for related packages since apt installs dependencies too
        expected_related = ["curl", "vim", "wget", "tree", "libcurl"]
        found_related = [pkg for pkg in dependency_names if any(exp in pkg for exp in expected_related)]
        assert (
            len(found_related) > 0
        ), f"Expected to find packages related to {installed_packages} in: {dependency_names[:20]}..."

        print(f"✓ Package count increased from {base_count} to {len(dependencies)}")
        print(f"✓ Found related packages: {found_related[:10]}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
