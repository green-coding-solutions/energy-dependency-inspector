import os
import subprocess
from typing import Tuple

try:
    import docker

    DOCKER_AVAILABLE = True
except ImportError:
    DOCKER_AVAILABLE = False

from .interfaces import EnvironmentExecutor


class HostExecutor(EnvironmentExecutor):
    """Executor for running commands on the host system."""

    def execute_command(self, command: str, working_dir: str = None) -> Tuple[str, str, int]:
        """Execute a command on the host system.

        Args:
            command: The command to execute
            working_dir: Optional working directory

        Returns:
            Tuple of (stdout, stderr, exit_code)
        """
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                cwd=working_dir,
                timeout=30,
                check=False,
            )
            return result.stdout, result.stderr, result.returncode
        except subprocess.TimeoutExpired:
            return "", "Command timed out after 30 seconds", 1
        except (subprocess.SubprocessError, OSError) as e:
            return "", f"Command execution failed: {str(e)}", 1

    def file_exists(self, path: str) -> bool:
        """Check if a file exists on the host system.

        Args:
            path: Path to check

        Returns:
            True if file exists, False otherwise
        """
        return os.path.exists(path)


class DockerExecutor(EnvironmentExecutor):
    """Executor for running commands inside Docker containers."""

    def __init__(self, container_identifier: str):
        """Initialize Docker executor.

        Args:
            container_identifier: Container ID (short or full) or container name

        Raises:
            RuntimeError: If Docker is not available or container cannot be found
        """
        if not DOCKER_AVAILABLE:
            raise RuntimeError("Docker library not available. Install with: pip install docker")

        try:
            self.client = docker.from_env()
            # Try to get container by ID or name
            self.container = self.client.containers.get(container_identifier)

            # Verify container is running
            if self.container.status != "running":
                raise RuntimeError(
                    f"Container '{container_identifier}' is not running (status: {self.container.status})"
                )

        except docker.errors.NotFound as exc:
            raise RuntimeError(f"Container '{container_identifier}' not found") from exc
        except docker.errors.APIError as e:
            raise RuntimeError(f"Docker API error: {str(e)}") from e

    def execute_command(self, command: str, working_dir: str = None) -> Tuple[str, str, int]:
        """Execute a command inside the Docker container.

        Args:
            command: The command to execute
            working_dir: Optional working directory

        Returns:
            Tuple of (stdout, stderr, exit_code)
        """
        try:
            # Prepare exec_run parameters
            exec_kwargs = {
                "cmd": ["sh", "-c", command],
                "stdout": True,
                "stderr": True,
                "tty": False,
            }

            if working_dir:
                exec_kwargs["workdir"] = working_dir

            # Execute command in container
            result = self.container.exec_run(**exec_kwargs)

            # Decode output
            stdout = result.output.decode("utf-8") if result.output else ""

            # For docker exec_run, stderr is combined with stdout
            # We'll try to separate them based on common patterns
            stderr = ""

            return stdout, stderr, result.exit_code

        except docker.errors.APIError as e:
            return "", f"Docker API error: {str(e)}", 1
        except (OSError, ValueError) as e:
            return "", f"Command execution failed: {str(e)}", 1

    def file_exists(self, path: str) -> bool:
        """Check if a file exists inside the Docker container.

        Args:
            path: Path to check

        Returns:
            True if file exists, False otherwise
        """
        try:
            # Use test command to check file existence
            _, _, exit_code = self.execute_command(f'test -e "{path}"')
            return exit_code == 0
        except (OSError, ValueError):
            return False
