import json
from typing import Dict, Any, List

from .interfaces import EnvironmentExecutor, PackageManagerDetector
from detectors.pip_detector import PipDetector
from detectors.dpkg_detector import DpkgDetector
from detectors.apk_detector import ApkDetector


class DependencyResolver:
    """Main orchestrator for dependency detection and extraction."""

    def __init__(self, debug: bool = False):
        self.debug = debug
        self.detectors: List[PackageManagerDetector] = [
            DpkgDetector(),
            ApkDetector(),
            PipDetector(),
        ]

    def resolve_dependencies(self, executor: EnvironmentExecutor, working_dir: str = None) -> Dict[str, Any]:
        """Resolve all dependencies from available package managers."""
        result = {}

        for detector in self.detectors:
            detector_name = detector.NAME

            if self.debug:
                print(f"Checking requirements for {detector_name}...")

            try:
                if not detector.meets_requirements(executor):
                    if self.debug:
                        print(f"{detector_name} requirements not met")
                    continue

                if self.debug:
                    print(f"Checking availability of {detector_name}...")

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
                continue

        return result

    def resolve_and_format(
        self, executor: EnvironmentExecutor, working_dir: str = None, pretty_print: bool = True
    ) -> str:
        """Resolve dependencies and format as JSON string."""
        dependencies = self.resolve_dependencies(executor, working_dir)

        if self.debug:
            excerpt = self._create_excerpt(dependencies)
            if pretty_print:
                return json.dumps(excerpt, indent=2, sort_keys=True)
            else:
                return json.dumps(excerpt, sort_keys=True)
        else:
            if pretty_print:
                return json.dumps(dependencies, indent=2, sort_keys=True)
            else:
                return json.dumps(dependencies, sort_keys=True)

    def _create_excerpt(self, dependencies: Dict[str, Any], max_deps_per_manager: int = 3) -> Dict[str, Any]:
        """Create an excerpt of dependencies for debug mode."""
        excerpt: Dict[str, Any] = {}

        for manager_name, manager_data in dependencies.items():
            excerpt[manager_name] = {}

            for key, value in manager_data.items():
                if key != "dependencies":
                    excerpt[manager_name][key] = value

            if "dependencies" in manager_data:
                deps = manager_data["dependencies"]
                total_deps = len(deps)

                if total_deps <= max_deps_per_manager:
                    excerpt[manager_name]["dependencies"] = deps
                else:
                    limited_deps = dict(list(deps.items())[:max_deps_per_manager])
                    excerpt[manager_name]["dependencies"] = limited_deps
                    excerpt[manager_name]["_excerpt_info"] = {
                        "total_dependencies": total_deps,
                        "shown": max_deps_per_manager,
                        "note": f"Showing {max_deps_per_manager} of {total_deps} dependencies (debug mode excerpt)",
                    }

        return excerpt
