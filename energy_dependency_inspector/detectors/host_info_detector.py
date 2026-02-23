import platform
from typing import Optional, Any
from ..core.interfaces import EnvironmentExecutor, PackageManagerDetector
from ..executors.host_executor import HostExecutor


class HostInfoDetector(PackageManagerDetector):
    """Detector for Host metadata"""

    NAME = "host-info"

    def is_usable(self, executor: EnvironmentExecutor, working_dir: Optional[str] = None) -> bool:
        """Check if this is a non Docker environment."""
        _ = working_dir  # Unused parameter, required by interface
        return isinstance(executor, HostExecutor)

    def get_dependencies(
        self, executor: EnvironmentExecutor, working_dir: Optional[str] = None, skip_hash_collection: bool = False
    ) -> dict[str, Any]:
        """Extract Host metadata.

        Note: This detector returns metadata rather than packages, but conforms to the interface.
        The orchestrator handles this specially.
        """
        _ = working_dir  # Unused parameter, required by interface
        _ = skip_hash_collection  # Not applicable for host metadata
        if not isinstance(executor, HostExecutor):
            return {}

        result = {
            "kernel_version": platform.platform(),
            "os": platform.version()
        }

        return result

    def is_os_package_manager(self) -> bool:
        """Host info detector is not an OS package manager."""
        return False
