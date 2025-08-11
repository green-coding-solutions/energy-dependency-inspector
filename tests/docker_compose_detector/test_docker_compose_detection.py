"""Test Docker Compose stack dependency detection."""

import os
import subprocess
import sys
import time
from typing import Dict, Any

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import pytest

from executors import DockerComposeExecutor
from core.orchestrator import Orchestrator
from tests.common.docker_test_base import DockerTestBase

try:
    import docker
except ImportError:
    docker = None


class TestDockerComposeDetection(DockerTestBase):
    """Test Docker Compose stack dependency detection."""

    @pytest.fixture
    def compose_project_path(self) -> str:
        """Get path to the Docker compose project."""
        return os.path.dirname(os.path.abspath(__file__))

    @pytest.mark.skipif(docker is None, reason="Docker not available")
    def test_docker_compose_stack_detection(self, compose_project_path: str, request: pytest.FixtureRequest) -> None:
        """Test Docker Compose stack detection using Django as an example."""
        compose_project_name = "dependency-resolver-compose-test"

        verbose_output = self.setup_verbose_output(request)

        try:
            # Start Docker compose stack
            self._start_compose_stack(compose_project_path, compose_project_name)

            # Wait for containers to be ready (just check that they exist)
            self._wait_for_compose_stack(compose_project_name)

            # Test Docker Compose stack detection
            executor = DockerComposeExecutor(compose_project_name)
            orchestrator = Orchestrator(debug=False)

            result = orchestrator.resolve_dependencies(executor)

            # Print resolver output if requested
            if verbose_output:
                self.print_verbose_results("DOCKER COMPOSE STACK DETECTION OUTPUT:", result)

            # Validate results
            self._validate_docker_compose_dependencies(result)

        finally:
            # Clean up compose stack
            self._cleanup_compose_stack(compose_project_path, compose_project_name)

    def _start_compose_stack(self, compose_path: str, project_name: str) -> None:
        """Start the Docker compose stack."""
        cmd = [
            "docker",
            "compose",
            "-f",
            os.path.join(compose_path, "docker-compose.yml"),
            "-p",
            project_name,
            "up",
            "-d",
            "--build",
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, cwd=compose_path, check=False)

        if result.returncode != 0:
            pytest.fail(f"Failed to start compose stack: {result.stderr}")

    def _wait_for_compose_stack(self, project_name: str, max_wait: int = 60) -> None:
        """Wait for Docker Compose stack containers to be running."""
        client = docker.from_env()

        start_time = time.time()
        while time.time() - start_time < max_wait:
            try:
                # Look for containers in the compose project
                containers = client.containers.list(filters={"label": [f"com.docker.compose.project={project_name}"]})

                if len(containers) >= 2:  # Expecting web and db containers
                    running_count = sum(1 for c in containers if c.status == "running")
                    if running_count >= 2:
                        return

                time.sleep(2)

            except Exception as e:  # pylint: disable=broad-exception-caught
                print(f"Error checking compose stack status: {e}")
                time.sleep(2)

        pytest.fail("Docker Compose stack did not become ready within timeout")

    def _cleanup_compose_stack(self, compose_path: str, project_name: str) -> None:
        """Clean up the Docker compose stack."""
        cmd = [
            "docker",
            "compose",
            "-f",
            os.path.join(compose_path, "docker-compose.yml"),
            "-p",
            project_name,
            "down",
            "-v",
            "--remove-orphans",
        ]

        subprocess.run(cmd, capture_output=True, cwd=compose_path, check=False)

    def _validate_docker_compose_dependencies(self, result: Dict[str, Any]) -> None:
        """Validate that Docker Compose stack dependencies were detected correctly."""
        self.validate_basic_structure(result, "docker-compose")

        compose_result = result["docker-compose"]
        dependencies = compose_result["dependencies"]

        assert compose_result["scope"] == "compose", "docker-compose scope should be 'compose'"
        assert len(dependencies) >= 2, f"Should have at least 2 services (web, db): {list(dependencies.keys())}"

        # Check for expected service names
        service_names = list(dependencies.keys())
        assert "web" in service_names, f"Expected 'web' service in dependencies: {service_names}"
        assert "db" in service_names, f"Expected 'db' service in dependencies: {service_names}"

        # Validate web service dependency structure
        web_dep = dependencies["web"]
        assert "version" in web_dep, f"Web service should have version: {web_dep}"
        assert "hash" in web_dep, f"Web service should have hash: {web_dep}"

        # Validate db service dependency structure
        db_dep = dependencies["db"]
        assert "version" in db_dep, f"DB service should have version: {db_dep}"
        assert "hash" in db_dep, f"DB service should have hash: {db_dep}"

        # Validate version and hash formats
        web_version = web_dep["version"]
        web_hash = web_dep["hash"]
        db_version = db_dep["version"]
        db_hash = db_dep["hash"]

        assert isinstance(web_version, str) and len(web_version) > 0, "Web version should be non-empty string"
        assert isinstance(web_hash, str) and len(web_hash) > 0, "Web hash should be non-empty string"
        assert isinstance(db_version, str) and len(db_version) > 0, "DB version should be non-empty string"
        assert isinstance(db_hash, str) and len(db_hash) > 0, "DB hash should be non-empty string"

        # Validate hash format (should start with sha256:)
        assert web_hash.startswith("sha256:"), f"Web hash should start with 'sha256:': {web_hash}"
        assert db_hash.startswith("sha256:"), f"DB hash should start with 'sha256:': {db_hash}"
        assert len(web_hash) == 71, f"Web hash should be 71 chars (sha256: + 64 hex): {web_hash}"  # sha256: + 64 chars
        assert len(db_hash) == 71, f"DB hash should be 71 chars (sha256: + 64 hex): {db_hash}"

        # Validate expected image versions
        assert "postgres" in db_version.lower(), f"DB version should contain 'postgres': {db_version}"

        print(f"✓ Successfully detected Docker Compose stack services: {', '.join(service_names)}")
        print(f"✓ Web service: {web_version} (hash: {web_hash[:19]}...)")
        print(f"✓ DB service: {db_version} (hash: {db_hash[:19]}...)")
        print(f"✓ Total services found: {len(dependencies)}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
