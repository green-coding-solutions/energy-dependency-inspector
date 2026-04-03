import hashlib
import json
from typing import Optional, Any

from ..core.interfaces import EnvironmentExecutor, PackageManagerDetector


class ComposerDetector(PackageManagerDetector):
    """Detector for PHP packages managed by Composer."""

    NAME = "composer"

    def __init__(self, debug: bool = False):
        self.debug = debug

    def is_usable(self, executor: EnvironmentExecutor, working_dir: Optional[str] = None) -> bool:
        """Check if Composer is usable in the environment."""
        _, _, exit_code = executor.execute_command("composer --version", working_dir)
        return exit_code == 0

    def get_dependencies(
        self, executor: EnvironmentExecutor, working_dir: Optional[str] = None, skip_hash_collection: bool = False
    ) -> dict[str, Any]:
        """Extract Composer dependencies with versions from project and global locations."""
        php_version = self._get_php_version(executor, working_dir)
        project_results = self._get_project_dependencies(executor, working_dir, skip_hash_collection)
        global_result = self._get_global_dependencies(executor, working_dir, skip_hash_collection)

        if len(project_results) == 1 and not global_result:
            if php_version:
                project_results[0]["php_version"] = php_version
            return project_results[0]

        if not project_results and global_result:
            if php_version:
                global_result["php_version"] = php_version
            return global_result

        if project_results or global_result:
            locations = {}

            for project_result in project_results:
                project_location_data = {"scope": "project", "dependencies": project_result["dependencies"]}
                if "hash" in project_result:
                    project_location_data["hash"] = project_result["hash"]
                locations[project_result["location"]] = project_location_data

            if global_result:
                global_location_data = {"scope": "system", "dependencies": global_result["dependencies"]}
                if "hash" in global_result:
                    global_location_data["hash"] = global_result["hash"]
                locations[global_result["location"]] = global_location_data

            result: dict[str, Any] = {"scope": "mixed", "locations": locations}
            if php_version:
                result["php_version"] = php_version
            return result

        if working_dir:
            location = self._resolve_absolute_path(executor, working_dir)
            result = {"scope": "project", "location": location, "dependencies": {}}
            if php_version:
                result["php_version"] = php_version
            return result

        result = {"scope": "system", "location": "/root/.config/composer/vendor", "dependencies": {}}
        if php_version:
            result["php_version"] = php_version
        return result

    def _get_project_dependencies(
        self, executor: EnvironmentExecutor, working_dir: Optional[str] = None, skip_hash_collection: bool = False
    ) -> list[dict[str, Any]]:
        """Get dependencies from all discovered Composer projects."""
        project_dirs = self._find_project_directories(executor, working_dir)
        results: list[dict[str, Any]] = []

        for project_dir in project_dirs:
            stdout, stderr, exit_code = executor.execute_command(
                "composer show --direct --format=json --no-interaction", project_dir
            )
            if exit_code != 0:
                if self.debug:
                    print(f"ERROR: composer project show failed with exit code {exit_code} in {project_dir}")
                    print(f"ERROR: stderr: {stderr}")
                continue

            dependencies = self._parse_dependencies(stdout)
            if not dependencies:
                continue

            location = self._get_project_location(executor, project_dir)
            result: dict[str, Any] = {"scope": "project", "location": location, "dependencies": dependencies}
            if not skip_hash_collection:
                result["hash"] = self._generate_location_hash(executor, location)
            results.append(result)

        return results

    def _find_project_directories(
        self, executor: EnvironmentExecutor, working_dir: Optional[str] = None
    ) -> list[str]:
        """Find all directories containing a composer.json file."""
        try:
            search_root = self._resolve_absolute_path(executor, working_dir or "/")
        except RuntimeError:
            if self.debug:
                print("ERROR: composer project discovery could not resolve scan root")
            return []

        find_command = (
            f"find '{search_root}' "
            "-path '*/vendor/*' -prune -o "
            "-name 'composer.json' -type f -print | sed 's|/composer.json$||' | LC_COLLATE=C sort -u"
        )
        stdout, stderr, exit_code = executor.execute_command(find_command)

        if exit_code != 0:
            if self.debug:
                print(f"ERROR: composer project discovery failed with exit code {exit_code}")
                print(f"ERROR: stderr: {stderr}")
            return []

        return [line.strip() for line in stdout.splitlines() if line.strip()]

    def _get_global_dependencies(
        self, executor: EnvironmentExecutor, working_dir: Optional[str] = None, skip_hash_collection: bool = False
    ) -> dict[str, Any] | None:
        """Get dependencies from Composer's global project."""
        stdout, stderr, exit_code = executor.execute_command(
            "composer global show --direct --format=json --no-interaction", working_dir
        )
        if exit_code != 0:
            if self.debug:
                print(f"ERROR: composer global show failed with exit code {exit_code}")
                print(f"ERROR: stderr: {stderr}")
            return None

        dependencies = self._parse_dependencies(stdout)
        if not dependencies:
            return None

        location = self._get_global_location(executor)
        result: dict[str, Any] = {"scope": "system", "location": location, "dependencies": dependencies}
        if not skip_hash_collection:
            result["hash"] = self._generate_location_hash(executor, location)
        return result

    def _parse_dependencies(self, stdout: str) -> dict[str, dict[str, str]]:
        """Parse JSON output from Composer show commands."""
        try:
            composer_data = json.loads(stdout)
            if not composer_data:
                # when you have a valid composer file but install no packages in it composer will return []
                # which means we can skip early
                return {}
        except json.JSONDecodeError:
            if self.debug:
                print("ERROR: Failed to parse composer show JSON output")
            return {}

        packages = []
        for key in ("installed", "locked", "packages"):
            if isinstance(composer_data.get(key), list):
                packages = composer_data[key]
                break

        dependencies: dict[str, dict[str, str]] = {}
        for package_info in packages:
            if not isinstance(package_info, dict):
                continue

            package_name = package_info.get("name")
            if not package_name:
                continue

            version = package_info.get("version") or package_info.get("pretty_version")
            if not version:
                versions = package_info.get("versions")
                if isinstance(versions, list) and versions:
                    version = str(versions[0])
                else:
                    version = "unknown"

            dependencies[package_name] = {"version": str(version)}

        return dependencies

    def _get_project_location(self, executor: EnvironmentExecutor, working_dir: Optional[str] = None) -> str:
        """Get the absolute Composer vendor directory for the local project."""
        stdout, _, exit_code = executor.execute_command("composer config vendor-dir --absolute", working_dir)
        if exit_code == 0 and stdout.strip():
            return stdout.strip()

        search_dir = working_dir or "/"
        resolved_dir = self._resolve_absolute_path(executor, search_dir)
        return f"{resolved_dir}/vendor"

    def _get_global_location(self, executor: EnvironmentExecutor) -> str:
        """Get the absolute Composer vendor directory for the global project."""
        stdout, _, exit_code = executor.execute_command("composer global config vendor-dir --absolute")
        if exit_code == 0 and stdout.strip():
            return stdout.strip()

        return "/root/.config/composer/vendor"

    def _get_php_version(self, executor: EnvironmentExecutor, working_dir: Optional[str] = None) -> str:
        """Get the PHP runtime version for the Composer environment."""
        stdout, _, exit_code = executor.execute_command("php --version", working_dir)
        if exit_code == 0 and stdout.strip():
            return stdout.splitlines()[0].strip()
        return ""

    def _resolve_absolute_path(self, executor: EnvironmentExecutor, path: str) -> str:
        """Resolve absolute path within the executor's context."""
        if path == "/":
            return "/"
        if path == ".":
            stdout, stderr, exit_code = executor.execute_command("pwd")
            if exit_code == 0 and stdout.strip():
                return stdout.strip()
            raise RuntimeError(f"Failed to resolve current directory in executor context: {stderr}")

        stdout, stderr, exit_code = executor.execute_command(f"cd '{path}' && pwd")
        if exit_code == 0 and stdout.strip():
            return stdout.strip()
        raise RuntimeError(f"Failed to resolve path '{path}' in executor context: {stderr}")

    def _generate_location_hash(self, executor: EnvironmentExecutor, location: str) -> str:
        """Generate a hash based on the contents of the Composer vendor directory."""
        stdout, _, exit_code = executor.execute_command(
            f"cd '{location}' && find . "
            "-name '.git' -prune -o "
            "-name '.composer' -prune -o "
            "-name '*.log' -prune -o "
            "-not -name '*.tmp' "
            "-not -name '*.temp' "
            "\\( -type f -o -type l \\) -printf '%s %p %l\\n' | LC_COLLATE=C sort -n -k1,1 -k2,2"
        )

        if exit_code == 0 and stdout.strip():
            return hashlib.sha256(stdout.strip().encode()).hexdigest()

        if self.debug:
            print(f"ERROR: composer_detector hash generation command failed with exit code {exit_code}")
            print(f"ERROR: location: {location}")
        return ""

    def is_os_package_manager(self) -> bool:
        """Composer is a language package manager, not an OS package manager."""
        return False
