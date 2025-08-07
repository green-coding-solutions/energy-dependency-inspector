"""Test Django Docker compose dependency detection."""

import json
import os
import subprocess
import sys
import time
from typing import Dict, Any

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import pytest

from core.executor import DockerExecutor
from core.resolver import DependencyResolver

try:
    import docker
except ImportError:
    docker = None


class TestDjangoDockerDetection:
    """Test dependency detection in Django Docker compose environment."""

    @pytest.fixture
    def compose_project_path(self) -> str:
        """Get path to the Django compose project."""
        return os.path.dirname(os.path.abspath(__file__))

    @pytest.mark.skipif(docker is None, reason="Docker not available")
    def test_django_docker_compose_dependency_detection(
        self, compose_project_path: str, request: pytest.FixtureRequest
    ) -> None:
        """Test dependency detection in a Django Docker compose stack."""
        compose_project_name = "dependency-resolver-django-test"

        # Check for verbose output option
        verbose_output = request.config.getoption("--verbose-resolver", default=False)

        try:
            # Start Docker compose stack
            self._start_compose_stack(compose_project_path, compose_project_name)

            # Wait for container to be ready
            web_container_id = self._wait_for_web_container(compose_project_name)

            # Test dependency detection
            executor = DockerExecutor(web_container_id)
            resolver = DependencyResolver(debug=False)

            result = resolver.resolve_dependencies(executor)

            # Print resolver output if requested
            if verbose_output:
                print("\n" + "=" * 60)
                print("DEPENDENCY RESOLVER OUTPUT:")
                print("=" * 60)
                print(json.dumps(result, indent=2, sort_keys=True))
                print("=" * 60)

            # Validate results
            self._validate_django_dependencies(result)

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

    def _wait_for_web_container(self, project_name: str, max_wait: int = 60) -> str:
        """Wait for web container to be running and return its ID."""
        client = docker.from_env()

        start_time = time.time()
        while time.time() - start_time < max_wait:
            try:
                # Look for the web container
                containers = client.containers.list(
                    filters={"label": [f"com.docker.compose.project={project_name}", "com.docker.compose.service=web"]}
                )

                if containers:
                    container = containers[0]
                    container.reload()

                    if container.status == "running":
                        # Additional check: ensure pip is available
                        try:
                            executor = DockerExecutor(container.id)
                            _, _, exit_code = executor.execute_command("pip --version")
                            if exit_code == 0:
                                return str(container.id)
                        except Exception:  # pylint: disable=broad-exception-caught
                            pass  # Continue waiting

                time.sleep(2)

            except Exception as e:  # pylint: disable=broad-exception-caught
                print(f"Error checking container status: {e}")
                time.sleep(2)

        pytest.fail("Web container did not become ready within timeout")
        return ""  # unreachable but satisfies mypy

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

    def _validate_django_dependencies(self, result: Dict[str, Any]) -> None:
        """Validate that Django dependencies were detected correctly."""
        assert isinstance(result, dict), "Result should be a dictionary"

        # Should have pip detector results
        assert "pip" in result, f"Expected 'pip' in result keys: {list(result.keys())}"

        pip_result = result["pip"]
        assert "dependencies" in pip_result, "pip result should contain 'dependencies'"

        dependencies = pip_result["dependencies"]
        assert isinstance(dependencies, dict), "Dependencies should be a dictionary"
        assert len(dependencies) > 0, "Should have detected some dependencies"

        # Check for Django
        django_found = any("django" in dep_name.lower() for dep_name in dependencies.keys())
        assert django_found, f"Expected to find Django in dependencies: {list(dependencies.keys())}"

        # Check for psycopg2
        psycopg2_found = any("psycopg2" in dep_name.lower() for dep_name in dependencies.keys())
        assert psycopg2_found, f"Expected to find psycopg2 in dependencies: {list(dependencies.keys())}"

        # Validate dependency structure for Django
        django_deps = [(name, dep) for name, dep in dependencies.items() if "django" in name.lower()]
        assert len(django_deps) > 0, "Should have at least one Django dependency"

        _, django_dep = django_deps[0]
        assert "version" in django_dep, f"Django dependency should have version: {django_dep}"

        # Check if hash is in dependency or in the pip_result (location hash for all pip dependencies)
        if "hash" not in django_dep and "hash" in pip_result:
            # Global hash for all pip dependencies location
            location_hash = pip_result["hash"]
        else:
            location_hash = django_dep.get("hash")

        assert (
            location_hash is not None
        ), f"Django dependency should have location hash somewhere: pip_result={pip_result}"
        assert "location" in pip_result, "pip result should have location field"

        # Validate version format (should be semver-like)
        version = django_dep["version"]
        assert isinstance(version, str), "Version should be a string"
        assert len(version) > 0, "Version should not be empty"

        print(f"✓ Successfully detected Django v{version} and other pip dependencies")
        print(f"✓ Total dependencies found: {len(dependencies)}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
