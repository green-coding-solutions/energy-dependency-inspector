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

        Returns actual command exit code on success, or 1 for execution environment failures.
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
        """Check if a file exists on the host system."""
        return os.path.exists(path)


class DockerExecutor(EnvironmentExecutor):
    """Executor for running commands inside Docker containers.

    Uses custom RuntimeError with actionable messages for setup failures,
    preserving original exceptions with 'from' clause for debugging.
    """

    def __init__(self, container_identifier: str):
        """Initialize Docker executor."""
        if not DOCKER_AVAILABLE:
            raise RuntimeError("Docker library not available. Install with: pip install docker")

        try:
            self.client = docker.from_env()
            self.container = self.client.containers.get(container_identifier)

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

        Returns actual command exit code on success, or 1 for execution environment failures.
        """
        try:
            exec_kwargs = {
                "cmd": ["sh", "-c", command],
                "stdout": True,
                "stderr": True,
                "tty": False,
            }

            if working_dir:
                exec_kwargs["workdir"] = working_dir

            result = self.container.exec_run(**exec_kwargs)
            stdout = result.output.decode("utf-8") if result.output else ""
            stderr = ""

            return stdout, stderr, result.exit_code

        except docker.errors.APIError as e:
            return "", f"Docker API error: {str(e)}", 1
        except (OSError, ValueError) as e:
            return "", f"Command execution failed: {str(e)}", 1

    def file_exists(self, path: str) -> bool:
        """Check if a file exists inside the Docker container."""
        try:
            _, _, exit_code = self.execute_command(f'test -e "{path}"')
            return exit_code == 0
        except (OSError, ValueError):
            return False
