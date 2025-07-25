import hashlib
from typing import Dict, Any

from core.interfaces import EnvironmentExecutor, PackageManagerDetector


class AptDetector(PackageManagerDetector):
    """Detector for system packages managed by apt/dpkg."""

    def get_name(self) -> str:
        """Return the package manager identifier."""
        return "system"

    def is_available(self, executor: EnvironmentExecutor) -> bool:
        """Check if dpkg-query is available in the environment."""
        _, _, exit_code = executor.execute_command("dpkg-query --version")
        return exit_code == 0

    def get_dependencies(self, executor: EnvironmentExecutor, working_dir: str = None) -> Dict[str, Any]:
        """Extract system packages with versions using dpkg-query.

        Uses 'dpkg-query -W -f' to get installed packages with their versions and architecture.
        """
        command = "dpkg-query -W -f='${Package}\t${Version}\t${Architecture}\n'"
        stdout, _, exit_code = executor.execute_command(command, working_dir)

        if exit_code != 0:
            return {"location": "global", "dependencies": {}}

        dependencies = {}
        for line in stdout.strip().split("\n"):
            if line and "\t" in line:
                parts = line.split("\t")
                if len(parts) >= 2:
                    package_name = parts[0].strip()
                    version = parts[1].strip()
                    architecture = parts[2].strip() if len(parts) > 2 else ""

                    full_version = f"{version} {architecture}" if architecture else version

                    dependencies[package_name] = {
                        "version": full_version,
                        "hash": self._generate_hash(package_name, full_version),
                    }

        return {"location": "global", "dependencies": dependencies}

    def _generate_hash(self, package_name: str, version: str) -> str:
        """Generate a hash for the package based on name and version."""
        content = f"{package_name}:{version}"
        return hashlib.sha256(content.encode()).hexdigest()[:32]
