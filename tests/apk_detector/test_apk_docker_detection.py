"""Test APK detector using Docker Alpine environment."""

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


class TestApkDockerDetection:
    """Test APK detector using Docker Alpine environment."""

    ALPINE_IMAGE = "alpine:3.18"

    @pytest.mark.skipif(docker is None, reason="Docker not available")
    def test_apk_detector_alpine_container(self, request: pytest.FixtureRequest) -> None:
        """Test APK detector in Alpine Linux Docker container with base and additional packages."""

        # Check for verbose output option
        verbose_output = request.config.getoption("--verbose-resolver", default=False)

        container_id = None

        try:
            container_id = self._start_alpine_container(self.ALPINE_IMAGE)
            self._wait_for_container_ready(container_id)

            executor = DockerExecutor(container_id)
            orchestrator = Orchestrator(debug=False)

            # Test base Alpine packages first
            result_base = orchestrator.resolve_dependencies(executor)

            if verbose_output:
                print("\n" + "=" * 60)
                print("BASE ALPINE DEPENDENCIES:")
                print("=" * 60)
                print(json.dumps(result_base, indent=2))
                print("=" * 60)

            self._validate_apk_dependencies(result_base)
            base_package_count = len(result_base["apk"]["dependencies"])

            # Install additional packages
            packages_to_install = ["curl", "git", "bash", "nano"]
            install_cmd = f"apk add --no-cache {' '.join(packages_to_install)}"

            _, stderr, exit_code = executor.execute_command(install_cmd)
            if exit_code != 0:
                pytest.fail(f"Failed to install additional packages: {stderr}")

            # Test with additional packages
            result_extended = orchestrator.resolve_dependencies(executor)

            if verbose_output:
                print("\n" + "=" * 60)
                print("EXTENDED ALPINE DEPENDENCIES:")
                print("=" * 60)
                print(json.dumps(result_extended, indent=2))
                print("=" * 60)

            self._validate_apk_dependencies_extended(result_extended, base_package_count, packages_to_install)

        finally:
            if container_id:
                self._cleanup_container(container_id)

    def _start_alpine_container(self, image: str) -> str:
        """Start Alpine Docker container and return its ID."""
        cmd = ["docker", "run", "-d", "--rm", image, "sleep", "300"]

        result = subprocess.run(cmd, capture_output=True, text=True, check=False)

        if result.returncode != 0:
            pytest.fail(f"Failed to start Alpine container: {result.stderr}")

        container_id = result.stdout.strip()
        return container_id

    def _wait_for_container_ready(self, container_id: str, max_wait: int = 30) -> None:
        """Wait for Alpine container to be ready."""
        client = docker.from_env()

        start_time = time.time()
        while time.time() - start_time < max_wait:
            try:
                container = client.containers.get(container_id)
                container.reload()

                if container.status == "running":
                    try:
                        executor = DockerExecutor(container_id)
                        _, _, exit_code = executor.execute_command("apk --version")
                        if exit_code == 0:
                            return
                    except Exception:  # pylint: disable=broad-exception-caught
                        pass  # Continue waiting

                time.sleep(1)

            except Exception as e:  # pylint: disable=broad-exception-caught
                print(f"Error checking container status: {e}")
                time.sleep(1)

        pytest.fail("Alpine container did not become ready within timeout")

    def _cleanup_container(self, container_id: str) -> None:
        """Stop and remove the Docker container."""
        cmd = ["docker", "stop", container_id]
        subprocess.run(cmd, capture_output=True, check=False)

    def _validate_apk_dependencies(self, result: Dict[str, Any]) -> None:
        """Validate that APK dependencies were detected correctly."""
        assert isinstance(result, dict), "Result should be a dictionary"

        # Should have apk detector results
        assert "apk" in result, f"Expected 'apk' in result keys: {list(result.keys())}"

        apk_result = result["apk"]
        assert "dependencies" in apk_result, "apk result should contain 'dependencies'"
        assert "scope" in apk_result, "apk result should contain 'scope'"

        dependencies = apk_result["dependencies"]
        assert isinstance(dependencies, dict), "Dependencies should be a dictionary"
        assert len(dependencies) > 0, "Should have detected some dependencies"

        # Check for expected Alpine base packages
        dependency_names = list(dependencies.keys())

        # Basic Alpine should have essential packages
        expected_packages = ["musl", "busybox", "alpine-baselayout", "alpine-keys"]
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

            # APK versions should include architecture
            assert any(
                arch in version for arch in ["x86_64", "aarch64", "armhf", "armv7"]
            ), f"Version for {dep_name} should include architecture: {version}"

        scope = apk_result["scope"]
        assert scope == "system", f"Scope should be 'system', got: {scope}"

        print(f"✓ Successfully detected {len(dependencies)} APK packages")
        print(f"✓ Scope: {scope}")
        print(f"✓ Sample packages: {list(dependencies.keys())[:5]}")

    def _validate_apk_dependencies_extended(
        self, result: Dict[str, Any], base_count: int, installed_packages: list
    ) -> None:
        """Validate APK dependencies with additional installed packages."""
        self._validate_apk_dependencies(result)  # Basic validation first

        apk_result = result["apk"]
        dependencies = apk_result["dependencies"]
        dependency_names = list(dependencies.keys())

        # Should have more packages than base Alpine
        assert len(dependencies) > base_count, f"Expected more than {base_count} packages, got: {len(dependencies)}"

        # Check for the packages we installed
        found_additional = [pkg for pkg in installed_packages if pkg in dependency_names]
        assert (
            len(found_additional) > 0
        ), f"Expected to find at least one of {installed_packages} in: {dependency_names}"

        print(f"✓ Package count increased from {base_count} to {len(dependencies)}")
        print(f"✓ Found additional packages: {found_additional}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
