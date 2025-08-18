import docker

from typing import Any
from ..core.interfaces import EnvironmentExecutor


class DockerComposeExecutor(EnvironmentExecutor):
    """Executor for analyzing Docker Compose stacks.

    This executor manages running containers from a Docker Compose stack
    and provides methods to execute commands across all containers.
    """

    def __init__(self, stack_name: str):
        """Initialize Docker Compose executor."""

        try:
            self.client = docker.from_env()
            self.stack_name = stack_name
            self.containers = self._get_compose_containers()

            if not self.containers:
                raise RuntimeError(f"No running containers found for Docker Compose stack '{stack_name}'")

        except docker.errors.APIError as e:
            raise RuntimeError(f"Docker API error: {str(e)}") from e

    def _get_compose_containers(self) -> list[Any]:
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

    def execute_command(self, command: str, working_dir: str = None) -> tuple[str, str, int]:
        """Docker Compose executor does not execute commands in containers.

        For Docker Compose environments, we only analyze the container images
        themselves, not the contents inside the containers.
        """
        return "", "Docker Compose executor does not execute commands in containers", 1

    def path_exists(self, path: str) -> bool:
        """Docker Compose executor does not check paths in containers.

        For Docker Compose environments, we only analyze the container images
        themselves, not the contents inside the containers.
        """
        return False

    def get_containers(self) -> list[Any]:
        """Get all containers in the Docker Compose stack."""
        return self.containers
