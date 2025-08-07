from abc import ABC, abstractmethod
from typing import Dict, Any, Tuple


class EnvironmentExecutor(ABC):
    """Abstract base class for executing commands in different environments."""

    @abstractmethod
    def execute_command(self, command: str, working_dir: str = None) -> Tuple[str, str, int]:
        """Execute a command in the target environment."""
        raise NotImplementedError

    @abstractmethod
    def file_exists(self, path: str) -> bool:
        """Check if a file exists in the target environment."""
        raise NotImplementedError


class PackageManagerDetector(ABC):
    """Abstract base class for package manager detection and dependency extraction."""

    NAME: str

    @abstractmethod
    def is_usable(self, executor: EnvironmentExecutor, working_dir: str = None) -> bool:
        """Check if this package manager is usable in the environment.

        This should verify both that the environment meets requirements
        and that the package manager tool is available.
        """
        raise NotImplementedError

    @abstractmethod
    def get_dependencies(self, executor: EnvironmentExecutor, working_dir: str = None) -> Dict[str, Any]:
        """Extract dependencies with versions and hashes."""
        raise NotImplementedError

    @abstractmethod
    def is_global(self, executor: EnvironmentExecutor, working_dir: str = None) -> bool:
        """Check if this detector would operate globally (system-wide) for the given working directory.

        Returns True if the detector would return location: "global" in get_dependencies().
        This allows checking global status without the overhead of extracting all dependencies.
        """
        raise NotImplementedError
