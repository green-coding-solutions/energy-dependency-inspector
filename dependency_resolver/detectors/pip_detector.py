import hashlib
import os
from typing import Optional, Any

from ..core.interfaces import EnvironmentExecutor, PackageManagerDetector
from ..executors.host_executor import HostExecutor


class PipDetector(PackageManagerDetector):
    """Detector for Python packages managed by pip."""

    NAME = "pip"

    def __init__(self, venv_path: Optional[str] = None, debug: bool = False):
        self.explicit_venv_path = venv_path
        self.debug = debug
        self._cached_venv_path: str | None = None
        self._venv_path_searched = False
        self._cached_pip_command: str | None = None

    def is_usable(self, executor: EnvironmentExecutor, working_dir: Optional[str] = None) -> bool:
        """Check if pip is usable in the environment."""
        _, _, exit_code = executor.execute_command("pip --version", working_dir)
        return exit_code == 0

    def get_dependencies(
        self, executor: EnvironmentExecutor, working_dir: Optional[str] = None, skip_hash_collection: bool = False
    ) -> dict[str, Any]:
        """Extract pip dependencies with versions.

        Uses 'pip list --format=freeze' for clean package==version format.
        See docs/technical/detectors/pip_detector.md
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
            scope = "system" if self._is_system_location(location) else "project"
            return {"scope": scope, "location": location, "dependencies": {}}

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
        scope = "system" if self._is_system_location(location) else "project"

        # Build result with desired field order: scope, location, hash, dependencies
        result: dict[str, Any] = {"scope": scope, "location": location}

        # Generate location-based hash if appropriate
        if dependencies and not skip_hash_collection:
            result["hash"] = self._generate_location_hash(executor, location)

        result["dependencies"] = dependencies
        return result

    def _is_system_location(self, location: str) -> bool:
        """Check if a location path represents a system-wide installation."""
        return location.startswith(("/usr/lib", "/usr/local/lib"))

    def _get_pip_location(self, executor: EnvironmentExecutor, working_dir: Optional[str] = None) -> str:
        """Get the actual location path of the pip environment."""
        pip_command = self._get_pip_command(executor, working_dir)
        stdout, _, exit_code = executor.execute_command(f"{pip_command} show pip", working_dir)

        if exit_code == 0:
            for line in stdout.split("\n"):
                if line.startswith("Location:"):
                    location = line.split(":", 1)[1].strip()
                    return location

        # Fallback: return a default system location when pip location cannot be determined
        return "/usr/lib/python3/dist-packages"

    def _get_pip_command(self, executor: EnvironmentExecutor, working_dir: Optional[str] = None) -> str:
        """Get the appropriate pip command, activating venv if available."""
        if hasattr(self, "_cached_pip_command") and self._cached_pip_command:
            return self._cached_pip_command

        venv_path = self._find_venv_path(executor, working_dir)
        if venv_path:
            venv_pip = f"{venv_path}/bin/pip"
            if executor.path_exists(venv_pip):
                self._cached_pip_command = venv_pip
                return venv_pip

        self._cached_pip_command = "pip"
        return "pip"

    def _validate_venv_path(self, executor: EnvironmentExecutor, path: str) -> str | None:
        """Check if a path contains pyvenv.cfg and return the venv path if valid."""
        pyvenv_cfg_path = f"{path}/pyvenv.cfg"
        if executor.path_exists(pyvenv_cfg_path):
            self._cached_venv_path = path
            self._venv_path_searched = True
            return path
        return None

    def _find_venv_path(self, executor: EnvironmentExecutor, working_dir: Optional[str] = None) -> str | None:
        """Find virtual environment using priority-based search for pyvenv.cfg files."""
        # Return cached result if already searched
        if self._venv_path_searched:
            return self._cached_venv_path

        # 1. Explicit venv path (highest priority) - check immediately
        if self.explicit_venv_path:
            stdout, _, exit_code = executor.execute_command(f"echo {self.explicit_venv_path}")
            if exit_code == 0 and stdout.strip():
                venv_path = self._validate_venv_path(executor, stdout.strip())
                if venv_path:
                    self._cached_venv_path = venv_path
                    self._venv_path_searched = True
                    return venv_path

        # 2. VIRTUAL_ENV environment variable (Docker containers) - check immediately
        if not isinstance(executor, HostExecutor):
            stdout, _, exit_code = executor.execute_command("echo $VIRTUAL_ENV", working_dir)
            if exit_code == 0 and stdout.strip():
                venv_path = self._validate_venv_path(executor, stdout.strip())
                if venv_path:
                    self._cached_venv_path = venv_path
                    self._venv_path_searched = True
                    return venv_path

        # 3. Extract venv path from pip show pip location
        stdout, _, exit_code = executor.execute_command("pip show pip", working_dir)
        if exit_code == 0:
            for line in stdout.split("\n"):
                if line.startswith("Location:"):
                    pip_location = line.split(":", 1)[1].strip()
                    # Skip system locations
                    if not pip_location.startswith(("/usr/lib", "/usr/local/lib")) and "/lib/python" in pip_location:
                        venv_path = pip_location.split("/lib/python")[0]
                        # Trust this path since pip is installed there - just cache and return
                        self._cached_venv_path = venv_path
                        self._venv_path_searched = True
                        return venv_path
                    break

        # 4. Batch search for remaining venv locations
        # Collect all paths and use single find command for efficiency (fewer executor calls)
        search_paths = set()
        common_venv_names = ["venv", ".venv", "env", ".env", "virtualenv"]

        # Check working directory, if specified
        if working_dir:
            search_paths.add(working_dir)  # working_dir itself
            for venv_name in common_venv_names:
                search_paths.add(f"{working_dir}/{venv_name}")

        # Check current directory, if running in container environment
        if not isinstance(executor, HostExecutor):
            pwd_stdout, _, pwd_exit_code = executor.execute_command("pwd")
            if pwd_exit_code == 0 and pwd_stdout.strip():
                current_dir = pwd_stdout.strip()
                for venv_name in common_venv_names:
                    search_paths.add(f"{current_dir}/{venv_name}")

        # Check home directory subdirectories (always check)
        # Resolve home directory explicitly to avoid tilde expansion issues
        home_stdout, _, home_exit_code = executor.execute_command("echo $HOME")
        if home_exit_code == 0 and home_stdout.strip():
            home_dir = home_stdout.strip()
            for venv_name in common_venv_names:
                search_paths.add(f"{home_dir}/{venv_name}")

        # External venv locations (project-specific, only if working_dir specified)
        if working_dir:
            resolved_working_dir = self._resolve_absolute_path(executor, working_dir)
            project_name = os.path.basename(resolved_working_dir)

            # Use resolved home directory for external locations too
            if home_exit_code == 0 and home_stdout.strip():
                home_dir = home_stdout.strip()
                external_locations = [
                    f"{home_dir}/.virtualenvs/{project_name}",
                    f"{home_dir}/.local/share/virtualenvs/{project_name}",
                    f"{home_dir}/.cache/pypoetry/virtualenvs/{project_name}",
                    f"{home_dir}/.pyenv/versions/{project_name}",
                ]
                search_paths.update(external_locations)

        if search_paths:
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
                "find /opt /home -name 'pyvenv.cfg' -type f 2>/dev/null | head -1"
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

    def is_os_package_manager(self) -> bool:
        """PIP is a language package manager, not an OS package manager."""
        return False
