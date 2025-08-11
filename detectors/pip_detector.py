import hashlib
import os
from typing import Dict, Any

from core.interfaces import EnvironmentExecutor, PackageManagerDetector
from executors import HostExecutor


class PipDetector(PackageManagerDetector):
    """Detector for Python packages managed by pip."""

    NAME = "pip"

    def __init__(self, venv_path: str = None, debug: bool = False):
        self.explicit_venv_path = venv_path
        self.debug = debug

    def is_usable(self, executor: EnvironmentExecutor, working_dir: str = None) -> bool:
        """Check if pip is usable in the environment."""
        _, _, exit_code = executor.execute_command("pip --version", working_dir)
        return exit_code == 0

    def get_dependencies(self, executor: EnvironmentExecutor, working_dir: str = None) -> Dict[str, Any]:
        """Extract pip dependencies with versions.

        Uses 'pip list --format=freeze' for clean package==version format.
        See docs/adr/0006-pip-list-freeze-for-python-packages.md
        """
        # If working_dir is specified but no venv exists there, return empty dependencies
        if working_dir:
            venv_path = self._find_venv_path(executor, working_dir)
            if not venv_path:
                location = self._resolve_absolute_path(executor, working_dir)
                return {"scope": "project", "location": location, "dependencies": {}}

        pip_command = self._get_pip_command(executor, working_dir)
        stdout, _, exit_code = executor.execute_command(f"{pip_command} list --format=freeze", working_dir)

        if exit_code != 0:
            location = self._get_pip_location(executor, working_dir)
            scope = "system" if location == "system" else "project"
            result: Dict[str, Any] = {"scope": scope}
            if scope == "project":
                result["location"] = location
            result["dependencies"] = {}
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
        scope = "system" if location == "system" else "project"

        # Build result with desired field order: scope, location, hash, dependencies
        final_result: Dict[str, Any] = {"scope": scope}

        if scope == "project":
            final_result["location"] = location
            # Generate location-based hash if appropriate
            if dependencies:
                final_result["hash"] = self._generate_location_hash(executor, location)

        final_result["dependencies"] = dependencies

        return final_result

    def _get_pip_location(self, executor: EnvironmentExecutor, working_dir: str = None) -> str:
        """Get the location of the pip environment."""
        pip_command = self._get_pip_command(executor, working_dir)
        stdout, _, exit_code = executor.execute_command(f"{pip_command} show pip", working_dir)

        if exit_code == 0:
            for line in stdout.split("\n"):
                if line.startswith("Location:"):
                    return line.split(":", 1)[1].strip()

        return "system"

    def _get_pip_command(self, executor: EnvironmentExecutor, working_dir: str = None) -> str:
        """Get the appropriate pip command, activating venv if available."""
        venv_path = self._find_venv_path(executor, working_dir)
        if venv_path:
            venv_pip = f"{venv_path}/bin/pip"
            if executor.path_exists(venv_pip):
                return venv_pip
        return "pip"

    def _find_venv_path(self, executor: EnvironmentExecutor, working_dir: str = None) -> str:
        """Find virtual environment by searching for pyvenv.cfg files.

        Implements automatic virtual environment detection strategy.
        See docs/adr/0007-python-virtual-environment-detection.md
        """
        # If explicit venv path is provided, use it first
        if self.explicit_venv_path:
            # Expand ~ within the executor context, not on the host
            stdout, _, exit_code = executor.execute_command(f"echo {self.explicit_venv_path}")
            if exit_code == 0 and stdout.strip():
                expanded_path = stdout.strip()
                pyvenv_cfg = f"{expanded_path}/pyvenv.cfg"
                if executor.path_exists(pyvenv_cfg):
                    return expanded_path

        # Use VIRTUAL_ENV environment variable in non-host environments (e.g., Docker)
        if not isinstance(executor, HostExecutor):
            stdout, _, exit_code = executor.execute_command("echo $VIRTUAL_ENV", working_dir)
            if exit_code == 0 and stdout.strip():
                virtual_env_path = stdout.strip()
                pyvenv_cfg = f"{virtual_env_path}/pyvenv.cfg"
                if executor.path_exists(pyvenv_cfg):
                    return virtual_env_path

        # Search for local virtual environments in project directory
        search_dir = working_dir or "."

        pyvenv_cfg = f"{search_dir}/pyvenv.cfg"
        if executor.path_exists(pyvenv_cfg):
            return search_dir

        common_venv_names = ["venv", ".venv", "env", ".env", "virtualenv"]

        for venv_name in common_venv_names:
            venv_dir = f"{search_dir}/{venv_name}"
            pyvenv_cfg = f"{venv_dir}/pyvenv.cfg"
            if executor.path_exists(pyvenv_cfg):
                return venv_dir

        # Search for virtual environments in common external locations
        if working_dir:
            # Get project name from the resolved working directory
            resolved_working_dir = self._resolve_absolute_path(executor, working_dir)
            project_name = os.path.basename(resolved_working_dir)
            common_venv_locations = [
                f"~/.virtualenvs/{project_name}",
                f"~/.local/share/virtualenvs/{project_name}",
                f"~/.cache/pypoetry/virtualenvs/{project_name}",
                f"~/.pyenv/versions/{project_name}",
            ]

            for venv_location in common_venv_locations:
                # Expand ~ within the executor context, not on the host
                stdout, _, exit_code = executor.execute_command(f"echo {venv_location}")
                if exit_code == 0 and stdout.strip():
                    expanded_path = stdout.strip()
                    pyvenv_cfg = f"{expanded_path}/pyvenv.cfg"
                    if executor.path_exists(pyvenv_cfg):
                        return expanded_path

        return None

    def _resolve_absolute_path(self, executor: EnvironmentExecutor, path: str) -> str:
        """Resolve absolute path within the executor's context."""
        if path == ".":
            stdout, stderr, exit_code = executor.execute_command("pwd")
            if exit_code == 0 and stdout.strip():
                return stdout.strip()
            raise RuntimeError(f"Failed to resolve current directory in executor context: {stderr}")
        else:
            stdout, stderr, exit_code = executor.execute_command(f"cd '{path}' && pwd")
            if exit_code == 0 and stdout.strip():
                return stdout.strip()
            raise RuntimeError(f"Failed to resolve path '{path}' in executor context: {stderr}")

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
            if self.debug:
                print(f"ERROR: pip_detector hash generation command failed with exit code {exit_code}")
                print(f"ERROR: command stdout: {stdout}")
                print(f"ERROR: location: {location}")
            return ""

    def has_system_scope(self, executor: EnvironmentExecutor, working_dir: str = None) -> bool:
        """PIP has system scope when no virtual environment is found."""
        return self._get_pip_location(executor, working_dir) == "system"
