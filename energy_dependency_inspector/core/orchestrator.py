from typing import Optional, Any
from .interfaces import EnvironmentExecutor, PackageManagerDetector
from ..detectors.pip_detector import PipDetector
from ..detectors.npm_detector import NpmDetector
from ..detectors.dpkg_detector import DpkgDetector
from ..detectors.apk_detector import ApkDetector
from ..detectors.docker_info_detector import DockerInfoDetector
from ..detectors.maven_detector import MavenDetector


class Orchestrator:
    """Main orchestrator for dependency detection and extraction."""

    def __init__(
        self,
        debug: bool = False,
        skip_os_packages: bool = False,
        venv_path: str | None = None,
        skip_hash_collection: bool = False,
        selected_detectors: str | None = None,
    ):
        self.debug = debug
        self.skip_os_packages = skip_os_packages
        self.skip_hash_collection = skip_hash_collection

        # Create all detector instances
        all_detectors: list[PackageManagerDetector] = [
            DockerInfoDetector(),
            DpkgDetector(),
            ApkDetector(),
            MavenDetector(debug=debug),
            PipDetector(venv_path=venv_path, debug=debug),
            NpmDetector(debug=debug),
        ]

        # Filter detectors based on selection
        if selected_detectors:
            selected_names = [name.strip() for name in selected_detectors.split(",")]
            available_names = {detector.NAME for detector in all_detectors}

            # Validate detector names
            invalid_names = [name for name in selected_names if name not in available_names]
            if invalid_names:
                raise ValueError(
                    f"Invalid detector names: {', '.join(invalid_names)}. Available detectors: {', '.join(sorted(available_names))}"
                )

            # Filter to only selected detectors
            self.detectors = [detector for detector in all_detectors if detector.NAME in selected_names]
            if self.debug:
                selected_detector_names = [detector.NAME for detector in self.detectors]
                print(f"Selected detectors: {', '.join(selected_detector_names)}")
        else:
            self.detectors = all_detectors

    def resolve_dependencies(self, executor: EnvironmentExecutor, working_dir: Optional[str] = None) -> dict[str, Any]:
        """Resolve all dependencies from available package managers."""
        # Validate working directory if provided
        if working_dir is not None and not executor.path_exists(working_dir):
            raise ValueError(f"Working directory does not exist: {working_dir}")

        result: dict[str, Any] = {}

        for detector in self.detectors:
            detector_name = detector.NAME

            if self.debug:
                print(f"Checking usability of {detector_name}...")

            try:
                if detector.is_usable(executor, working_dir):
                    # Check if detector is OS package manager and skip if requested
                    if self.skip_os_packages and detector.is_os_package_manager():
                        if self.debug:
                            print(f"Skipping {detector_name} (OS package manager, --skip-os-packages enabled)")
                        continue

                    if self.debug:
                        print(f"{detector_name} is usable, extracting dependencies...")

                    dependencies = detector.get_dependencies(
                        executor, working_dir, skip_hash_collection=self.skip_hash_collection
                    )

                    # Special handling for docker-info detector (simplified format)
                    if detector_name == "docker-info":
                        result["source"] = dependencies
                        result["source"]["type"] = "container"
                        if self.debug:
                            print(f"Found container info for {detector_name}")
                    else:
                        # Standard handling for other detectors
                        # Check if result has dependencies (single location) or locations (mixed scope structure)
                        has_dependencies = dependencies.get("dependencies") or (
                            dependencies.get("scope") == "mixed" and dependencies.get("locations")
                        )
                        if has_dependencies or self.debug:
                            result[detector_name] = dependencies

                        if self.debug:
                            if dependencies.get("scope") == "mixed":
                                # Count dependencies across all locations for mixed scope
                                dep_count = 0
                                for location_data in dependencies.get("locations", {}).values():
                                    dep_count += len(location_data.get("dependencies", {}))
                            else:
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
