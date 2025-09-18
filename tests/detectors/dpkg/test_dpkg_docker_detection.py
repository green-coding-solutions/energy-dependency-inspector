"""Test DPKG detector using Docker Debian/Ubuntu environment."""

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


class TestDpkgDockerDetection(DockerTestBase):
    """Test DPKG detector using Docker Debian/Ubuntu environment."""

    UBUNTU_IMAGE = "ubuntu:22.04"

    @pytest.mark.skipif(docker is None, reason="Docker not available")
    def test_dpkg_detector_ubuntu_container(self, request: pytest.FixtureRequest) -> None:
        """Test DPKG detector in Ubuntu Linux Docker container with base and additional packages."""

        verbose_output = self.setup_verbose_output(request)
        container_id = None

        try:
            container_id = self.start_container(self.UBUNTU_IMAGE)
            self.wait_for_container_ready(container_id, "dpkg-query --version")

            executor = DockerExecutor(container_id)
            orchestrator = Orchestrator(debug=False)

            # Test base Ubuntu packages first
            result_base = orchestrator.resolve_dependencies(executor)

            if verbose_output:
                self.print_verbose_results("BASE UBUNTU DEPENDENCIES:", result_base)

            self._validate_dpkg_dependencies(result_base)
            base_package_count = self._get_dpkg_package_count(result_base)

            # Install additional packages
            packages_to_install = ["curl", "vim", "wget", "tree"]
            install_cmd = f"apt-get update && apt-get install -y {' '.join(packages_to_install)}"

            _, stderr, exit_code = executor.execute_command(install_cmd)
            if exit_code != 0:
                pytest.fail(f"Failed to install additional packages: {stderr}")

            # Test with additional packages
            result_extended = orchestrator.resolve_dependencies(executor)

            if verbose_output:
                self.print_verbose_results("EXTENDED UBUNTU DEPENDENCIES:", result_extended)

            self._validate_dpkg_dependencies_extended(result_extended, base_package_count, packages_to_install)

            # Validate hash coverage once for the final extended package set
            final_packages = self._get_dpkg_packages(result_extended)
            self._validate_hash_coverage(final_packages)

        finally:
            if container_id:
                self.cleanup_container(container_id)

    def _get_dpkg_packages(self, result: Dict[str, Any]) -> list:
        """Get DPKG packages from result."""
        if "system" not in result or "packages" not in result["system"]:
            return []
        packages = result["system"]["packages"]
        return [pkg for pkg in packages if pkg.get("type") == "dpkg"]

    def _get_dpkg_package_count(self, result: Dict[str, Any]) -> int:
        """Get the count of DPKG packages from result."""
        return len(self._get_dpkg_packages(result))

    def _validate_dpkg_dependencies(self, result: Dict[str, Any]) -> None:
        """Validate that DPKG dependencies were detected correctly."""
        self.validate_basic_structure(result, "dpkg")

        # Get DPKG packages from system scope
        assert "system" in result, "Expected 'system' scope in result"
        system_result = result["system"]
        assert "packages" in system_result, "System scope should contain 'packages'"

        packages = system_result["packages"]
        dpkg_packages = [pkg for pkg in packages if pkg.get("type") == "dpkg"]
        assert len(dpkg_packages) > 0, "Should have found DPKG packages"

        # Check for expected Ubuntu base packages
        package_names = [pkg["name"] for pkg in dpkg_packages]

        # Basic Ubuntu should have essential packages
        expected_packages = ["base-files", "libc6", "bash", "coreutils", "dpkg"]
        found_expected = [pkg for pkg in expected_packages if pkg in package_names]
        assert len(found_expected) > 0, f"Expected to find at least one of {expected_packages} in: {package_names}"

        # Validate dependency structure
        self.validate_dependency_structure(dpkg_packages)

        # DPKG-specific validation: check architecture in versions and hashes
        for package in dpkg_packages[:5]:
            version = package["version"]
            assert any(
                arch in version for arch in ["amd64", "all", "arm64", "armhf", "i386"]
            ), f"Version for {package['name']} should include architecture: {version}"
            assert package["type"] == "dpkg", f"Package type should be 'dpkg', got: {package['type']}"

            # Some packages may have hashes
            if "hash" in package:
                hash_value = package["hash"]
                assert isinstance(hash_value, str), f"Hash for {package['name']} should be a string: {hash_value}"
                assert len(hash_value) == 64, f"Hash for {package['name']} should be 64 chars (SHA256): {hash_value}"

        print(f"✓ Successfully detected {len(dpkg_packages)} DPKG packages")
        print("✓ Scope: system")
        print(f"✓ Sample packages: {package_names[:5]}")

    def _validate_dpkg_dependencies_extended(
        self, result: Dict[str, Any], base_count: int, installed_packages: list
    ) -> None:
        """Validate DPKG dependencies with additional installed packages."""
        self._validate_dpkg_dependencies(result)  # Basic validation first

        # Get DPKG packages from system scope
        dpkg_packages = self._get_dpkg_packages(result)
        package_names = [pkg["name"] for pkg in dpkg_packages]

        # Should have more packages than base Ubuntu
        current_count = len(dpkg_packages)
        assert current_count > base_count, f"Expected more than {base_count} packages, got: {current_count}"

        # Check for the packages we installed (may have different names or be dependencies)
        # Look for related packages since apt installs dependencies too
        expected_related = ["curl", "vim", "wget", "tree", "libcurl"]
        found_related = [pkg for pkg in package_names if any(exp in pkg for exp in expected_related)]
        assert (
            len(found_related) > 0
        ), f"Expected to find packages related to {installed_packages} in: {package_names[:20]}..."

        print(f"✓ Package count increased from {base_count} to {current_count}")
        print(f"✓ Found related packages: {found_related[:10]}")

    def _validate_hash_coverage(self, packages: list) -> None:
        """Validate that all packages have hashes."""
        total_packages = len(packages)
        packages_with_hash = sum(1 for pkg in packages if "hash" in pkg)

        print(f"✓ Hash coverage: {packages_with_hash}/{total_packages} packages have hashes")

        assert packages_with_hash == total_packages, (
            f"Expected all {total_packages} packages to have hashes, but only {packages_with_hash} have hashes. "
            f"Missing hashes suggest the md5sums file handling may not be working correctly."
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
