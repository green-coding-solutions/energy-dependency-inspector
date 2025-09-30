from typing import Optional, Any
from ..core.interfaces import EnvironmentExecutor, PackageManagerDetector
from ..executors.docker_executor import DockerExecutor


class DockerInfoDetector(PackageManagerDetector):
    """Detector for Docker container metadata (image name and hash)."""

    NAME = "docker-info"

    def is_usable(self, executor: EnvironmentExecutor, working_dir: Optional[str] = None) -> bool:
        """Check if this is a Docker environment."""
        _ = working_dir  # Unused parameter, required by interface
        return isinstance(executor, DockerExecutor)

    def get_dependencies(
        self, executor: EnvironmentExecutor, working_dir: Optional[str] = None, skip_hash_collection: bool = False
    ) -> dict[str, Any]:
        """Extract Docker container metadata.

        Note: This detector returns metadata rather than packages, but conforms to the interface.
        The orchestrator handles this specially.
        """
        _ = working_dir  # Unused parameter, required by interface
        _ = skip_hash_collection  # Not applicable for docker metadata
        if not isinstance(executor, DockerExecutor):
            return {}

        container_info = executor.get_container_info()

        # Return simplified container info structure as metadata
        # The orchestrator will handle this specially for source section
        result = {
            "name": container_info["name"],
            "image": container_info["image"],
            "hash": container_info["image_hash"],
        }

        # Include error if present
        if "error" in container_info:
            result["error"] = container_info["error"]

        return result

    def is_os_package_manager(self) -> bool:
        """Docker info detector is not an OS package manager."""
        return False
