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
        skip_system_scope: bool = False,
        venv_path: str | None = None,
        skip_hash_collection: bool = False,
        selected_detectors: str | None = None,
    ):
        self.debug = debug
        self.skip_system_scope = skip_system_scope
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

    def resolve_dependencies(
        self, executor: EnvironmentExecutor, working_dir: Optional[str] = None, only_container_info: bool = False
    ) -> dict[str, Any]:
        """Resolve all dependencies from available package managers."""
        # Validate working directory if provided
        if working_dir is not None and not executor.path_exists(working_dir):
            raise ValueError(f"Working directory does not exist: {working_dir}")

        result: dict[str, Any] = {}

        if only_container_info:
            # Only run docker-info detector when only container info is requested
            detectors_to_run = [d for d in self.detectors if d.NAME == "docker-info"]
        else:
            detectors_to_run = self.detectors

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
