import shlex

import docker

from ..core.interfaces import EnvironmentExecutor
from typing import Optional


class DockerExecutor(EnvironmentExecutor):
    """Executor for running commands inside Docker containers.

    Uses custom RuntimeError with actionable messages for setup failures,
    preserving original exceptions with 'from' clause for debugging.
    """

    def __init__(self, container_identifier: str):
        """Initialize Docker executor."""

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

    def execute_command(self, command: str, working_dir: Optional[str] = None) -> tuple[str, str, int]:
        """Execute a command inside the Docker container with direct execution fallback.

        Returns actual command exit code on success, or 1 for execution environment failures.
        """
        try:
            # First, try with sh
            result = self.container.exec_run(
                cmd=["sh", "-c", command], stdout=True, stderr=True, tty=False, workdir=working_dir
            )
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

    def _execute_command_direct(self, command: str, working_dir: Optional[str] = None) -> tuple[str, str, int]:
        """Fallback: execute simple commands directly without shell."""
        try:
            # Handle only the simple cases we actually use
            cmd_parts = DockerExecutor._parse_simple_command(command)
            if not cmd_parts:
                return "", f"Command too complex for direct execution (no shell available): {command}", 1

            result = self.container.exec_run(cmd=cmd_parts, stdout=True, stderr=True, tty=False, workdir=working_dir)
            stdout = result.output.decode("utf-8") if result.output else ""
            stderr = ""

            return stdout, stderr, result.exit_code

        except docker.errors.APIError as e:
            return "", f"Direct execution failed: {str(e)}", 1

    @staticmethod
    def _parse_simple_command(command: str) -> list[str] | None:
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

    def path_exists(self, path: str) -> bool:
        """Check if a path (file or directory) exists inside the Docker container."""
        try:
            _, _, exit_code = self.execute_command(f'test -e "{path}"')
            return exit_code == 0
        except (OSError, ValueError):
            return False

    def get_container_info(self) -> dict:
        """Get container metadata including image name and hash."""
        try:
            # Reload container to get latest info
            self.container.reload()

            # Get image information
            image = self.container.image
            if image is None:
                return {"name": self.container.name, "image": "unknown", "image_hash": "unknown"}
            image_name = self._extract_image_name(image.tags)
            image_id = image.id

            return {"name": self.container.name, "image": image_name, "image_hash": image_id}
        except (AttributeError, KeyError, ValueError) as e:
            return {"name": self.container.name, "image": "unknown", "image_hash": "unknown", "error": str(e)}

    def _extract_image_name(self, tags: list) -> str:
        """Extract a readable image name from image tags."""
        if not tags:
            return "unknown"

        # Use the first tag, or if empty, return 'unknown'
        first_tag = tags[0] if tags else "unknown"

        # Clean up the tag (remove registry prefixes if any)
        if "/" in first_tag:
            # Keep only the last part after the last slash for readability
            parts = first_tag.split("/")
            return parts[-1]

        return first_tag
