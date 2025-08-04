from typing import Dict, Any

from core.interfaces import EnvironmentExecutor, PackageManagerDetector


class ApkDetector(PackageManagerDetector):
    """Detector for system packages managed by apk (Alpine Linux)."""

    NAME = "apk"

    def is_usable(self, executor: EnvironmentExecutor, working_dir: str = None) -> bool:
        """Check if apk is usable (running on Alpine Linux and apk is available)."""
        stdout, _, exit_code = executor.execute_command("cat /etc/os-release")
        if exit_code == 0:
            meets_requirements = "alpine" in stdout.lower()
        else:
            meets_requirements = executor.file_exists("/etc/alpine-release")

        if not meets_requirements:
            return False

        _, _, apk_exit_code = executor.execute_command("apk --version")
        return apk_exit_code == 0

    def get_dependencies(self, executor: EnvironmentExecutor, working_dir: str = None) -> Dict[str, Any]:
        """Extract system packages with versions and architecture using apk list.

        Uses 'apk list --installed' for comprehensive package information including architecture.
        See docs/adr/0004-apk-list-for-alpine-packages.md
        """
        command = "apk list --installed"
        stdout, _, exit_code = executor.execute_command(command, working_dir)

        if exit_code != 0:
            return {"location": "global", "dependencies": {}}

        dependencies = {}
        for line in stdout.strip().split("\n"):
            line = line.strip()

            if not line or line.startswith("WARNING:"):
                continue

            # Parse format: package-name-version [architecture] {status} (license)
            # Example: bash-5.2.15-r5 x86_64 {bash} (GPL-3.0-or-later)
            if " " in line:
                parts = line.split(" ")
                package_version = parts[0]
                architecture = parts[1] if len(parts) > 1 else ""

                # Extract package name and version from package-version string
                if "-" in package_version:
                    version_parts = package_version.rsplit("-", 2)
                    if len(version_parts) >= 2:
                        package_name = version_parts[0].strip()
                        version = "-".join(version_parts[1:]).strip()

                        full_version = f"{version} {architecture}" if architecture else version

                        package_data = {
                            "version": full_version,
                        }

                        dependencies[package_name] = package_data

        return {"location": "global", "dependencies": dependencies}
