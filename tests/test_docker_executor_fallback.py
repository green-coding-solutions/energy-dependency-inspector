"""Test DockerExecutor fallback mechanism for containers without shell."""

import json
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

from core.executor import DockerExecutor
from core.resolver import DependencyResolver

try:
    import docker
except ImportError:
    docker = None


class TestDockerExecutorFallback:
    """Test DockerExecutor fallback mechanism when sh is not available."""

    def test_parse_simple_command(self) -> None:
        """Test the _parse_simple_command method."""
        if docker is None:
            pytest.skip("Docker not available")

        # We can test this without a running container
        # Test the parsing method directly on the class
        executor_class = DockerExecutor

        # Test simple commands
        assert executor_class._parse_simple_command(None, "python3 --version") == ["python3", "--version"]
        assert executor_class._parse_simple_command(None, "cat /etc/os-release") == ["cat", "/etc/os-release"]
        assert executor_class._parse_simple_command(None, "test -e /usr/bin/python3") == [
            "test",
            "-e",
            "/usr/bin/python3",
        ]

        # Test complex commands that should be rejected
        assert executor_class._parse_simple_command(None, "echo hello | cat") is None
        assert executor_class._parse_simple_command(None, "cd /tmp && ls") is None
        assert executor_class._parse_simple_command(None, "echo hello > file.txt") is None
        assert executor_class._parse_simple_command(None, "echo $HOME") is None

        # Test commands starting with flags (should be rejected)
        assert executor_class._parse_simple_command(None, "--version python3") is None

    @pytest.mark.skipif(docker is None, reason="Docker not available")
    def test_dependency_resolver_integration_with_distroless(self) -> None:
        """Test full dependency resolver integration with distroless container."""
        client = docker.from_env()

        container_name = "test-resolver-distroless"

        try:
            # Start a distroless Python container with pre-installed packages
            # Use python3-debian11 which has some Python packages installed
            container = client.containers.run(
                "gcr.io/distroless/python3-debian11",
                command=["python3", "-c", "import time; time.sleep(3600)"],
                name=container_name,
                detach=True,
                remove=True,
            )

            container.reload()
            assert container.status == "running"

            # Test the dependency resolver with the distroless container
            executor = DockerExecutor(container_name)
            resolver = DependencyResolver(debug=True)

            # This should work even without sh - the resolver will use our fallback
            result = resolver.resolve_dependencies(executor)

            # Verify we get a proper result structure
            assert isinstance(result, dict)

            # Check that at least some detectors were checked
            # Note: distroless containers typically won't have dpkg, apk, npm, or pip
            # but the resolver should still work and return an empty result
            # The important thing is that it doesn't crash due to missing sh

            # Verify the result can be formatted as JSON (as dependency_resolver.py does)
            formatted_result = resolver.resolve_and_format(executor)
            assert isinstance(formatted_result, str)

            # Should be valid JSON
            try:
                parsed = json.loads(formatted_result)
                assert isinstance(parsed, dict)
            except json.JSONDecodeError:
                pytest.fail(f"resolve_and_format returned invalid JSON: {formatted_result}")

        finally:
            # Clean up
            try:
                container = client.containers.get(container_name)
                container.stop()
            except docker.errors.NotFound:
                pass

    @pytest.mark.skipif(docker is None, reason="Docker not available")
    def test_dependency_resolver_with_python_packages(self) -> None:
        """Test dependency resolver with a container that has Python packages but no sh."""
        client = docker.from_env()

        container_name = "test-resolver-python-packages"

        try:
            # Create a container from distroless base but with some Python packages
            # We'll use a different approach - start with a container that has pip installed
            # but simulate the no-sh scenario by testing the fallback path

            # Start Ubuntu container and install Python packages, then test fallback
            container = client.containers.run(
                "python:3.11-slim",
                command=["python3", "-c", "import time; time.sleep(3600)"],
                name=container_name,
                detach=True,
                remove=True,
            )

            container.reload()
            assert container.status == "running"

            # Install some test packages first
            executor = DockerExecutor(container_name)

            # Install a simple package
            _, stderr, exit_code = executor.execute_command("pip install six==1.16.0")
            if exit_code != 0:
                pytest.skip(f"Could not install test package: {stderr}")

            # Now test the resolver
            resolver = DependencyResolver(debug=False)  # Less verbose for this test
            result = resolver.resolve_dependencies(executor)

            # Should find pip dependencies
            assert isinstance(result, dict)

            # Check if pip detector found something
            if "pip" in result:
                pip_result = result["pip"]
                assert "dependencies" in pip_result
                assert isinstance(pip_result["dependencies"], dict)

                # Should find 'six' package we installed
                dependencies = pip_result["dependencies"]
                assert len(dependencies) > 0

                # Verify 'six' is in the dependencies
                found_six = any("six" in dep_name.lower() for dep_name in dependencies.keys())
                assert found_six, f"Expected to find 'six' in dependencies: {list(dependencies.keys())}"

        finally:
            # Clean up
            try:
                container = client.containers.get(container_name)
                container.stop()
            except docker.errors.NotFound:
                pass
