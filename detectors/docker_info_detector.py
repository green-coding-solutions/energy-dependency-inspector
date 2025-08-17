from typing import Dict, Any

from core.interfaces import EnvironmentExecutor, PackageManagerDetector
from executors import DockerExecutor


class DockerInfoDetector(PackageManagerDetector):
    """Detector for Docker container metadata (image name and hash)."""

    NAME = "docker-info"

    def is_usable(self, executor: EnvironmentExecutor, working_dir: str = None) -> bool:
        """Check if this is a Docker environment."""
        return isinstance(executor, DockerExecutor)

    def get_dependencies(self, executor: EnvironmentExecutor, working_dir: str = None) -> Dict[str, Any]:
        """Extract Docker container metadata."""
        if not isinstance(executor, DockerExecutor):
            return {}

        container_info = executor.get_container_info()

        # Return simplified container info structure
        result = {
            "name": container_info["name"],
            "image": container_info["image"],
            "hash": container_info["image_hash"],
        }

        # Include error if present
        if "error" in container_info:
            result["error"] = container_info["error"]

        return result

    def has_system_scope(self, executor: EnvironmentExecutor, working_dir: str = None) -> bool:
        """Docker container info has container scope, not system scope."""
        return False
