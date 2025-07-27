from typing import Dict, Any

from core.interfaces import EnvironmentExecutor, PackageManagerDetector


class ApkDetector(PackageManagerDetector):
    """Detector for system packages managed by apk (Alpine Linux)."""

    def get_name(self) -> str:
        """Return the package manager identifier."""
        return "apk"

    def meets_requirements(self, executor: EnvironmentExecutor) -> bool:
        """Check if running on Alpine Linux."""
        # Check if running on Alpine Linux by checking /etc/os-release
        stdout, _, exit_code = executor.execute_command("cat /etc/os-release")
        if exit_code == 0:
            return "alpine" in stdout.lower()

        # Fallback: check if /etc/alpine-release exists
        return executor.file_exists("/etc/alpine-release")

    def is_available(self, executor: EnvironmentExecutor) -> bool:
        """Check if apk is available."""
        _, _, apk_exit_code = executor.execute_command("apk --version")
        return apk_exit_code == 0

    def get_dependencies(self, executor: EnvironmentExecutor, working_dir: str = None) -> Dict[str, Any]:
        """Extract system packages with versions using apk info.

        Uses 'apk info -v' to get installed packages with their versions.
        """
        command = "apk info -v"
        stdout, _, exit_code = executor.execute_command(command, working_dir)

        if exit_code != 0:
            return {"location": "global", "dependencies": {}}

        dependencies = {}
        for line in stdout.strip().split("\n"):
            line = line.strip()

            # Skip warning messages and empty lines
            if not line or line.startswith("WARNING:"):
                continue

            # apk info -v format: package-name-version-release
            # Example: alpine-baselayout-3.7.0-r0
            if "-" in line:
                # Find the last two dashes to separate package name from version-release
                parts = line.rsplit("-", 2)
                if len(parts) >= 2:
                    package_name = parts[0].strip()
                    # Combine version and release (e.g., "3.7.0-r0")
                    version = "-".join(parts[1:]).strip()

                    package_data = {
                        "version": version,
                    }

                    # APK doesn't provide direct package hashes, so we don't include hash field
                    # Following specification: "Do not generate synthetic hashes for individual packages"

                    dependencies[package_name] = package_data

        return {"location": "global", "dependencies": dependencies}
