import hashlib
import json
from typing import Optional, Any

from ..core.interfaces import EnvironmentExecutor, PackageManagerDetector

# Package type constant
PACKAGE_TYPE_NPM = "npm"


class NpmDetector(PackageManagerDetector):
    """Detector for Node.js packages managed by npm."""

    NAME = "npm"

    def __init__(self, debug: bool = False):
        self.debug = debug

    def is_usable(self, executor: EnvironmentExecutor, working_dir: Optional[str] = None) -> bool:
        """Check if npm is usable and the project uses npm (not yarn/pnpm)."""
        _, _, exit_code = executor.execute_command("npm --version", working_dir)
        if exit_code != 0:
            return False

        # Check if project uses npm by looking for npm-specific files in the working directory
        search_dir = working_dir or "."

        # Check package.json first (most common case)
        if executor.path_exists(f"{search_dir}/package.json"):
            # Only check exclusions if package.json exists
            exclusions = ["yarn.lock", "pnpm-lock.yaml", "bun.lockb"]
            for exclusion in exclusions:
                if executor.path_exists(f"{search_dir}/{exclusion}"):
                    return False
            return True

        # Fallback to package-lock.json
        return executor.path_exists(f"{search_dir}/package-lock.json")

    def get_dependencies(
        self, executor: EnvironmentExecutor, working_dir: Optional[str] = None
    ) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        """Extract npm dependencies with versions.

        Uses 'npm list --json --depth=0' for structured package information.
        See docs/technical/detectors/npm_detector.md

        Returns:
            tuple: (packages, metadata)
            - packages: List of package dicts with name, version, type
            - metadata: Dict with location and hash for project scope, empty for system scope
        """
        stdout, _, exit_code = executor.execute_command("npm list --json --depth=0", working_dir)

        location = self._get_npm_location(executor, working_dir)
        packages: list[dict[str, Any]] = []

        if exit_code != 0:
            if location == "system":
                return packages, {}
            else:
                return packages, {"location": location}

        try:
            npm_data = json.loads(stdout)
            npm_dependencies = npm_data.get("dependencies", {})

            for package_name, package_info in npm_dependencies.items():
                version = package_info.get("version", "unknown")
                packages.append({"name": package_name, "version": version, "type": PACKAGE_TYPE_NPM})

        except (json.JSONDecodeError, AttributeError):
            pass

        if location == "system":
            return packages, {}
        else:
            # Build metadata for project scope
            metadata = {"location": location}
            # Generate location-based hash if we have packages
            if packages:
                metadata["hash"] = self._generate_location_hash(executor, location)
            return packages, metadata

    def _get_npm_location(self, executor: EnvironmentExecutor, working_dir: Optional[str] = None) -> str:
        """Get the location of the npm project."""
        search_dir = working_dir or "."

        package_json_path = f"{search_dir}/package.json"
        if executor.path_exists(package_json_path):
            return self._resolve_absolute_path(executor, search_dir)

        node_modules_path = f"{search_dir}/node_modules"
        if executor.path_exists(node_modules_path):
            return self._resolve_absolute_path(executor, search_dir)

        return "system"

    def _resolve_absolute_path(self, executor: EnvironmentExecutor, path: str) -> str:
        """Resolve absolute path within the executor's context."""
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

    def has_system_scope(self, executor: EnvironmentExecutor, working_dir: Optional[str] = None) -> bool:
        """NPM has system scope when no local package.json or node_modules exists."""
        return self._get_npm_location(executor, working_dir) == "system"
