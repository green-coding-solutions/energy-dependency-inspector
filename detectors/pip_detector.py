import hashlib
import os
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

    def get_dependencies(self, executor: EnvironmentExecutor, working_dir: str = None) -> Dict[str, Any]:
        """Extract pip dependencies with versions.

        Uses 'pip list --format=freeze' to get installed packages.
        Since PyPI doesn't reuse filenames for same versions, version numbers are sufficient as unique identifiers.
        """
        pip_command = self._get_pip_command(executor, working_dir)
        stdout, _, exit_code = executor.execute_command(f"{pip_command} list --format=freeze", working_dir)

        if exit_code != 0:
            location = self._get_pip_location(executor, working_dir)
            result = {"location": location, "dependencies": {}}
            if location != "global":
                result["hash"] = self._generate_location_hash(executor, location)
            return result

        dependencies = {}
        for line in stdout.strip().split("\n"):
            if line and "==" in line:
                package_name, version = line.split("==", 1)
                package_name = package_name.strip()
                version = version.strip()

                dependencies[package_name] = {
                    "version": version,
                }

        location = self._get_pip_location(executor, working_dir)
        result = {"location": location, "dependencies": dependencies}
        if location != "global":
            result["hash"] = self._generate_location_hash(executor, location)
        return result

    def _get_pip_location(self, executor: EnvironmentExecutor, working_dir: str = None) -> str:
        """Get the location of the pip environment."""
        pip_command = self._get_pip_command(executor, working_dir)
        stdout, _, exit_code = executor.execute_command(f"{pip_command} show pip", working_dir)

        if exit_code == 0:
            for line in stdout.split("\n"):
                if line.startswith("Location:"):
                    return line.split(":", 1)[1].strip()

        return "global"

    def _get_pip_command(self, executor: EnvironmentExecutor, working_dir: str = None) -> str:
        """Get the appropriate pip command, activating venv if available."""
        venv_path = self._find_venv_path(executor, working_dir)
        if venv_path:
            # Use the venv's pip directly
            venv_pip = os.path.join(venv_path, "bin", "pip")
            if executor.file_exists(venv_pip):
                return venv_pip
        return "pip"

    def _find_venv_path(self, executor: EnvironmentExecutor, working_dir: str = None) -> str:
        """Find virtual environment by searching for pyvenv.cfg files.

        Returns the path to the virtual environment directory, or None if not found.
        """
        search_dir = working_dir or "."

        # First check if current directory has pyvenv.cfg (we might be inside a venv)
        pyvenv_cfg = os.path.join(search_dir, "pyvenv.cfg")
        if executor.file_exists(pyvenv_cfg):
            return search_dir

        # Search subdirectories for pyvenv.cfg
        # Common venv directory names to check first
        common_venv_names = ["venv", ".venv", "env", ".env", "virtualenv"]

        for venv_name in common_venv_names:
            venv_dir = os.path.join(search_dir, venv_name)
            pyvenv_cfg = os.path.join(venv_dir, "pyvenv.cfg")
            if executor.file_exists(pyvenv_cfg):
                return venv_dir

        return None

    def _generate_location_hash(self, executor: EnvironmentExecutor, location: str) -> str:
        """Generate a hash based on the contents of the location directory."""
        # Get directory listing with relative paths + file sizes
        stdout, _, exit_code = executor.execute_command(
            f"cd '{location}' && find . "
            "-name '__pycache__' -prune -o "
            "-name 'pip*' -prune -o "
            "-name 'setuptools*' -prune -o "
            "-name 'pkg_resources' -prune -o "
            "-name '*distutils*' -prune -o "
            "-name '*.egg-info' -prune -o "  # "-path '*/pip/_vendor' -prune -o " \
            "-not -name '*.pyc' "
            "-not -name '*.pyo' "
            "-not -name 'INSTALLER' "
            "-not -name 'RECORD' "
            "-type f -exec stat -c '%n %s' {} \\; | sort"
        )
        if exit_code == 0 and stdout.strip():
            # Hash the sorted list of files
            content = stdout.strip()
            return hashlib.sha256(content.encode()).hexdigest()[:32]
        else:
            print(f"ERROR: pip_detector hash generation command failed with exit code {exit_code}")
            print(f"ERROR: command stdout: {stdout}")
            print(f"ERROR: location: {location}")
            return ""
