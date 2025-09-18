import hashlib
import os
from typing import Optional, Any

from ..core.interfaces import EnvironmentExecutor, PackageManagerDetector
from ..executors.host_executor import HostExecutor

# Package type constant
PACKAGE_TYPE_PIP = "pip"


class PipDetector(PackageManagerDetector):
    """Detector for Python packages managed by pip."""

    NAME = "pip"

    def __init__(self, venv_path: Optional[str] = None, debug: bool = False):
        self.explicit_venv_path = venv_path
        self.debug = debug
        self._cached_venv_path: str | None = None
        self._venv_path_searched = False

    def is_usable(self, executor: EnvironmentExecutor, working_dir: Optional[str] = None) -> bool:
        """Check if pip is usable in the environment."""
        _, _, exit_code = executor.execute_command("pip --version", working_dir)
        return exit_code == 0

    def get_dependencies(
        self, executor: EnvironmentExecutor, working_dir: Optional[str] = None
    ) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        """Extract pip dependencies with versions.

        Uses 'pip list --format=freeze' for clean package==version format.
        See docs/technical/detectors/pip_detector.md

        Returns:
            tuple: (packages, metadata)
            - packages: List of package dicts with name, version, type
            - metadata: Dict with location and hash for project scope, empty for system scope
        """
        # If working_dir is specified but no venv exists there, return empty dependencies
        if working_dir:
            venv_path = self._find_venv_path(executor, working_dir)
            if not venv_path:
                location = self._resolve_absolute_path(executor, working_dir)
                return [], {"location": location}

        pip_command = self._get_pip_command(executor, working_dir)
        stdout, _, exit_code = executor.execute_command(f"{pip_command} list --format=freeze", working_dir)

        if exit_code != 0:
            location = self._get_pip_location(executor, working_dir)
            if location == "system":
                return [], {}
            else:
                return [], {"location": location}

        packages = []
        for line in stdout.strip().split("\n"):
            if line and "==" in line:
                package_name, version = line.split("==", 1)
                package_name = package_name.strip()
                version = version.strip()

                packages.append({"name": package_name, "version": version, "type": PACKAGE_TYPE_PIP})

        location = self._get_pip_location(executor, working_dir)

        if location == "system":
            return packages, {}
        else:
            # Build metadata for project scope
            metadata = {"location": location}
            # Generate location-based hash if we have packages
            if packages:
                metadata["hash"] = self._generate_location_hash(executor, location)
            return packages, metadata

    def _get_pip_location(self, executor: EnvironmentExecutor, working_dir: Optional[str] = None) -> str:
        """Get the location of the pip environment."""
        pip_command = self._get_pip_command(executor, working_dir)
        stdout, _, exit_code = executor.execute_command(f"{pip_command} show pip", working_dir)

        if exit_code == 0:
            for line in stdout.split("\n"):
                if line.startswith("Location:"):
                    return line.split(":", 1)[1].strip()

        return "system"

    def _get_pip_command(self, executor: EnvironmentExecutor, working_dir: Optional[str] = None) -> str:
        """Get the appropriate pip command, activating venv if available."""
        venv_path = self._find_venv_path(executor, working_dir)
        if venv_path:
            venv_pip = f"{venv_path}/bin/pip"
            if executor.path_exists(venv_pip):
                return venv_pip
        return "pip"

    def _find_venv_path(self, executor: EnvironmentExecutor, working_dir: Optional[str] = None) -> str | None:
        """Find virtual environment using batch search for pyvenv.cfg files."""
        # Return cached result if already searched
        if self._venv_path_searched:
            return self._cached_venv_path

        # Build search paths in priority order
        search_paths = []
        search_dir = working_dir or "."

        # 1. Explicit venv path (highest priority)
        if self.explicit_venv_path:
            stdout, _, exit_code = executor.execute_command(f"echo {self.explicit_venv_path}")
            if exit_code == 0 and stdout.strip():
                search_paths.append(stdout.strip())

        # 2. VIRTUAL_ENV environment variable (Docker containers)
        if not isinstance(executor, HostExecutor):
            stdout, _, exit_code = executor.execute_command("echo $VIRTUAL_ENV", working_dir)
            if exit_code == 0 and stdout.strip():
                search_paths.append(stdout.strip())

        # 3. Local project directory and common venv names
        search_paths.extend(
            [
                search_dir,
                f"{search_dir}/venv",
                f"{search_dir}/.venv",
                f"{search_dir}/env",
                f"{search_dir}/.env",
                f"{search_dir}/virtualenv",
            ]
        )

        # 4. External venv locations (if working_dir specified)
        if working_dir:
            resolved_working_dir = self._resolve_absolute_path(executor, working_dir)
            project_name = os.path.basename(resolved_working_dir)

            # Expand external paths
            external_locations = [
                f"~/.virtualenvs/{project_name}",
                f"~/.local/share/virtualenvs/{project_name}",
                f"~/.cache/pypoetry/virtualenvs/{project_name}",
                f"~/.pyenv/versions/{project_name}",
            ]

            for location in external_locations:
                stdout, _, exit_code = executor.execute_command(f"echo {location}")
                if exit_code == 0 and stdout.strip():
                    search_paths.append(stdout.strip())

        # Single batch find command to locate pyvenv.cfg in all search paths
        if search_paths:
            # Escape paths and create find command
            escaped_paths = [f"'{path}'" for path in search_paths]
            find_cmd = f"find {' '.join(escaped_paths)} -maxdepth 1 -name 'pyvenv.cfg' -type f 2>/dev/null | head -1"

            stdout, _, exit_code = executor.execute_command(find_cmd)
            if exit_code == 0 and stdout.strip():
                pyvenv_cfg_path = stdout.strip()
                venv_path = os.path.dirname(pyvenv_cfg_path)
                self._cached_venv_path = venv_path
                self._venv_path_searched = True
                return venv_path

        # Fallback: System-wide search (only in container environments)
        if not isinstance(executor, HostExecutor):
            if self.debug:
                print("pip_detector performing system-wide pyvenv.cfg search in container environment")

            stdout, _, exit_code = executor.execute_command(
                "find /opt /home /usr/local -name 'pyvenv.cfg' -type f 2>/dev/null | head -1"
            )

            if exit_code == 0 and stdout.strip():
                pyvenv_cfg_path = stdout.strip()
                venv_path = os.path.dirname(pyvenv_cfg_path)
                if self.debug:
                    print(f"pip_detector found pyvenv.cfg at {pyvenv_cfg_path}, venv_path: {venv_path}")
                self._cached_venv_path = venv_path
                self._venv_path_searched = True
                return venv_path

        # No venv found
        if self.debug:
            print("pip_detector did not found any venv location!")
        self._cached_venv_path = None
        self._venv_path_searched = True
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
        See docs/technical/detectors/pip_detector.md
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

    def has_system_scope(self, executor: EnvironmentExecutor, working_dir: Optional[str] = None) -> bool:
        """PIP has system scope when no virtual environment is found."""
        return self._get_pip_location(executor, working_dir) == "system"
