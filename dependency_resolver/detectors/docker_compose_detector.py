import re
from typing import Any

from ..core.interfaces import EnvironmentExecutor, PackageManagerDetector
from ..executors.docker_compose_executor import DockerComposeExecutor


class DockerComposeDetector(PackageManagerDetector):
    """Detector for Docker Compose container images and their dependencies."""

    NAME = "docker-compose"

    def is_usable(self, executor: EnvironmentExecutor, working_dir: str = None) -> bool:
        """Check if this is a Docker Compose environment and if we can extract container information."""
        return isinstance(executor, DockerComposeExecutor) and len(executor.get_containers()) > 0

    def get_dependencies(self, executor: EnvironmentExecutor, working_dir: str = None) -> dict[str, Any]:
        """Extract Docker Compose container images with their tags and hashes."""
        if not isinstance(executor, DockerComposeExecutor):
            return {"scope": "compose", "dependencies": {}}

        containers = executor.get_containers()
        dependencies = {}

        for container in containers:
            try:
                # Get container details
                container.reload()

                # Extract service name from container name
                # Docker Compose naming: <project>_<service>_<number>
                service_name = self._extract_service_name(container.name, executor.stack_name)

                # Get image information
                image = container.image
                image_name = self._extract_image_name(image.tags)
                image_id = image.id

                dependencies[service_name] = {"version": image_name, "hash": image_id}

            except (AttributeError, KeyError, ValueError) as e:
                # Continue processing other containers if one fails
                print(f"Warning: Failed to process container {container.name}: {str(e)}")
                continue

        return {"scope": "compose", "dependencies": dependencies}

    def _extract_service_name(self, container_name: str, stack_name: str) -> str:
        """Extract the service name from Docker Compose container name."""
        # Handle newer Docker Compose naming: <project>-<service>-<number>
        if container_name.startswith(f"{stack_name}-"):
            service_part = container_name.removeprefix(f"{stack_name}-")
            # Remove trailing -<number> pattern
            service_name = re.sub(r"-\d+$", "", service_part)
            return service_name

        # Handle legacy Docker Compose naming: <project>_<service>_<number>
        if container_name.startswith(f"{stack_name}_"):
            service_part = container_name.removeprefix(f"{stack_name}_")
            # Remove trailing _<number> pattern
            service_name = re.sub(r"_\d+$", "", service_part)
            return service_name

        # Fallback: use the full container name
        return container_name

    def _extract_image_name(self, tags: list[str]) -> str:
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

    def has_system_scope(self, executor: EnvironmentExecutor, working_dir: str = None) -> bool:
        """Docker Compose containers have compose scope, not system scope."""
        return False
