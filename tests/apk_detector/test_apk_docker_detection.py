"""Test APK detector using Docker Alpine environment."""

import os
import sys
from typing import Dict, Any

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import pytest

from executors import DockerExecutor
from core.orchestrator import Orchestrator
from tests.common.docker_test_base import DockerTestBase

try:
    import docker
except ImportError:
    docker = None


class TestApkDockerDetection(DockerTestBase):
    """Test APK detector using Docker Alpine environment."""

    ALPINE_IMAGE = "alpine:3.18"

    @pytest.mark.skipif(docker is None, reason="Docker not available")
    def test_apk_detector_alpine_container(self, request: pytest.FixtureRequest) -> None:
        """Test APK detector in Alpine Linux Docker container with base and additional packages."""

        verbose_output = self.setup_verbose_output(request)
        container_id = None

        try:
            container_id = self.start_container(self.ALPINE_IMAGE)
            self.wait_for_container_ready(container_id, "apk --version")

            executor = DockerExecutor(container_id)
            orchestrator = Orchestrator(debug=False)

            # Test base Alpine packages first
            result_base = orchestrator.resolve_dependencies(executor)

            if verbose_output:
                self.print_verbose_results("BASE ALPINE DEPENDENCIES:", result_base)

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
                self.print_verbose_results("EXTENDED ALPINE DEPENDENCIES:", result_extended)

            self._validate_apk_dependencies_extended(result_extended, base_package_count, packages_to_install)

        finally:
            if container_id:
                self.cleanup_container(container_id)

    def _validate_apk_dependencies(self, result: Dict[str, Any]) -> None:
        """Validate that APK dependencies were detected correctly."""
        self.validate_basic_structure(result, "apk")

        apk_result = result["apk"]
        dependencies = apk_result["dependencies"]

        # Check for expected Alpine base packages
        dependency_names = list(dependencies.keys())

        # Basic Alpine should have essential packages
        expected_packages = ["musl", "busybox", "alpine-baselayout", "alpine-keys"]
        found_expected = [pkg for pkg in expected_packages if pkg in dependency_names]
        assert len(found_expected) > 0, f"Expected to find at least one of {expected_packages} in: {dependency_names}"

        # Validate dependency structure
        self.validate_dependency_structure(dependencies)

        # APK-specific validation: check architecture in versions
        sample_deps = list(dependencies.items())[:5]
        for dep_name, dep_info in sample_deps:
            version = dep_info["version"]
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
