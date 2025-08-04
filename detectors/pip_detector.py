import hashlib
import os
from typing import Dict, Any

from core.interfaces import EnvironmentExecutor, PackageManagerDetector


class PipDetector(PackageManagerDetector):
    """Detector for Python packages managed by pip."""

    NAME = "pip"

    def is_usable(self, executor: EnvironmentExecutor) -> bool:
        """Check if pip is usable in the environment."""
        _, _, exit_code = executor.execute_command("pip --version")
        return exit_code == 0

    def get_dependencies(self, executor: EnvironmentExecutor, working_dir: str = None) -> Dict[str, Any]:
        """Extract pip dependencies with versions.

        Uses 'pip list --format=freeze' for clean package==version format.
        See docs/adr/0006-pip-list-freeze-for-python-packages.md
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
            venv_pip = os.path.join(venv_path, "bin", "pip")
            if executor.file_exists(venv_pip):
                return venv_pip
        return "pip"

    def _find_venv_path(self, executor: EnvironmentExecutor, working_dir: str = None) -> str:
        """Find virtual environment by searching for pyvenv.cfg files.

        Implements automatic virtual environment detection strategy.
        See docs/adr/0007-python-virtual-environment-detection.md
        """
        search_dir = working_dir or "."

        pyvenv_cfg = os.path.join(search_dir, "pyvenv.cfg")
        if executor.file_exists(pyvenv_cfg):
            return search_dir

        common_venv_names = ["venv", ".venv", "env", ".env", "virtualenv"]

        for venv_name in common_venv_names:
            venv_dir = os.path.join(search_dir, venv_name)
            pyvenv_cfg = os.path.join(venv_dir, "pyvenv.cfg")
            if executor.file_exists(pyvenv_cfg):
                return venv_dir

        return None

    def _generate_location_hash(self, executor: EnvironmentExecutor, location: str) -> str:
        """Generate a hash based on the contents of the location directory.

        Implements package manager location hashing as part of multi-tiered hash strategy.
        See docs/adr/0005-hash-generation-strategy.md
        """
        # Use environment-independent sorting for consistent hashes across systems.
        # Two-tier sort strategy: primary by file size (numeric), secondary by path (lexicographic).
        # Include both regular files and symbolic links to capture complete directory state.
        # For symlinks, include the target path (%l) to make hash sensitive to link changes.
        # The -printf format ensures consistent "size path [target]" output regardless of system.
        # LC_COLLATE=C ensures byte-wise lexicographic sorting independent of system locale.
        stdout, _, exit_code = executor.execute_command(
            f"cd '{location}' && find . "
            "-name '__pycache__' -prune -o "
            "-name '__editable__*' -prune -o "
            "-name 'pip*' -prune -o "
            "-name 'setuptools*' -prune -o "
            "-name 'pkg_resources' -prune -o "
            "-name '*distutils*' -prune -o "
            "-path '*/pip/_vendor' -prune -o "
            "-not -name '*.pyc' "
            "-not -name '*.pyo' "
            "-not -name 'INSTALLER' "
            "-not -name 'RECORD' "
            "\\( -type f -o -type l \\) -printf '%s %p %l\\n' | LC_COLLATE=C sort -n -k1,1 -k2,2"
        )
        if exit_code == 0 and stdout.strip():
            content = stdout.strip()
            return hashlib.sha256(content.encode()).hexdigest()
        else:
            print(f"ERROR: pip_detector hash generation command failed with exit code {exit_code}")
            print(f"ERROR: command stdout: {stdout}")
            print(f"ERROR: location: {location}")
            return ""
