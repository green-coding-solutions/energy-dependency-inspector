import hashlib
import os
import re
from typing import Optional, Any

from ..core.interfaces import EnvironmentExecutor, PackageManagerDetector


class JavaRuntimeDetector(PackageManagerDetector):
    """Detector for Java runtime environments with JAR files."""

    NAME = "java-runtime"

    def __init__(self, debug: bool = False):
        self.debug = debug
        self._java_available_cache: bool | None = None
        self._java_version_cache: dict[str, str] | None = None

    def is_usable(self, executor: EnvironmentExecutor, working_dir: Optional[str] = None) -> bool:
        """Check if Java runtime is available or JAR files are present."""
        search_dir = working_dir or "."

        # Check for JAR files in working directory
        stdout, _, exit_code = executor.execute_command(
            f"find '{search_dir}' -name '*.jar' -type f | head -1", working_dir
        )
        if exit_code == 0 and stdout.strip():
            return True

        # Check for Java runtime availability
        return self._java_available(executor, working_dir)

    def get_dependencies(self, executor: EnvironmentExecutor, working_dir: Optional[str] = None) -> dict[str, Any]:
        """Extract JAR files and Java runtime information."""
        search_dir = working_dir or "."
        location = self._resolve_absolute_path(executor, search_dir)
        artifacts: dict[str, dict[str, Any]] = {}

        result: dict[str, Any] = {"type": "runtime", "location": location}

        # Discover JAR files
        jar_files = self._discover_jar_files(executor, search_dir)

        # Extract metadata from each JAR
        for jar_path in jar_files:
            jar_info = self._extract_jar_metadata(executor, jar_path, search_dir)
            if jar_info:
                # Use relative path as artifact name
                relative_path = jar_path
                if jar_path.startswith(f"{search_dir}/"):
                    relative_path = jar_path[len(f"{search_dir}/") :]

                # Convert size to integer and add artifact type
                artifact_info = {
                    "version": jar_info.get("version", "unknown"),
                    "size": int(jar_info.get("size", "0")) if jar_info.get("size", "0").isdigit() else 0,
                    "type": "jar",
                    "path": jar_path,
                }
                artifacts[relative_path] = artifact_info

        # Add Java runtime environment info if available
        java_metadata = self._get_java_metadata(executor, working_dir)
        if java_metadata:
            runtime_env = {"platform": "java"}
            if "java_version" in java_metadata:
                runtime_env["version"] = java_metadata["java_version"]
            if "java_vendor" in java_metadata:
                runtime_env["vendor"] = java_metadata["java_vendor"]
            if "java_runtime" in java_metadata:
                runtime_env["runtime"] = java_metadata["java_runtime"]

            result["runtime_environment"] = runtime_env

        # Generate location-based hash if we have artifacts
        if artifacts:
            result["hash"] = self._generate_location_hash(executor, location)

        result["artifacts"] = artifacts
        return result

    def has_system_scope(self, executor: EnvironmentExecutor, working_dir: Optional[str] = None) -> bool:
        """Java runtime detector is always project scope."""
        return False

    def _java_available(self, executor: EnvironmentExecutor, working_dir: Optional[str] = None) -> bool:
        """Check if Java runtime is available."""
        if self._java_available_cache is not None:
            return self._java_available_cache

        _, _, exit_code = executor.execute_command("java -version", working_dir)
        self._java_available_cache = exit_code == 0
        return self._java_available_cache

    def _discover_jar_files(self, executor: EnvironmentExecutor, search_dir: str) -> list[str]:
        """Find all JAR files in the working directory and subdirectories."""
        stdout, stderr, exit_code = executor.execute_command(
            f"find '{search_dir}' -name '*.jar' -type f",
        )

        if exit_code != 0:
            if self.debug:
                print(f"ERROR: JAR file discovery failed: {stderr}")
            return []

        jar_files = []
        for line in stdout.strip().split("\n"):
            jar_path = line.strip()
            if jar_path:
                jar_files.append(jar_path)

        return jar_files

    def _extract_jar_metadata(
        self, executor: EnvironmentExecutor, jar_path: str, working_dir: str  # pylint: disable=unused-argument
    ) -> dict[str, str] | None:
        """Extract metadata from a JAR file."""
        metadata: dict[str, str] = {}

        # Get file size
        stdout, _, exit_code = executor.execute_command(f"stat -f%z '{jar_path}' 2>/dev/null || stat -c%s '{jar_path}'")
        if exit_code == 0 and stdout.strip():
            metadata["size"] = stdout.strip()

        # Try to extract version from manifest
        version = self._extract_version_from_manifest(executor, jar_path)
        if version:
            metadata["version"] = version
        else:
            # Try to extract version from filename
            version = self._extract_version_from_filename(jar_path)
            if version:
                metadata["version"] = version
            else:
                metadata["version"] = "unknown"

        return metadata if metadata else None

    def _extract_version_from_manifest(self, executor: EnvironmentExecutor, jar_path: str) -> str | None:
        """Extract version information from JAR manifest."""
        # Try to read manifest from JAR
        stdout, _, exit_code = executor.execute_command(f"unzip -q -c '{jar_path}' META-INF/MANIFEST.MF 2>/dev/null")

        if exit_code != 0 or not stdout.strip():
            return None

        # Parse manifest for version information
        for line in stdout.split("\n"):
            line = line.strip()
            # Look for common version attributes
            for version_key in ["Implementation-Version", "Bundle-Version", "Version", "Specification-Version"]:
                if line.startswith(f"{version_key}:"):
                    version = line.split(":", 1)[1].strip()
                    if version and version != "null":
                        return version

        return None

    def _extract_version_from_filename(self, jar_path: str) -> str | None:
        """Extract version from JAR filename using common patterns."""
        filename = os.path.basename(jar_path)

        # Remove .jar extension first
        if filename.endswith(".jar"):
            base_name = filename[:-4]
        else:
            base_name = filename

        # Common patterns: name-version.jar, name_version.jar
        # Use more flexible patterns that work with complex names like commons-lang3
        patterns = [
            r"^(.+)[-_](\d+(?:\.\d+)*(?:-[A-Za-z0-9]+)?)$",  # name-1.2.3 or name-1.2.3-SNAPSHOT
            r"^(.+)[-_]v(\d+(?:\.\d+)*)$",  # name-v1.2.3
            r"^(.+?)(\d+(?:\.\d+)*(?:-[A-Za-z0-9]+)?)$",  # name1.2.3 (no separator)
        ]

        for pattern in patterns:
            match = re.match(pattern, base_name)
            if match:
                return match.group(2)

        return None

    def _get_java_metadata(
        self, executor: EnvironmentExecutor, working_dir: Optional[str] = None
    ) -> dict[str, str] | None:
        """Get Java runtime metadata."""
        if not self._java_available(executor, working_dir):
            return None

        if self._java_version_cache is not None:
            return self._java_version_cache

        stdout, stderr, exit_code = executor.execute_command("java -version", working_dir)
        if exit_code != 0:
            return None

        metadata: dict[str, str] = {}

        # Parse java -version output (goes to stderr typically)
        version_output = stderr if stderr else stdout

        # Extract Java version
        version_match = re.search(r'version "([^"]+)"', version_output)
        if version_match:
            metadata["java_version"] = version_match.group(1)

        # Extract vendor/runtime info
        lines = version_output.split("\n")
        for line in lines:
            line = line.strip()
            if "Runtime Environment" in line:
                # Extract runtime name
                runtime_match = re.search(r"([^(]+Runtime Environment)", line)
                if runtime_match:
                    metadata["java_runtime"] = runtime_match.group(1).strip()
            elif "VM" in line and "(" in line:
                # Extract vendor from VM line
                vendor_match = re.search(r"\(([^)]+)\)", line)
                if vendor_match:
                    metadata["java_vendor"] = vendor_match.group(1).strip()

        self._java_version_cache = metadata if metadata else None
        return self._java_version_cache

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
        """Generate a hash based on JAR files and their metadata."""
        stdout, stderr, exit_code = executor.execute_command(
            f"cd '{location}' && find . -name '*.jar' -type f -printf '%s %p\\n' | LC_COLLATE=C sort -k2,2"
        )

        if exit_code == 0 and stdout.strip():
            content = stdout.strip()
            return hashlib.sha256(content.encode()).hexdigest()
        else:
            if self.debug:
                print(f"ERROR: java_runtime_detector hash generation command failed with exit code {exit_code}")
                print(f"ERROR: location: {location}")
                print(f"ERROR: stderr: {stderr}")
            return ""
