import json
from typing import Dict, Any, List

from .interfaces import EnvironmentExecutor, PackageManagerDetector
from detectors.pip_detector import PipDetector
from detectors.apt_detector import AptDetector


class DependencyResolver:
    """Main orchestrator for dependency detection and extraction."""

    def __init__(self, debug: bool = False):
        """Initialize the dependency resolver.

        Args:
            debug: Enable debug logging
        """
        self.debug = debug
        self.detectors: List[PackageManagerDetector] = [
            AptDetector(),  # System packages first (priority order)
            PipDetector(),  # Language-specific packages
        ]

    def resolve_dependencies(
        self, executor: EnvironmentExecutor, working_dir: str = None
    ) -> Dict[str, Any]:
        """Resolve all dependencies from available package managers.

        Args:
            executor: Environment executor to use
            working_dir: Optional working directory

        Returns:
            Dictionary with dependencies organized by package manager
        """
        result = {}

        for detector in self.detectors:
            detector_name = detector.get_name()

            if self.debug:
                print(f"Checking availability of {detector_name}...")

            try:
                if detector.is_available(executor):
                    if self.debug:
                        print(f"{detector_name} is available, extracting dependencies...")

                    dependencies = detector.get_dependencies(executor, working_dir)
                    result[detector_name] = dependencies

                    if self.debug:
                        dep_count = len(dependencies.get("dependencies", {}))
                        print(f"Found {dep_count} dependencies for {detector_name}")
                else:
                    if self.debug:
                        print(f"{detector_name} is not available")

            except (RuntimeError, OSError, ValueError) as e:
                if self.debug:
                    print(f"Error checking {detector_name}: {str(e)}")
                # Error isolation: failed detectors don't affect others
                continue

        return result

    def resolve_and_format(
        self, executor: EnvironmentExecutor, working_dir: str = None, pretty_print: bool = True
    ) -> str:
        """Resolve dependencies and format as JSON string.

        Args:
            executor: Environment executor to use
            working_dir: Optional working directory
            pretty_print: Whether to pretty-print the JSON output

        Returns:
            JSON string with all resolved dependencies
        """
        dependencies = self.resolve_dependencies(executor, working_dir)

        if pretty_print:
            return json.dumps(dependencies, indent=2, sort_keys=True)
        else:
            return json.dumps(dependencies, sort_keys=True)
