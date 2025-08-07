import hashlib
import json
import os
from typing import Dict, Any

from core.interfaces import EnvironmentExecutor, PackageManagerDetector


class NpmDetector(PackageManagerDetector):
    """Detector for Node.js packages managed by npm."""

    NAME = "npm"

    def is_usable(self, executor: EnvironmentExecutor, working_dir: str = None) -> bool:
        """Check if npm is usable and the project uses npm (not yarn/pnpm)."""
        _, _, exit_code = executor.execute_command("npm --version", working_dir)
        if exit_code != 0:
            return False

        # Check if project uses npm by looking for npm-specific files in the working directory
        search_dir = working_dir or "."

        # If yarn.lock, pnpm-lock.yaml, or bun.lockb exist, prefer those package managers
        if executor.file_exists(os.path.join(search_dir, "yarn.lock")):
            return False
        if executor.file_exists(os.path.join(search_dir, "pnpm-lock.yaml")):
            return False
        if executor.file_exists(os.path.join(search_dir, "bun.lockb")):
            return False

        # If package.json exists or package-lock.json exists, and no other lock files, use npm
        package_json_exists = executor.file_exists(os.path.join(search_dir, "package.json"))
        package_lock_exists = executor.file_exists(os.path.join(search_dir, "package-lock.json"))

        return package_json_exists or package_lock_exists

    def get_dependencies(self, executor: EnvironmentExecutor, working_dir: str = None) -> Dict[str, Any]:
        """Extract npm dependencies with versions.

        Uses 'npm list --json --depth=0' for structured package information.
        See docs/adr/0011-npm-list-json-for-nodejs-packages.md
        """
        stdout, _, exit_code = executor.execute_command("npm list --json --depth=0", working_dir)

        location = self._get_npm_location(executor, working_dir)
        scope = "system" if location == "system" else "project"
        dependencies: Dict[str, Dict[str, str]] = {}

        # Build result with desired field order: scope, location, hash, dependencies
        result: Dict[str, Any] = {"scope": scope}
        if scope == "project":
            result["location"] = location

        if exit_code != 0:
            result["dependencies"] = dependencies
            return result

        try:
            npm_data = json.loads(stdout)
            npm_dependencies = npm_data.get("dependencies", {})

            for package_name, package_info in npm_dependencies.items():
                version = package_info.get("version", "unknown")
                dependencies[package_name] = {"version": version}

        except (json.JSONDecodeError, AttributeError):
            pass

        # Generate location-based hash if appropriate
        if dependencies and scope == "project":
            result["hash"] = self._generate_location_hash(executor, location)

        result["dependencies"] = dependencies

        return result

    def _get_npm_location(self, executor: EnvironmentExecutor, working_dir: str = None) -> str:
        """Get the location of the npm project."""
        search_dir = working_dir or "."

        package_json_path = os.path.join(search_dir, "package.json")
        if executor.file_exists(package_json_path):
            return os.path.abspath(search_dir)

        node_modules_path = os.path.join(search_dir, "node_modules")
        if executor.file_exists(node_modules_path):
            return os.path.abspath(search_dir)

        return "system"

    def _generate_location_hash(self, executor: EnvironmentExecutor, location: str) -> str:
        """Generate a hash based on the contents of the location directory.

        Implements package manager location hashing as part of multi-tiered hash strategy.
        See docs/adr/0005-hash-generation-strategy.md
        """
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
            return ""

    def has_system_scope(self, executor: EnvironmentExecutor, working_dir: str = None) -> bool:
        """NPM has system scope when no local package.json or node_modules exists."""
        return self._get_npm_location(executor, working_dir) == "system"
