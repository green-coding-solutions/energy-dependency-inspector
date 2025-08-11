"""Test IF npm Docker container dependency detection."""

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


class TestIfNpmDockerDetection:
    """Test npm dependency detection in IF Docker container environment."""

    IF_DOCKER_IMAGE = "ghcr.io/green-software-foundation/if"

    @pytest.mark.skipif(docker is None, reason="Docker not available")
    def test_if_npm_docker_container_detection(self, request: pytest.FixtureRequest) -> None:
        """Test npm dependency detection inside the IF Docker container."""

        # Check for verbose output option
        verbose_output = request.config.getoption("--verbose-resolver", default=False)

        container_id = None

        try:
            container_id = self._start_if_container(self.IF_DOCKER_IMAGE)
            self._wait_for_container_ready(container_id)

            executor = DockerExecutor(container_id)
            orchestrator = Orchestrator(debug=False)

            result = orchestrator.resolve_dependencies(executor)

            if verbose_output:
                print("\n" + "=" * 60)
                print("DEPENDENCY RESOLVER OUTPUT:")
                print("=" * 60)
                print(json.dumps(result, indent=2))
                print("=" * 60)

            self._validate_if_npm_dependencies(result)

        finally:
            if container_id:
                self._cleanup_container(container_id)

    def _start_if_container(self, image: str) -> str:
        """Start the IF Docker container and return its ID."""
        cmd = ["docker", "run", "-d", "--rm", image]

        result = subprocess.run(cmd, capture_output=True, text=True, check=False)

        if result.returncode != 0:
            pytest.fail(f"Failed to start IF container: {result.stderr}")

        container_id = result.stdout.strip()
        return container_id

    def _wait_for_container_ready(self, container_id: str, max_wait: int = 60) -> None:
        """Wait for the IF container to be running and npm to be available."""
        client = docker.from_env()

        start_time = time.time()
        while time.time() - start_time < max_wait:
            try:
                container = client.containers.get(container_id)
                container.reload()

                if container.status == "running":
                    try:
                        executor = DockerExecutor(container_id)
                        _, _, exit_code = executor.execute_command("npm --version")
                        if exit_code == 0:
                            return
                    except Exception:  # pylint: disable=broad-exception-caught
                        pass  # Continue waiting

                time.sleep(2)

            except Exception as e:  # pylint: disable=broad-exception-caught
                print(f"Error checking container status: {e}")
                time.sleep(2)

        pytest.fail("IF container did not become ready within timeout")

    def _cleanup_container(self, container_id: str) -> None:
        """Stop and remove the Docker container."""
        cmd = ["docker", "stop", container_id]
        subprocess.run(cmd, capture_output=True, check=False)

    def _validate_if_npm_dependencies(self, result: Dict[str, Any]) -> None:
        """Validate that IF npm dependencies were detected correctly."""
        assert isinstance(result, dict), "Result should be a dictionary"

        # Should have npm detector results
        assert "npm" in result, f"Expected 'npm' in result keys: {list(result.keys())}"

        npm_result = result["npm"]
        assert "dependencies" in npm_result, "npm result should contain 'dependencies'"
        assert "scope" in npm_result, "npm result should contain 'scope'"

        dependencies = npm_result["dependencies"]
        assert isinstance(dependencies, dict), "Dependencies should be a dictionary"
        assert len(dependencies) > 0, "Should have detected some dependencies"

        # Check for expected IF dependencies (based on typical Node.js project structure)
        # Look for common dependencies that would be in an IF project
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

        # Validate dependency structure for a few packages
        sample_deps = list(dependencies.items())[:3]  # Check first 3 dependencies
        for dep_name, dep_info in sample_deps:
            assert isinstance(dep_info, dict), f"Dependency {dep_name} should be a dict: {dep_info}"
            assert "version" in dep_info, f"Dependency {dep_name} should have version: {dep_info}"

            version = dep_info["version"]
            assert isinstance(version, str), f"Version for {dep_name} should be a string: {version}"
            assert len(version) > 0, f"Version for {dep_name} should not be empty"

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
