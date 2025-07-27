from abc import ABC, abstractmethod
from typing import Dict, Any, Tuple


class EnvironmentExecutor(ABC):
    """Abstract base class for executing commands in different environments."""

    @abstractmethod
    def execute_command(self, command: str, working_dir: str = None) -> Tuple[str, str, int]:
        """Execute a command in the target environment.

        Args:
            command: The command to execute
            working_dir: Optional working directory

        Returns:
            Tuple of (stdout, stderr, exit_code)
        """
        raise NotImplementedError

    @abstractmethod
    def file_exists(self, path: str) -> bool:
        """Check if a file exists in the target environment.

        Args:
            path: Path to check

        Returns:
            True if file exists, False otherwise
        """
        raise NotImplementedError


class PackageManagerDetector(ABC):
    """Abstract base class for package manager detection and dependency extraction."""

    def meets_requirements(self, executor: EnvironmentExecutor) -> bool:  # pylint: disable=unused-argument
        """Check if pre-requirements are met for this detector.

        This method should be overridden by detectors that have specific
        OS or environment requirements. Default implementation returns True.

        Args:
            executor: Environment executor to use for checking

        Returns:
            True if pre-requirements are met, False otherwise
        """
        return True

    @abstractmethod
    def is_available(self, executor: EnvironmentExecutor) -> bool:
        """Check if this package manager is available in the environment.

        Args:
            executor: Environment executor to use for checking

        Returns:
            True if package manager is available, False otherwise
        """
        raise NotImplementedError

    @abstractmethod
    def get_dependencies(self, executor: EnvironmentExecutor, working_dir: str = None) -> Dict[str, Any]:
        """Extract dependencies with versions and hashes.

        Args:
            executor: Environment executor to use
            working_dir: Optional working directory

        Returns:
            Dictionary containing location and dependencies information
        """
        raise NotImplementedError

    @abstractmethod
    def get_name(self) -> str:
        """Return the package manager identifier.

        Returns:
            String identifier for this package manager
        """
        raise NotImplementedError
