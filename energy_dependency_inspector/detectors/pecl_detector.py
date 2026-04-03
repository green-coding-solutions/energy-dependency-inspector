from typing import Optional, Any

from ..core.interfaces import EnvironmentExecutor, PackageManagerDetector


class PeclDetector(PackageManagerDetector):
    """Detector for PHP extensions managed by PECL."""

    NAME = "pecl"

    def __init__(self, debug: bool = False):
        self.debug = debug

    def is_usable(self, executor: EnvironmentExecutor, working_dir: Optional[str] = None) -> bool:
        """Check if PECL is usable in the environment."""
        _, _, exit_code = executor.execute_command("pecl version", working_dir)
        return exit_code == 0

    def get_dependencies(
        self, executor: EnvironmentExecutor, working_dir: Optional[str] = None, skip_hash_collection: bool = False
    ) -> dict[str, Any]:
        """Extract installed PECL extensions and PHP version."""
        del skip_hash_collection

        php_version = self._get_php_version(executor, working_dir)
        stdout, stderr, exit_code = executor.execute_command("pecl list", working_dir)

        dependencies: dict[str, dict[str, str]] = {}
        if exit_code == 0:
            dependencies = self._parse_pecl_list(stdout)
        elif self.debug:
            print(f"ERROR: pecl list failed with exit code {exit_code}")
            print(f"ERROR: stderr: {stderr}")

        result: dict[str, Any] = {"scope": "system", "dependencies": dependencies}
        if php_version:
            result["php_version"] = php_version
        return result

    def _get_php_version(self, executor: EnvironmentExecutor, working_dir: Optional[str] = None) -> str:
        """Get the PHP runtime version for the PECL environment."""
        stdout, _, exit_code = executor.execute_command("php --version", working_dir)
        if exit_code == 0 and stdout.strip():
            return stdout.splitlines()[0].strip()
        return ""

    def _parse_pecl_list(self, stdout: str) -> dict[str, dict[str, str]]:
        """Parse `pecl list` output into dependency metadata."""
        dependencies: dict[str, dict[str, str]] = {}

        for line in stdout.splitlines():
            stripped = line.strip().lower()
            if not stripped:
                continue
            if stripped.startswith("installed packages"):
                continue
            if stripped.startswith("package") and stripped.endswith("state"):
                continue
            if set(stripped) == {"="}:
                continue

            parts = stripped.split()
            if len(parts) < 2:
                continue

            package_name, version = parts[0], parts[1]
            dependencies[package_name] = {"version": version}

        return dependencies

    def is_os_package_manager(self) -> bool:
        """PECL is a language package manager, not an OS package manager."""
        return False
