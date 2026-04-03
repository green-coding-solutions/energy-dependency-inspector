import hashlib
import re
import xml.etree.ElementTree as ET
from typing import Optional, Any

from ..core.interfaces import EnvironmentExecutor, PackageManagerDetector


class MavenDetector(PackageManagerDetector):
    """Detector for Maven-based Java projects."""

    NAME = "maven"

    def __init__(self, debug: bool = False):
        self.debug = debug

    def is_usable(self, executor: EnvironmentExecutor, working_dir: Optional[str] = None) -> bool:
        """Check if at least one Maven project exists under the scan root."""
        return len(self._find_project_directories(executor, working_dir)) > 0

    def get_dependencies(
        self, executor: EnvironmentExecutor, working_dir: Optional[str] = None, skip_hash_collection: bool = False
    ) -> dict[str, Any]:
        """Extract Maven dependencies with versions.

        Returns:
            tuple: (packages, metadata)
            - packages: List of package dicts with name, version, type
            - metadata: Dict with location and hash for project scope
        """
        project_dirs = self._find_project_directories(executor, working_dir)
        results: list[dict[str, Any]] = []

        for project_dir in project_dirs:
            dependencies: dict[str, dict[str, str]]

            if self._maven_available(executor, project_dir):
                dependencies = self._get_dependencies_via_maven(executor, project_dir)
            else:
                dependencies = self._get_dependencies_via_pom_parsing(executor, project_dir)

            if not dependencies:
                continue

            result: dict[str, Any] = {"scope": "project", "location": project_dir, "dependencies": dependencies}
            if not skip_hash_collection:
                result["hash"] = self._generate_location_hash(executor, project_dir)
            results.append(result)

        if len(results) > 1:
            locations = {}
            for project_result in results:
                location_data = {"scope": "project", "dependencies": project_result["dependencies"]}
                if "hash" in project_result:
                    location_data["hash"] = project_result["hash"]
                locations[project_result["location"]] = location_data
            return {"scope": "mixed", "locations": locations}

        if len(results) == 1:
            return results[0]

        search_root = self._resolve_absolute_path(executor, working_dir or "/")
        return {"scope": "project", "location": search_root, "dependencies": {}}

    def is_os_package_manager(self) -> bool:
        """Maven is a language package manager, not an OS package manager."""
        return False

    def _maven_available(self, executor: EnvironmentExecutor, working_dir: Optional[str] = None) -> bool:
        """Check if Maven is available in the environment."""
        # Check for Maven wrapper first (project-specific)
        search_dir = working_dir or "/"
        if executor.path_exists(f"{search_dir}/mvnw"):
            _, _, exit_code = executor.execute_command("./mvnw --version", working_dir)
            if exit_code == 0:
                return True

        # Fall back to system Maven
        _, _, exit_code = executor.execute_command("mvn --version", working_dir)
        return exit_code == 0

    def _get_maven_command(self, executor: EnvironmentExecutor, working_dir: Optional[str] = None) -> str:
        """Determine which Maven command to use (wrapper first, then system)."""
        search_dir = working_dir or "/"
        if executor.path_exists(f"{search_dir}/mvnw"):
            _, _, exit_code = executor.execute_command("./mvnw --version", working_dir)
            if exit_code == 0:
                return "./mvnw"
        return "mvn"

    def _get_dependencies_via_maven(
        self, executor: EnvironmentExecutor, working_dir: Optional[str] = None
    ) -> dict[str, dict[str, str]]:
        """Extract dependencies using Maven command."""
        # Determine which Maven command to use
        maven_cmd = self._get_maven_command(executor, working_dir)

        stdout, stderr, exit_code = executor.execute_command(
            f"{maven_cmd} dependency:list -B -q -DoutputFile=/dev/stdout -DexcludeTransitive=true", working_dir
        )

        if exit_code != 0:
            if self.debug:
                print(f"ERROR: Maven dependency:list failed with exit code {exit_code}")
                print(f"ERROR: stderr: {stderr}")
            return {}

        dependencies: dict[str, dict[str, str]] = {}

        # Parse Maven dependency:list output
        # Format: groupId:artifactId:type:version:scope
        for line in stdout.strip().split("\n"):
            original_line = line
            line = line.strip()
            if not line or line.startswith("[") or "The following files have been resolved:" in line:
                continue

            # Match Maven coordinate format - look for lines that originally had leading spaces and contain ':'
            if original_line.startswith(" ") and ":" in line:
                # Clean the line from ANSI codes and extra whitespace
                clean_line = line.strip()

                # Split on colon to get Maven coordinates
                parts = clean_line.split(":")
                if len(parts) >= 5:
                    group_id = parts[0].strip()
                    artifact_id = parts[1].strip()
                    version = parts[3].strip()
                    scope_with_extra = parts[4].strip()

                    # Extract scope by removing ANSI codes and extra text
                    # Scope is everything before the first ANSI escape sequence or special character
                    scope = re.split(r"[\x1b\s]", scope_with_extra)[0].strip()

                    # Include compile, runtime, and provided scopes; exclude test
                    if scope in ("compile", "runtime", "provided"):
                        package_name = f"{group_id}:{artifact_id}"
                        dependencies[package_name] = {"version": version}

        return dependencies

    def _get_dependencies_via_pom_parsing(
        self, executor: EnvironmentExecutor, search_dir: str
    ) -> dict[str, dict[str, str]]:
        """Extract dependencies by parsing pom.xml directly."""
        pom_path = f"{search_dir}/pom.xml"

        # Read pom.xml content
        stdout, stderr, exit_code = executor.execute_command(f"cat '{pom_path}'")
        if exit_code != 0:
            if self.debug:
                print(f"ERROR: Failed to read pom.xml: {stderr}")
            return {}

        try:
            # Parse XML content
            root = ET.fromstring(stdout)

            # Handle XML namespaces
            namespace = ""
            if root.tag.startswith("{"):
                namespace = root.tag[root.tag.find("{") : root.tag.find("}") + 1]

            dependencies: dict[str, dict[str, str]] = {}

            # Find dependencies section
            deps_element = root.find(f"{namespace}dependencies")
            if deps_element is not None:
                for dep in deps_element.findall(f"{namespace}dependency"):
                    group_id_elem = dep.find(f"{namespace}groupId")
                    artifact_id_elem = dep.find(f"{namespace}artifactId")
                    version_elem = dep.find(f"{namespace}version")
                    scope_elem = dep.find(f"{namespace}scope")

                    if group_id_elem is not None and artifact_id_elem is not None:
                        group_id = group_id_elem.text or ""
                        artifact_id = artifact_id_elem.text or ""
                        version = version_elem.text if version_elem is not None else "unknown"
                        scope = scope_elem.text if scope_elem is not None else "compile"

                        # Skip test-scoped dependencies by default
                        if scope != "test":
                            package_name = f"{group_id}:{artifact_id}"
                            resolved_version = self._resolve_version_properties(version or "unknown", root, namespace)
                            dependencies[package_name] = {"version": resolved_version}

            return dependencies

        except ET.ParseError as e:
            if self.debug:
                print(f"ERROR: Failed to parse pom.xml: {e}")
            return {}

    def _find_project_directories(
        self, executor: EnvironmentExecutor, working_dir: Optional[str] = None
    ) -> list[str]:
        """Find all directories containing a pom.xml file under the scan root."""
        search_root = self._resolve_absolute_path(executor, working_dir or "/")
        stdout, stderr, exit_code = executor.execute_command(
            f"find '{search_root}' "
            "-path '*/target/*' -prune -o "
            "-path '*/.m2/*' -prune -o "
            "-name 'pom.xml' -type f -print 2>/dev/null | sed 's|/pom.xml$||' | LC_COLLATE=C sort -u"
        )

        if exit_code != 0:
            if self.debug:
                print(f"ERROR: Maven project discovery failed with exit code {exit_code}")
                print(f"ERROR: stderr: {stderr}")
            return []

        return [line.strip() for line in stdout.splitlines() if line.strip()]

    def _resolve_version_properties(self, version: str, root: ET.Element, namespace: str) -> str:
        """Attempt to resolve Maven property placeholders in version strings."""
        if not version.startswith("${") or not version.endswith("}"):
            return version

        # Extract property name
        prop_name = version[2:-1]

        # Look for property in properties section
        properties = root.find(f"{namespace}properties")
        if properties is not None:
            prop_elem = properties.find(f"{namespace}{prop_name}")
            if prop_elem is not None and prop_elem.text:
                return prop_elem.text

        # Check for common built-in properties
        if prop_name == "project.version":
            version_elem = root.find(f"{namespace}version")
            if version_elem is not None and version_elem.text:
                return version_elem.text

        # Return original if we can't resolve
        return version

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
        """Generate a hash based on the Maven project files."""
        stdout, _, exit_code = executor.execute_command(
            f"cd '{location}' && find . "
            "-name 'target' -prune -o "
            "-name '.m2' -prune -o "
            "\\( -name 'pom.xml' -o -name '*.properties' \\) "
            "-type f -printf '%s %p\\n' | LC_COLLATE=C sort -n -k1,1 -k2,2"
        )

        if exit_code == 0 and stdout.strip():
            content = stdout.strip()
            return hashlib.sha256(content.encode()).hexdigest()
        else:
            if self.debug:
                print(f"ERROR: maven_detector hash generation command failed with exit code {exit_code}")
                print(f"ERROR: location: {location}")
            return ""
