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
    docker = None


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
                self.print_verbose_results("EXTENDED UBUNTU DEPENDENCIES:", result_extended)

            self._validate_dpkg_dependencies_extended(result_extended, base_package_count, packages_to_install)

            # Validate hash coverage once for the final extended package set
            final_dependencies = result_extended["dpkg"]["dependencies"]
            self._validate_hash_coverage(final_dependencies)

        finally:
            if container_id:
                self.cleanup_container(container_id)

    def _validate_dpkg_dependencies(self, result: Dict[str, Any]) -> None:
        """Validate that DPKG dependencies were detected correctly."""
        self.validate_basic_structure(result, "dpkg")

        dpkg_result = result["dpkg"]
        dependencies = dpkg_result["dependencies"]

        # Check for expected Ubuntu base packages
        dependency_names = list(dependencies.keys())

        # Basic Ubuntu should have essential packages
        expected_packages = ["base-files", "libc6", "bash", "coreutils", "dpkg"]
        found_expected = [pkg for pkg in expected_packages if pkg in dependency_names]
        assert len(found_expected) > 0, f"Expected to find at least one of {expected_packages} in: {dependency_names}"

        # Validate dependency structure
        self.validate_dependency_structure(dependencies)

        # DPKG-specific validation: check architecture in versions and hashes
        sample_deps = list(dependencies.items())[:5]
        for dep_name, dep_info in sample_deps:
            version = dep_info["version"]
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

    def _validate_hash_coverage(self, dependencies: Dict[str, Any]) -> None:
        """Validate that all packages have hashes."""
        total_packages = len(dependencies)
        packages_with_hash = sum(1 for dep_info in dependencies.values() if "hash" in dep_info)

        print(f"✓ Hash coverage: {packages_with_hash}/{total_packages} packages have hashes")

        assert packages_with_hash == total_packages, (
            f"Expected all {total_packages} packages to have hashes, but only {packages_with_hash} have hashes. "
            f"Missing hashes suggest the md5sums file handling may not be working correctly."
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
