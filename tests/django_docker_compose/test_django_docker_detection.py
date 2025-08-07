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

from executors import DockerExecutor, DockerComposeExecutor
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
    def test_django_docker_container_pip_detection(
        self, compose_project_path: str, request: pytest.FixtureRequest
    ) -> None:
        """Test pip dependency detection inside a Docker container from a compose stack."""
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

    @pytest.mark.skipif(docker is None, reason="Docker not available")
    def test_django_docker_compose_stack_detection(
        self, compose_project_path: str, request: pytest.FixtureRequest
    ) -> None:
        """Test Docker Compose stack detection using DockerComposeExecutor."""
        compose_project_name = "dependency-resolver-django-test"

        # Check for verbose output option
        verbose_output = request.config.getoption("--verbose-resolver", default=False)

        try:
            # Start Docker compose stack
            self._start_compose_stack(compose_project_path, compose_project_name)

            # Wait for containers to be ready (just check that they exist)
            self._wait_for_compose_stack(compose_project_name)

            # Test Docker Compose stack detection
            executor = DockerComposeExecutor(compose_project_name)
            resolver = DependencyResolver(debug=False)

            result = resolver.resolve_dependencies(executor)

            # Print resolver output if requested
            if verbose_output:
                print("\n" + "=" * 60)
                print("DOCKER COMPOSE STACK DETECTION OUTPUT:")
                print("=" * 60)
                print(json.dumps(result, indent=2, sort_keys=True))
                print("=" * 60)

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

    def _validate_docker_compose_dependencies(self, result: Dict[str, Any]) -> None:
        """Validate that Docker Compose stack dependencies were detected correctly."""
        assert isinstance(result, dict), "Result should be a dictionary"

        # Should have docker-compose detector results
        assert "docker-compose" in result, f"Expected 'docker-compose' in result keys: {list(result.keys())}"

        compose_result = result["docker-compose"]
        assert "dependencies" in compose_result, "docker-compose result should contain 'dependencies'"
        assert "location" in compose_result, "docker-compose result should contain 'location'"
        assert compose_result["location"] == "global", "docker-compose location should be 'global'"

        dependencies = compose_result["dependencies"]
        assert isinstance(dependencies, dict), "Dependencies should be a dictionary"
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
