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

    def meets_requirements(self, executor: EnvironmentExecutor) -> bool:  # pylint: disable=unused-argument
        """Check if pre-requirements are met for this detector.

        Override for detectors with specific OS or environment requirements.
        """
        return True

    @abstractmethod
    def is_available(self, executor: EnvironmentExecutor) -> bool:
        """Check if this package manager is available in the environment."""
        raise NotImplementedError

    @abstractmethod
    def get_dependencies(self, executor: EnvironmentExecutor, working_dir: str = None) -> Dict[str, Any]:
        """Extract dependencies with versions and hashes."""
        raise NotImplementedError
