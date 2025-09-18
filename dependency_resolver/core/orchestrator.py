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
    ):
        self.debug = debug
        self.skip_system_scope = skip_system_scope
        self.skip_hash_collection = skip_hash_collection

        # Create detector instances
        self.detectors: list[PackageManagerDetector] = [
            DockerInfoDetector(),
            DpkgDetector(),
            ApkDetector(),
            MavenDetector(debug=debug),
            PipDetector(venv_path=venv_path, debug=debug),
            NpmDetector(debug=debug),
        ]

    def resolve_dependencies(
        self, executor: EnvironmentExecutor, working_dir: Optional[str] = None, only_container_info: bool = False
    ) -> dict[str, Any]:
        """Resolve all dependencies from available package managers."""
        # Validate working directory if provided
        if working_dir is not None and not executor.path_exists(working_dir):
            raise ValueError(f"Working directory does not exist: {working_dir}")

        result: dict[str, Any] = {}
        project_packages: list[dict[str, Any]] = []
        project_metadata: dict[str, dict[str, Any]] = {}
        system_packages: list[dict[str, Any]] = []
        system_metadata: dict[str, dict[str, Any]] = {}

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

                    # Special handling for docker-info detector
                    if detector_name == "docker-info":
                        packages, metadata = detector.get_dependencies(
                            executor, working_dir, skip_hash_collection=self.skip_hash_collection
                        )
                        if metadata:  # Only include if we got container info
                            metadata["type"] = "container"
                            result["source"] = metadata
                        if self.debug:
                            print(f"Found container info for {detector_name}")
                    else:
                        # Standard handling for package detectors
                        packages, metadata = detector.get_dependencies(
                            executor, working_dir, skip_hash_collection=self.skip_hash_collection
                        )

                        if detector.has_system_scope(executor, working_dir):
                            # System scope packages
                            system_packages.extend(packages)
                            if metadata:
                                system_metadata[detector_name] = metadata
                            if self.debug:
                                print(f"Found {len(packages)} system packages for {detector_name}")
                        else:
                            # Project scope packages
                            project_packages.extend(packages)
                            if metadata:
                                project_metadata[detector_name] = metadata
                            if self.debug:
                                print(f"Found {len(packages)} project packages for {detector_name}")
                else:
                    if self.debug:
                        print(f"{detector_name} is not available")

            except (RuntimeError, OSError, ValueError) as e:
                if self.debug:
                    print(f"Error checking {detector_name}: {str(e)}")
                continue

        # Build final result structure matching proposal
        if project_packages or project_metadata:
            project_section: dict[str, Any] = {"packages": project_packages, "package-management": project_metadata}
            result["project"] = project_section

        if system_packages or system_metadata:
            system_section: dict[str, Any] = {"packages": system_packages, "package-management": system_metadata}
            result["system"] = system_section

        return result
