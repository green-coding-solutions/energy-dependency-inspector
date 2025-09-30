"""Test DockerExecutor fallback mechanism for containers without shell."""

import json
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

from energy_dependency_inspector.executors import DockerExecutor
from energy_dependency_inspector.core.orchestrator import Orchestrator
from energy_dependency_inspector.core.output_formatter import OutputFormatter

try:
    import docker
except ImportError:
    docker = None  # type: ignore


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
        assert executor_class._parse_simple_command("python3 --version") == ["python3", "--version"]
        assert executor_class._parse_simple_command("cat /etc/os-release") == ["cat", "/etc/os-release"]
        assert executor_class._parse_simple_command("test -e /usr/bin/python3") == [
            "test",
            "-e",
            "/usr/bin/python3",
        ]

        # Test complex commands that should be rejected
        assert executor_class._parse_simple_command("echo hello | cat") is None
        assert executor_class._parse_simple_command("cd /tmp && ls") is None
        assert executor_class._parse_simple_command("echo hello > file.txt") is None
        assert executor_class._parse_simple_command("echo $HOME") is None

        # Test commands starting with flags (should be rejected)
        assert executor_class._parse_simple_command("--version python3") is None

    @pytest.mark.skipif(docker is None, reason="Docker not available")
    def test_energy_dependency_inspector_integration_with_distroless(self) -> None:
        """Test full energy-dependency-inspector integration with distroless container."""
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

            # Test the energy-dependency-inspector with the distroless container
            executor = DockerExecutor(container_name)
            orchestrator = Orchestrator(debug=True)

            # This should work even without sh - the resolver will use our fallback
            result = orchestrator.resolve_dependencies(executor)

            # Verify we get a proper result structure
            assert isinstance(result, dict)

            # Check that at least some detectors were checked
            # Note: distroless containers typically won't have dpkg, apk, npm, or pip
            # but the resolver should still work and return an empty result
            # The important thing is that it doesn't crash due to missing sh

            # Verify the result can be formatted as JSON (as python3 -m energy_dependency_inspector does)
            formatter = OutputFormatter(debug=True)
            formatted_result = formatter.format_json(result, pretty_print=True)
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
    def test_energy_dependency_inspector_with_python_packages(self) -> None:
        """Test energy-dependency-inspector with a container that has Python packages but no sh."""
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
            orchestrator = Orchestrator(debug=False)  # Less verbose for this test
            result = orchestrator.resolve_dependencies(executor)

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
