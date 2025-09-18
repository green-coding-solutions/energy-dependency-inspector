"""Test APK detector using Docker Alpine environment."""

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
            base_package_count = self._get_apk_package_count(result_base)

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

        # Get APK packages from system scope
        assert "system" in result, "Expected 'system' scope in result"
        system_result = result["system"]
        assert "packages" in system_result, "System scope should contain 'packages'"

        packages = system_result["packages"]
        apk_packages = [pkg for pkg in packages if pkg.get("type") == "apk"]
        assert len(apk_packages) > 0, "Should have found APK packages"

        # Check for expected Alpine base packages
        package_names = [pkg["name"] for pkg in apk_packages]

        # Basic Alpine should have essential packages
        expected_packages = ["musl", "busybox", "alpine-baselayout", "alpine-keys"]
        found_expected = [pkg for pkg in expected_packages if pkg in package_names]
        assert len(found_expected) > 0, f"Expected to find at least one of {expected_packages} in: {package_names}"

        # Validate dependency structure
        self.validate_dependency_structure(apk_packages)

        # APK-specific validation: check architecture in versions
        for package in apk_packages[:5]:
            version = package["version"]
            assert any(
                arch in version for arch in ["x86_64", "aarch64", "armhf", "armv7"]
            ), f"Version for {package['name']} should include architecture: {version}"
            assert package["type"] == "apk", f"Package type should be 'apk', got: {package['type']}"

        print(f"✓ Successfully detected {len(apk_packages)} APK packages")
        print("✓ Scope: system")
        print(f"✓ Sample packages: {package_names[:5]}")

    def _get_apk_package_count(self, result: Dict[str, Any]) -> int:
        """Get the count of APK packages from result."""
        if "system" not in result or "packages" not in result["system"]:
            return 0
        packages = result["system"]["packages"]
        apk_packages = [pkg for pkg in packages if pkg.get("type") == "apk"]
        return len(apk_packages)

    def _validate_apk_dependencies_extended(
        self, result: Dict[str, Any], base_count: int, installed_packages: list
    ) -> None:
        """Validate APK dependencies with additional installed packages."""
        self._validate_apk_dependencies(result)  # Basic validation first

        # Get APK packages from system scope
        system_result = result["system"]
        packages = system_result["packages"]
        apk_packages = [pkg for pkg in packages if pkg.get("type") == "apk"]
        package_names = [pkg["name"] for pkg in apk_packages]

        # Should have more packages than base Alpine
        current_count = len(apk_packages)
        assert current_count > base_count, f"Expected more than {base_count} packages, got: {current_count}"

        # Check for the packages we installed
        found_additional = [pkg for pkg in installed_packages if pkg in package_names]
        assert len(found_additional) > 0, f"Expected to find at least one of {installed_packages} in: {package_names}"

        print(f"✓ Package count increased from {base_count} to {current_count}")
        print(f"✓ Found additional packages: {found_additional}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
