import json
from typing import Dict, Any, List, Optional

from .interfaces import EnvironmentExecutor, PackageManagerDetector
from executors import DockerComposeExecutor
from detectors.pip_detector import PipDetector
from detectors.npm_detector import NpmDetector
from detectors.dpkg_detector import DpkgDetector
from detectors.apk_detector import ApkDetector
from detectors.docker_compose_detector import DockerComposeDetector


class Orchestrator:
    """Main orchestrator for dependency detection and extraction."""

    def __init__(
        self,
        debug: bool = False,
        skip_system_scope: bool = False,
        venv_path: Optional[str] = None,
    ):
        self.debug = debug
        self.skip_system_scope = skip_system_scope

        # Create detector instances
        self.detectors: List[PackageManagerDetector] = [
            DockerComposeDetector(),
            DpkgDetector(),
            ApkDetector(),
            PipDetector(venv_path=venv_path, debug=debug),
            NpmDetector(debug=debug),
        ]

    def resolve_dependencies(self, executor: EnvironmentExecutor, working_dir: str = None) -> Dict[str, Any]:
        """Resolve all dependencies from available package managers."""
        result = {}

        # For Docker Compose environments, only run the DockerComposeDetector
        if isinstance(executor, DockerComposeExecutor):
            detectors_to_run = [d for d in self.detectors if d.NAME == "docker-compose"]
        else:
            # For other environments, skip the DockerComposeDetector
            detectors_to_run = [d for d in self.detectors if d.NAME != "docker-compose"]

        for detector in detectors_to_run:
            detector_name = detector.NAME

            if self.debug:
                print(f"Checking usability of {detector_name}...")

            try:
                if detector.is_usable(executor, working_dir):
                    # Check if detector has system scope and skip if requested
                    if self.skip_system_scope and detector.has_system_scope(executor, working_dir):
                        if self.debug:
                            print(f"Skipping {detector_name} (system scope, --skip-system-scope enabled)")
                        continue

                    if self.debug:
                        print(f"{detector_name} is usable, extracting dependencies...")

                    dependencies = detector.get_dependencies(executor, working_dir)

                    # Only include detector in result if it has dependencies or debug mode is enabled
                    if dependencies.get("dependencies") or self.debug:
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
                return json.dumps(excerpt, indent=2)
            else:
                return json.dumps(excerpt)
        else:
            if pretty_print:
                return json.dumps(dependencies, indent=2)
            else:
                return json.dumps(dependencies)

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
