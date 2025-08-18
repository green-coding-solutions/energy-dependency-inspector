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
    docker = None


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

        npm_result = result["npm"]
        dependencies = npm_result["dependencies"]

        # Check for expected dependencies (based on typical Node.js project structure)
        # Look for common dependencies that would be in a Node.js project
        dependency_names = list(dependencies.keys())

        # Validate that we found actual npm packages
        assert len(dependency_names) > 5, f"Expected to find multiple npm dependencies, got: {dependency_names}"

        # Check for typical Node.js/TypeScript project dependencies
        typescript_related = any(
            name
            for name in dependency_names
            if any(keyword in name.lower() for keyword in ["typescript", "@types", "ts-", "jest"])
        )
        assert typescript_related, f"Expected to find TypeScript-related dependencies in: {dependency_names}"

        # Validate dependency structure
        self.validate_dependency_structure(dependencies, sample_count=3)

        scope = npm_result["scope"]
        assert scope == "project", f"Scope should be 'project', got: {scope}"

        assert "location" in npm_result, "npm result should have location field for project scope"
        location = npm_result["location"]
        assert isinstance(location, str), "Location should be a string"
        assert len(location) > 0, "Location should not be empty"

        if "hash" in npm_result:
            hash_value = npm_result["hash"]
            assert isinstance(hash_value, str), "Hash should be a string"

        print(f"✓ Successfully detected {len(dependencies)} npm dependencies")
        print(f"✓ Scope: {scope}")
        print(f"✓ Location: {npm_result.get('location', 'N/A')}")
        hash_value = npm_result.get("hash", "")
        if hash_value:
            print(f"✓ Hash: {hash_value[:16]}...")
        else:
            print("✓ Hash: (empty - hashing may have failed in container)")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
