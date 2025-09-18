from abc import ABC, abstractmethod
from typing import Optional, Any


class EnvironmentExecutor(ABC):
    """Abstract base class for executing commands in different environments."""

    @abstractmethod
    def execute_command(self, command: str, working_dir: Optional[str] = None) -> tuple[str, str, int]:
        """Execute a command in the target environment."""
        raise NotImplementedError

    @abstractmethod
    def path_exists(self, path: str) -> bool:
        """Check if a path (file or directory) exists in the target environment."""
        raise NotImplementedError


class PackageManagerDetector(ABC):
    """Abstract base class for package manager detection and dependency extraction."""

    NAME: str

    @abstractmethod
    def is_usable(self, executor: EnvironmentExecutor, working_dir: Optional[str] = None) -> bool:
        """Check if this package manager is usable in the environment.

        This should verify both that the environment meets requirements
        and that the package manager tool is available.
        """
        raise NotImplementedError

    @abstractmethod
    def get_dependencies(
        self, executor: EnvironmentExecutor, working_dir: Optional[str] = None, skip_hash_collection: bool = False
    ) -> dict[str, Any]:
        """Extract dependencies with versions and hashes.

        Args:
            executor: Environment executor for running commands
            working_dir: Working directory to use
            skip_hash_collection: Skip hash collection for improved performance

        Returns:
            tuple: (packages, metadata)
            - packages: List of package dicts with name, version, type, and optional hash
            - metadata: Dict with location and hash for project scope, empty for system scope
        """
        raise NotImplementedError

    @abstractmethod
    def has_system_scope(self, executor: EnvironmentExecutor, working_dir: Optional[str] = None) -> bool:
        """Check if this detector operates at system scope for the given environment.

        Returns True if the detector would return scope: "system" in get_dependencies().
        This allows efficient scope checking without the overhead of dependency extraction.
        """
        raise NotImplementedError
