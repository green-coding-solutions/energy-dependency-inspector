import os
import shlex
import subprocess
from typing import Tuple, List, Any

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
        """Execute a command inside the Docker container with direct execution fallback.

        Returns actual command exit code on success, or 1 for execution environment failures.
        """
        try:
            # First, try with sh
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
            # Check if this is a "sh not found" error
            if "executable file not found" in str(e).lower() and "sh" in str(e).lower():
                return self._execute_command_direct(command, working_dir)
            else:
                return "", f"Docker API error: {str(e)}", 1
        except (OSError, ValueError) as e:
            return "", f"Command execution failed: {str(e)}", 1

    def _execute_command_direct(self, command: str, working_dir: str = None) -> Tuple[str, str, int]:
        """Fallback: execute simple commands directly without shell."""
        try:
            # Handle only the simple cases we actually use
            cmd_parts = self._parse_simple_command(command)
            if not cmd_parts:
                return "", f"Command too complex for direct execution (no shell available): {command}", 1

            exec_kwargs = {
                "cmd": cmd_parts,
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
            return "", f"Direct execution failed: {str(e)}", 1

    def _parse_simple_command(self, command: str) -> list:
        """Parse commands that can be executed directly without shell."""
        # Reject complex shell operations
        if any(op in command for op in ["&&", "||", "|", ">", "<", ";", "`", "$(", "$"]):
            return None

        # Handle simple commands with arguments
        try:
            parts = shlex.split(command)
            # Basic validation: ensure it looks like a simple command
            if parts and not parts[0].startswith("-"):
                return parts
        except ValueError:
            pass

        return None

    def file_exists(self, path: str) -> bool:
        """Check if a file exists inside the Docker container."""
        try:
            _, _, exit_code = self.execute_command(f'test -e "{path}"')
            return exit_code == 0
        except (OSError, ValueError):
            return False


class DockerComposeExecutor(EnvironmentExecutor):
    """Executor for analyzing Docker Compose stacks.

    This executor manages running containers from a Docker Compose stack
    and provides methods to execute commands across all containers.
    """

    def __init__(self, stack_name: str):
        """Initialize Docker Compose executor."""
        if not DOCKER_AVAILABLE:
            raise RuntimeError("Docker library not available. Install with: pip install docker")

        try:
            self.client = docker.from_env()
            self.stack_name = stack_name
            self.containers = self._get_compose_containers()

            if not self.containers:
                raise RuntimeError(f"No running containers found for Docker Compose stack '{stack_name}'")

        except docker.errors.APIError as e:
            raise RuntimeError(f"Docker API error: {str(e)}") from e

    def _get_compose_containers(self) -> List[Any]:
        """Get all running containers that belong to the Docker Compose stack."""
        try:
            # Docker Compose sets labels on containers to identify the project
            containers = self.client.containers.list(
                filters={"label": [f"com.docker.compose.project={self.stack_name}"], "status": "running"}
            )
            return list(containers)
        except docker.errors.APIError:
            # Fallback: try to find containers by name pattern (stack_name_service_number)
            all_containers = self.client.containers.list(filters={"status": "running"})
            matching_containers = []
            for container in all_containers:
                # Check if container name follows docker-compose naming convention
                if container.name.startswith(f"{self.stack_name}_"):
                    matching_containers.append(container)
            return matching_containers

    def execute_command(self, command: str, working_dir: str = None) -> Tuple[str, str, int]:
        """Docker Compose executor does not execute commands in containers.

        For Docker Compose environments, we only analyze the container images
        themselves, not the contents inside the containers.
        """
        return "", "Docker Compose executor does not execute commands in containers", 1

    def file_exists(self, path: str) -> bool:
        """Docker Compose executor does not check files in containers.

        For Docker Compose environments, we only analyze the container images
        themselves, not the contents inside the containers.
        """
        return False

    def get_containers(self) -> List[Any]:
        """Get all containers in the Docker Compose stack."""
        return self.containers
