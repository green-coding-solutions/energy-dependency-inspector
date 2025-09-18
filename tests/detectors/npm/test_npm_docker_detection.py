"""Test npm Docker container dependency detection."""

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


class TestNpmDockerDetection(DockerTestBase):
    """Test npm dependency detection using Docker container environment."""

    IF_DOCKER_IMAGE = "ghcr.io/green-software-foundation/if"

    @pytest.mark.skipif(docker is None, reason="Docker not available")
    def test_npm_docker_container_detection(self, request: pytest.FixtureRequest) -> None:
        """Test npm dependency detection inside a Docker container."""

        verbose_output = self.setup_verbose_output(request)
        container_id = None

        try:
            container_id = self.start_container(self.IF_DOCKER_IMAGE, additional_args=[])
            self.wait_for_container_ready(container_id, "npm --version", max_wait=60)

            executor = DockerExecutor(container_id)
            orchestrator = Orchestrator(debug=False, skip_system_scope=True)

            result = orchestrator.resolve_dependencies(executor)

            if verbose_output:
                self.print_verbose_results("DEPENDENCY RESOLVER OUTPUT:", result)

            self._validate_npm_dependencies(result)

        finally:
            if container_id:
                self.cleanup_container(container_id)

    def _validate_npm_dependencies(self, result: Dict[str, Any]) -> None:
        """Validate that npm dependencies were detected correctly."""
        self.validate_basic_structure(result, "npm")

        # Get npm packages from project scope
        assert "project" in result, "Expected 'project' scope in result"
        project_result = result["project"]
        assert "packages" in project_result, "Project scope should contain 'packages'"

        packages = project_result["packages"]
        npm_packages = [pkg for pkg in packages if pkg.get("type") == "npm"]
        assert len(npm_packages) > 0, "Should have found npm packages"

        # Check for expected dependencies (based on typical Node.js project structure)
        package_names = [pkg["name"] for pkg in npm_packages]

        # Validate that we found actual npm packages
        assert len(package_names) > 5, f"Expected to find multiple npm dependencies, got: {package_names}"

        # Check for typical Node.js/TypeScript project dependencies
        typescript_related = any(
            name
            for name in package_names
            if any(keyword in name.lower() for keyword in ["typescript", "@types", "ts-", "jest"])
        )
        assert typescript_related, f"Expected to find TypeScript-related dependencies in: {package_names}"

        # Validate dependency structure
        self.validate_dependency_structure(npm_packages, sample_count=3)

        # Should have location metadata
        assert "npm" in project_result, "Project scope should contain npm metadata"
        npm_metadata = project_result["npm"]
        assert "location" in npm_metadata, "npm metadata should have location field for project scope"
        location = npm_metadata["location"]
        assert isinstance(location, str), "Location should be a string"
        assert len(location) > 0, "Location should not be empty"

        if "hash" in npm_metadata:
            hash_value = npm_metadata["hash"]
            assert isinstance(hash_value, str), "Hash should be a string"

        print(f"✓ Successfully detected {len(npm_packages)} npm dependencies")
        print("✓ Scope: project")
        print(f"✓ Location: {npm_metadata.get('location', 'N/A')}")
        hash_value = npm_metadata.get("hash", "")
        if hash_value:
            print(f"✓ Hash: {hash_value[:16]}...")
        else:
            print("✓ Hash: (empty - hashing may have failed in container)")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
