import hashlib
import os
from typing import Optional, Any

from ..core.interfaces import EnvironmentExecutor, PackageManagerDetector


class PipDetector(PackageManagerDetector):
    """Detector for Python packages managed by pip."""

    NAME = "pip"

    def __init__(self, venv_path: Optional[str] = None, debug: bool = False):
        self.explicit_venv_path = venv_path
        self.debug = debug

    def is_usable(self, executor: EnvironmentExecutor, working_dir: Optional[str] = None) -> bool:
        """Check if pip is usable in the environment."""
        _, _, exit_code = executor.execute_command("pip --version", working_dir)
        return exit_code == 0

    def get_dependencies(
        self, executor: EnvironmentExecutor, working_dir: Optional[str] = None, skip_hash_collection: bool = False
    ) -> dict[str, Any]:
        """Extract pip dependencies with versions from multiple locations.

        Uses 'pip list --format=freeze' for clean package==version format.
        Returns single location structure or nested structure for mixed locations.
        See docs/technical/detectors/pip_detector.md
        """
        project_results = self._get_venv_dependencies(executor, working_dir, skip_hash_collection)
        system_result = self._get_system_dependencies(executor, working_dir, skip_hash_collection)
        all_results = project_results + ([system_result] if system_result else [])

        if len(all_results) > 1:
            locations = {}

            for location_result in all_results:
                location_data = {
                    "scope": location_result["scope"],
                    "dependencies": location_result["dependencies"],
                }
                if "hash" in location_result:
                    location_data["hash"] = location_result["hash"]
                locations[location_result["location"]] = location_data

            return {"scope": "mixed", "locations": locations}
        if len(project_results) == 1:
            return project_results[0]
        if system_result:
            return system_result
        if working_dir:
            location = self._resolve_absolute_path(executor, working_dir)
            return {"scope": "project", "location": location, "dependencies": {}}
        return {"scope": "system", "location": "/usr/lib/python3/dist-packages", "dependencies": {}}

    def _get_venv_dependencies(
        self, executor: EnvironmentExecutor, working_dir: Optional[str] = None, skip_hash_collection: bool = False
    ) -> list[dict[str, Any]]:
        """Get dependencies from all discovered virtual environments."""
        results: list[dict[str, Any]] = []

        for venv_path in self._find_venv_paths(executor, working_dir):
            venv_pip = f"{venv_path}/bin/pip"
            stdout, _, exit_code = executor.execute_command(f"{venv_pip} list --format=freeze", working_dir)
            if exit_code != 0:
                continue

            dependencies = {}
            for line in stdout.strip().split("\n"):
                if line and "==" in line:
                    package_name, version = line.split("==", 1)
                    dependencies[package_name.strip()] = {"version": version.strip()}

            if not dependencies:
                continue

            location_stdout, _, location_exit_code = executor.execute_command(f"{venv_pip} show pip", working_dir)
            location = "/usr/lib/python3/dist-packages"
            if location_exit_code == 0:
                for line in location_stdout.split("\n"):
                    if line.startswith("Location:"):
                        location = line.split(":", 1)[1].strip()
                        break

            result: dict[str, Any] = {"scope": "project", "location": location, "dependencies": dependencies}
            if not skip_hash_collection:
                result["hash"] = self._generate_location_hash(executor, location)
            results.append(result)

        return results

    def _get_system_dependencies(
        self, executor: EnvironmentExecutor, working_dir: Optional[str] = None, skip_hash_collection: bool = False
    ) -> dict[str, Any] | None:
        """Get dependencies from system pip installation."""
        venv_paths = self._find_venv_paths(executor, working_dir)

        # Try different approaches to get system packages
        system_commands = [
            # Method 1: Deactivate any virtual env and use system python
            "unset VIRTUAL_ENV && unset PYTHONPATH && /usr/bin/python3 -m pip list --format=freeze 2>/dev/null || /usr/bin/pip3 list --format=freeze 2>/dev/null || pip list --format=freeze",
            # Method 2: Use system python directly
            "/usr/bin/python3 -m pip list --format=freeze",
            # Method 3: Use system pip directly
            "/usr/bin/pip3 list --format=freeze",
            # Method 4: Fallback to regular pip (might be system)
            "pip list --format=freeze",
        ]

        stdout = ""
        for cmd in system_commands:
            stdout, _, exit_code = executor.execute_command(cmd, working_dir)
            if exit_code == 0 and stdout.strip():
                break
        else:
            return None

        # Get system location
        location_commands = [
            "unset VIRTUAL_ENV && unset PYTHONPATH && /usr/bin/python3 -m pip show pip 2>/dev/null || /usr/bin/pip3 show pip 2>/dev/null || pip show pip",
            "/usr/bin/python3 -m pip show pip",
            "/usr/bin/pip3 show pip",
            "pip show pip",
        ]

        location = "/usr/lib/python3/dist-packages"  # fallback
        for cmd in location_commands:
            location_stdout, _, location_exit_code = executor.execute_command(cmd, working_dir)
            if location_exit_code == 0:
                for line in location_stdout.split("\n"):
                    if line.startswith("Location:"):
                        potential_location = line.split(":", 1)[1].strip()
                        # Only use if it looks like a system location
                        if self._is_system_location(potential_location):
                            location = potential_location
                            break
                break

        # If we have a venv and the location doesn't look like system, we might have gotten venv packages
        # In that case, we shouldn't return system dependencies
        if venv_paths and not self._is_system_location(location):
            return None

        dependencies = {}
        for line in stdout.strip().split("\n"):
            if line and "==" in line:
                package_name, version = line.split("==", 1)
                package_name = package_name.strip()
                version = version.strip()
                dependencies[package_name] = {"version": version}

        if not dependencies:
            return None

        result: dict[str, Any] = {"scope": "system", "location": location}
        if not skip_hash_collection:
            result["hash"] = self._generate_location_hash(executor, location)
        result["dependencies"] = dependencies
        return result

    def _is_system_location(self, location: str) -> bool:
        """Check if a location path represents a system-wide installation."""
        return location.startswith(("/usr/lib", "/usr/local/lib"))

    def _find_venv_paths(self, executor: EnvironmentExecutor, working_dir: Optional[str] = None) -> list[str]:
        """Find all virtual environments rooted at working_dir or / when unspecified."""
        venv_paths: list[str] = []
        seen_paths: set[str] = set()

        if self.explicit_venv_path:
            resolved_explicit_path = self._resolve_absolute_path(executor, self.explicit_venv_path)
            if self._is_valid_venv_path(executor, resolved_explicit_path):
                venv_paths.append(resolved_explicit_path)
                seen_paths.add(resolved_explicit_path)

        scan_root = self._resolve_absolute_path(executor, working_dir or "/")
        find_cmd = (
            f"find '{scan_root}' "
            "-path '*/site-packages/*' -prune -o "
            "-path '*/dist-packages/*' -prune -o "
            "-name 'pyvenv.cfg' -type f -print 2>/dev/null | LC_COLLATE=C sort -u"
        )
        stdout, _, exit_code = executor.execute_command(find_cmd)
        if exit_code != 0:
            if self.debug:
                print(f"pip_detector failed to enumerate virtual environments under {scan_root}")
            return venv_paths

        for line in stdout.splitlines():
            if not line.strip():
                continue
            venv_path = os.path.dirname(line.strip())
            if venv_path not in seen_paths and self._is_valid_venv_path(executor, venv_path):
                venv_paths.append(venv_path)
                seen_paths.add(venv_path)

        return venv_paths

    def _is_valid_venv_path(self, executor: EnvironmentExecutor, venv_path: str) -> bool:
        """Check whether a path is a pip-usable Python virtual environment."""
        return executor.path_exists(f"{venv_path}/pyvenv.cfg") and executor.path_exists(f"{venv_path}/bin/pip")

    def _resolve_absolute_path(self, executor: EnvironmentExecutor, path: str) -> str:
        """Resolve absolute path within the executor's context."""
        if path == "/":
            return "/"
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
