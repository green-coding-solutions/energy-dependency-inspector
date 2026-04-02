import hashlib
import json
import os
from typing import Optional, Any

from ..core.interfaces import EnvironmentExecutor, PackageManagerDetector


class NpmDetector(PackageManagerDetector):
    """Detector for Node.js packages managed by npm."""

    NAME = "npm"

    def __init__(self, debug: bool = False):
        self.debug = debug

    def is_usable(self, executor: EnvironmentExecutor, working_dir: Optional[str] = None) -> bool:
        """Check if npm is usable in the environment."""
        _, _, exit_code = executor.execute_command("npm --version", working_dir)
        return exit_code == 0

    def get_dependencies(
        self, executor: EnvironmentExecutor, working_dir: Optional[str] = None, skip_hash_collection: bool = False
    ) -> dict[str, Any]:
        """Extract npm dependencies with versions from multiple locations.

        Uses 'npm list --json --depth=0' for local packages and
        'npm list -g --json --depth=0' for global packages.
        Returns single location structure or nested structure for mixed locations.
        See docs/technical/detectors/npm_detector.md
        """
        node_version = self._get_node_version(executor, working_dir)

        local_results = self._get_local_dependencies(executor, working_dir, skip_hash_collection)
        global_result = self._get_global_dependencies(executor, working_dir, skip_hash_collection)

        if len(local_results) == 1 and not global_result:
            if node_version:
                local_results[0]["node_version"] = node_version
            return local_results[0]

        if not local_results and global_result:
            if node_version:
                global_result["node_version"] = node_version
            return global_result

        if local_results or global_result:
            locations = {}

            for local_result in local_results:
                local_location_data = {"scope": "project", "dependencies": local_result["dependencies"]}
                if "hash" in local_result:
                    local_location_data["hash"] = local_result["hash"]
                locations[local_result["location"]] = local_location_data

            if global_result:
                global_location_data = {"scope": "system", "dependencies": global_result["dependencies"]}
                if "hash" in global_result:
                    global_location_data["hash"] = global_result["hash"]
                locations[global_result["location"]] = global_location_data

            result: dict[str, Any] = {"scope": "mixed", "locations": locations}
            if node_version:
                result["node_version"] = node_version
            return result

        if working_dir:
            location = self._resolve_absolute_path(executor, working_dir)
            result = {"scope": "project", "location": location, "dependencies": {}}
        else:
            result = {"scope": "system", "location": "/usr/lib/node_modules", "dependencies": {}}

        if node_version:
            result["node_version"] = node_version
        return result

    def _get_local_dependencies(
        self, executor: EnvironmentExecutor, working_dir: Optional[str] = None, skip_hash_collection: bool = False
    ) -> list[dict[str, Any]]:
        """Get dependencies from all discovered npm projects."""
        results: list[dict[str, Any]] = []

        for node_modules_path in self._find_local_node_modules(executor, working_dir):
            project_dir = os.path.dirname(node_modules_path.rstrip("/"))

            if self._has_conflicting_lockfiles(executor, project_dir):
                continue

            stdout, _, exit_code = executor.execute_command("npm list --json --depth=0", project_dir)
            if exit_code != 0:
                continue

            dependencies = {}
            try:
                npm_data = json.loads(stdout)
                npm_dependencies = npm_data.get("dependencies", {})

                for package_name, package_info in npm_dependencies.items():
                    version = package_info.get("version", "unknown")
                    dependencies[package_name] = {"version": version}
            except (json.JSONDecodeError, AttributeError):
                continue

            if not dependencies:
                continue

            result: dict[str, Any] = {"scope": "project", "location": node_modules_path}
            if not skip_hash_collection:
                result["hash"] = self._generate_location_hash(executor, node_modules_path)
            result["dependencies"] = dependencies
            results.append(result)

        return results

    def _find_local_node_modules(
        self, executor: EnvironmentExecutor, working_dir: Optional[str] = None
    ) -> list[str]:
        """Find all project node_modules directories under the scan root."""
        search_root = self._resolve_absolute_path(executor, working_dir or "/")
        stdout, stderr, exit_code = executor.execute_command(
            f"find '{search_root}' -type d -name 'node_modules' -print 2>/dev/null | LC_COLLATE=C sort -u"
        )
        if exit_code != 0:
            if self.debug:
                print(f"ERROR: npm project discovery failed with exit code {exit_code}")
                print(f"ERROR: stderr: {stderr}")
            return []

        results: list[str] = []
        for line in stdout.splitlines():
            node_modules_path = line.strip()
            if not node_modules_path:
                continue
            if self._is_system_location(node_modules_path):
                continue
            project_dir = os.path.dirname(node_modules_path.rstrip("/"))
            has_package_json = executor.path_exists(f"{project_dir}/package.json")
            has_package_lock = executor.path_exists(f"{project_dir}/package-lock.json")
            if has_package_json or has_package_lock:
                results.append(node_modules_path)
        return results

    def _has_conflicting_lockfiles(self, executor: EnvironmentExecutor, project_dir: str) -> bool:
        """Detect lock files for alternative JavaScript package managers."""
        for exclusion in ("yarn.lock", "pnpm-lock.yaml", "bun.lockb"):
            if executor.path_exists(f"{project_dir}/{exclusion}"):
                return True
        return False

    def _get_global_dependencies(
        self, executor: EnvironmentExecutor, working_dir: Optional[str] = None, skip_hash_collection: bool = False
    ) -> dict[str, Any] | None:
        """Get dependencies from global npm installation."""
        stdout, _, exit_code = executor.execute_command("npm list -g --json --depth=0", working_dir)
        if exit_code != 0:
            return None

        dependencies = {}
        try:
            npm_data = json.loads(stdout)
            npm_dependencies = npm_data.get("dependencies", {})

            for package_name, package_info in npm_dependencies.items():
                version = package_info.get("version", "unknown")
                dependencies[package_name] = {"version": version}

        except (json.JSONDecodeError, AttributeError):
            pass

        if not dependencies:
            return None

        # Get global npm location
        location = self._get_global_npm_location(executor)

        result: dict[str, Any] = {"scope": "system", "location": location}
        if not skip_hash_collection:
            result["hash"] = self._generate_location_hash(executor, location)
        result["dependencies"] = dependencies
        return result

    def _is_system_location(self, location: str) -> bool:
        """Check if a location represents a system-wide npm installation."""
        return location.startswith(("/usr/lib/node_modules", "/usr/local/lib/node_modules"))

    def _get_global_npm_location(self, executor: EnvironmentExecutor) -> str:
        """Get the actual location path of the global npm installation."""
        # Get npm prefix (e.g., /usr)
        stdout, _, exit_code = executor.execute_command("npm config get prefix")
        if exit_code == 0 and stdout.strip():
            prefix = stdout.strip()
            return f"{prefix}/lib/node_modules"

        # Fallback: return default global location
        return "/usr/lib/node_modules"

    def _get_node_version(self, executor: EnvironmentExecutor, working_dir: Optional[str] = None) -> str:
        """Get the Node.js runtime version for the npm environment."""
        stdout, _, exit_code = executor.execute_command("node --version", working_dir)
        if exit_code == 0 and stdout.strip():
            return stdout.strip()
        return ""

    def _resolve_absolute_path(self, executor: EnvironmentExecutor, path: str) -> str:
        """Resolve absolute path within the executor's context."""
        if path == "/":
            return "/"
        if path == ".":
            # Get the current working directory from the executor
            stdout, stderr, exit_code = executor.execute_command("pwd")
            if exit_code == 0 and stdout.strip():
                return stdout.strip()
            raise RuntimeError(f"Failed to resolve current directory in executor context: {stderr}")
        else:
            # For non-current directory paths, try to resolve within executor context
            stdout, stderr, exit_code = executor.execute_command(f"cd '{path}' && pwd")
            if exit_code == 0 and stdout.strip():
                return stdout.strip()
            raise RuntimeError(f"Failed to resolve path '{path}' in executor context: {stderr}")

    def _generate_location_hash(self, executor: EnvironmentExecutor, location: str) -> str:
        """Generate a hash based on the contents of the location directory.

        Implements package manager location hashing as part of multi-tiered hash strategy.
        See docs/technical/detectors/npm_detector.md
        """
        # Use environment-independent sorting for consistent hashes across systems.
        # Two-tier sort strategy: primary by file size (numeric), secondary by path (lexicographic).
        # Include both regular files and symbolic links to capture complete directory state.
        # For symlinks, include the target path (%l) to make hash sensitive to link changes.
        # The -printf format ensures consistent "size path [target]" output regardless of system.
        # LC_COLLATE=C ensures byte-wise lexicographic sorting independent of system locale.
        # Excludes npm cache directories and temporary files that change frequently.
        stdout, _, exit_code = executor.execute_command(
            f"cd '{location}' && find . "
            "-name 'node_modules/.cache' -prune -o "
            "-name '*.log' -prune -o "
            "-name '.npm' -prune -o "
            "-not -name '*.tmp' "
            "-not -name '*.temp' "
            "\\( -type f -o -type l \\) -printf '%s %p %l\\n' | LC_COLLATE=C sort -n -k1,1 -k2,2"
        )

        if exit_code == 0 and stdout.strip():
            content = stdout.strip()
            return hashlib.sha256(content.encode()).hexdigest()
        else:
            if self.debug:
                print(f"ERROR: npm_detector hash generation command failed with exit code {exit_code}")
                print(f"ERROR: command stdout: {stdout}")
                print(f"ERROR: location: {location}")
            return ""

    def is_os_package_manager(self) -> bool:
        """NPM is a language package manager, not an OS package manager."""
        return False
