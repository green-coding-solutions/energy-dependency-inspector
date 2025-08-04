from typing import Dict, Any

from core.interfaces import EnvironmentExecutor, PackageManagerDetector


class ApkDetector(PackageManagerDetector):
    """Detector for system packages managed by apk (Alpine Linux)."""

    NAME = "apk"

    def is_usable(self, executor: EnvironmentExecutor) -> bool:
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
