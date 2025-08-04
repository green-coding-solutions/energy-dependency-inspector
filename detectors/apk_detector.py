from typing import Dict, Any

from core.interfaces import EnvironmentExecutor, PackageManagerDetector


class ApkDetector(PackageManagerDetector):
    """Detector for system packages managed by apk (Alpine Linux)."""

    NAME = "apk"

    def meets_requirements(self, executor: EnvironmentExecutor) -> bool:
        """Check if running on Alpine Linux."""
        stdout, _, exit_code = executor.execute_command("cat /etc/os-release")
        if exit_code == 0:
            return "alpine" in stdout.lower()

        return executor.file_exists("/etc/alpine-release")

    def is_available(self, executor: EnvironmentExecutor) -> bool:
        """Check if apk is available."""
        _, _, apk_exit_code = executor.execute_command("apk --version")
        return apk_exit_code == 0

    def get_dependencies(self, executor: EnvironmentExecutor, working_dir: str = None) -> Dict[str, Any]:
        """Extract system packages with versions using apk info."""
        command = "apk info -v"
        stdout, _, exit_code = executor.execute_command(command, working_dir)

        if exit_code != 0:
            return {"location": "global", "dependencies": {}}

        dependencies = {}
        for line in stdout.strip().split("\n"):
            line = line.strip()

            if not line or line.startswith("WARNING:"):
                continue

            if "-" in line:
                parts = line.rsplit("-", 2)
                if len(parts) >= 2:
                    package_name = parts[0].strip()
                    version = "-".join(parts[1:]).strip()

                    package_data = {
                        "version": version,
                    }

                    dependencies[package_name] = package_data

        return {"location": "global", "dependencies": dependencies}
