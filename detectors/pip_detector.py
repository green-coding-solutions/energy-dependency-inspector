import hashlib
from typing import Dict, Any

from core.interfaces import EnvironmentExecutor, PackageManagerDetector


class PipDetector(PackageManagerDetector):
    """Detector for Python packages managed by pip."""

    def get_name(self) -> str:
        """Return the package manager identifier."""
        return "pip"

    def is_available(self, executor: EnvironmentExecutor) -> bool:
        """Check if pip is available in the environment."""
        _, _, exit_code = executor.execute_command("pip --version")
        return exit_code == 0

    def get_dependencies(
        self, executor: EnvironmentExecutor, working_dir: str = None
    ) -> Dict[str, Any]:
        """Extract pip dependencies with versions.

        Uses 'pip list --format=freeze' to get installed packages.
        Since PyPI doesn't reuse filenames for same versions, version numbers are sufficient as unique identifiers.
        """
        stdout, _, exit_code = executor.execute_command(
            "pip list --format=freeze", working_dir
        )

        if exit_code != 0:
            return {"location": self._get_pip_location(executor, working_dir), "dependencies": {}}

        dependencies = {}
        for line in stdout.strip().split("\n"):
            if line and "==" in line:
                package_name, version = line.split("==", 1)
                package_name = package_name.strip()
                version = version.strip()

                dependencies[package_name] = {
                    "version": version,
                    "hash": self._generate_hash(package_name, version),
                }

        return {
            "location": self._get_pip_location(executor, working_dir),
            "dependencies": dependencies,
        }

    def _get_pip_location(self, executor: EnvironmentExecutor, working_dir: str = None) -> str:
        """Get the location of the pip environment."""
        stdout, _, exit_code = executor.execute_command("pip show pip", working_dir)

        if exit_code == 0:
            for line in stdout.split("\n"):
                if line.startswith("Location:"):
                    return line.split(":", 1)[1].strip()

        return "global"

    def _generate_hash(self, package_name: str, version: str) -> str:
        """Generate a hash for the package based on name and version.

        Since PyPI doesn't reuse filenames for same versions, this provides a unique identifier.
        """
        content = f"{package_name}=={version}"
        return hashlib.sha256(content.encode()).hexdigest()[:32]
