import hashlib
from typing import Optional, Any

from ..core.interfaces import EnvironmentExecutor, PackageManagerDetector


class DpkgDetector(PackageManagerDetector):
    """Detector for system packages managed by dpkg (Debian/Ubuntu)."""

    NAME = "dpkg"

    def __init__(self) -> None:
        self._batch_hash_cache: dict[str, str] | None = None

    def is_usable(self, executor: EnvironmentExecutor, working_dir: Optional[str] = None) -> bool:
        """Check if dpkg is usable (running on Debian/Ubuntu and dpkg-query is available)."""
        stdout, _, exit_code = executor.execute_command("cat /etc/os-release")
        if exit_code == 0:
            os_info = stdout.lower()
            meets_requirements = "debian" in os_info or "ubuntu" in os_info
        else:
            meets_requirements = executor.path_exists("/etc/debian_version")

        if not meets_requirements:
            return False

        _, _, dpkg_exit_code = executor.execute_command("dpkg-query --version")
        return dpkg_exit_code == 0

    def get_dependencies(
        self, executor: EnvironmentExecutor, working_dir: Optional[str] = None, skip_hash_collection: bool = False
    ) -> dict[str, Any]:
        """Extract system packages with versions using dpkg-query.

        Uses dpkg-query -W -f for reliable package information extraction.
        See docs/technical/detectors/dpkg_detector.md
        """
        command = "dpkg-query -W -f='${Package}\t${Version}\t${Architecture}\n'"
        stdout, _, exit_code = executor.execute_command(command, working_dir)

        if exit_code != 0:
            return {"scope": "system", "dependencies": {}}

        # Collect all package hashes in a single batch operation (unless skipped)
        batch_hashes = {} if skip_hash_collection else self._collect_all_package_hashes(executor)

        dependencies = {}
        for line in stdout.strip().split("\n"):
            if line and "\t" in line:
                parts = line.split("\t")
                if len(parts) >= 2:
                    package_name = parts[0].strip()
                    version = parts[1].strip()
                    architecture = parts[2].strip() if len(parts) > 2 else ""

                    full_version = f"{version} {architecture}" if architecture else version

                    package_data = {
                        "version": full_version,
                    }

                    # Skip hash collection if requested
                    if not skip_hash_collection:
                        # Use batch-collected hash or fallback to individual lookup
                        package_hash = batch_hashes.get(package_name)
                        if not package_hash:
                            package_hash = self._get_package_hash(executor, package_name, architecture)

                        if package_hash:
                            package_data["hash"] = package_hash

                    dependencies[package_name] = package_data

        return {"scope": "system", "dependencies": dependencies}

    def _get_package_hash(self, executor: EnvironmentExecutor, package_name: str, architecture: str = "") -> str | None:
        """Get package hash from dpkg md5sums file if available.

        Extracts MD5 hashes from /var/lib/dpkg/info/{package}.md5sums and combines into SHA256.
        Tries multiple file patterns to handle architecture-specific naming.
        See docs/technical/detectors/dpkg_detector.md
        """
        # Try different md5sums file patterns in order of preference
        patterns = [
            f"/var/lib/dpkg/info/{package_name}.md5sums",  # Standard pattern
        ]

        # Add architecture-specific patterns if architecture is available
        if architecture:
            patterns.extend(
                [
                    f"/var/lib/dpkg/info/{package_name}:{architecture}.md5sums",  # Multi-arch pattern
                    f"/var/lib/dpkg/info/{package_name}-{architecture}.md5sums",  # Alternative pattern
                ]
            )

        for md5sums_file in patterns:
            if executor.path_exists(md5sums_file):
                try:
                    stdout, _, exit_code = executor.execute_command(f"cat '{md5sums_file}'")
                    if exit_code == 0 and stdout.strip():
                        md5_hashes = []
                        for line in stdout.strip().split("\n"):
                            if line and " " in line:
                                md5_hash = line.split(" ")[0].strip()
                                if md5_hash:
                                    md5_hashes.append(md5_hash)

                        if md5_hashes:
                            content = "\n".join(sorted(md5_hashes))
                            return hashlib.sha256(content.encode()).hexdigest()
                except (OSError, IOError):
                    continue  # Try next pattern

        return None

    def _collect_all_package_hashes(self, executor: EnvironmentExecutor) -> dict[str, str]:
        """Collect all package hashes in a single batch operation.

        Uses a single command to read all .md5sums files at once,
        reducing subprocess overhead across all execution environments.

        Returns:
            Dict mapping package names to their combined SHA256 hash
        """
        if self._batch_hash_cache is not None:
            return self._batch_hash_cache

        # Single command with shell loop - environment agnostic
        command = """
cd /var/lib/dpkg/info 2>/dev/null && \
for file in *.md5sums; do
    if [ -f "$file" ]; then
        echo "FILE:$file"
        cat "$file" 2>/dev/null || true
    fi
done
"""

        stdout, _, exit_code = executor.execute_command(command)

        if exit_code != 0:
            self._batch_hash_cache = {}
            return self._batch_hash_cache

        # Parse batch output into per-package hashes
        self._batch_hash_cache = self._parse_batch_hash_output(stdout)
        return self._batch_hash_cache

    def _parse_batch_hash_output(self, batch_output: str) -> dict[str, str]:
        """Parse batch hash collection output into per-package hashes.

        Args:
            batch_output: Output from batch find command with FILE: markers

        Returns:
            Dict mapping package names to their combined SHA256 hash
        """
        package_hashes = {}
        current_package = None
        current_md5s: list[str] = []

        for line in batch_output.strip().split("\n"):
            line = line.strip()
            if line.startswith("FILE:"):
                # Process previous package if we have one
                if current_package and current_md5s:
                    combined_hash = self._combine_md5_hashes(current_md5s)
                    if combined_hash:
                        package_hashes[current_package] = combined_hash

                # Extract package name from filename
                filename = line[5:].strip()  # Remove 'FILE:' prefix
                current_package = self._extract_package_name_from_path(filename)
                current_md5s = []

            elif line and current_package:
                # Extract MD5 hash from line (format: "hash  filepath")
                if " " in line:
                    md5_hash = line.split(" ")[0].strip()
                    if md5_hash and len(md5_hash) == 32:  # Valid MD5 hash length
                        current_md5s.append(md5_hash)

        # Process final package
        if current_package and current_md5s:
            combined_hash = self._combine_md5_hashes(current_md5s)
            if combined_hash:
                package_hashes[current_package] = combined_hash

        return package_hashes

    def _extract_package_name_from_path(self, filename: str) -> str:
        """Extract package name from .md5sums filename.

        Handles various naming patterns:
        - package.md5sums -> package
        - package:arch.md5sums -> package
        - package-arch.md5sums -> package
        """
        # Remove .md5sums extension
        if filename.endswith(".md5sums"):
            package_part = filename[:-8]  # Remove '.md5sums'
        else:
            package_part = filename

        # Handle architecture patterns
        if ":" in package_part:
            # Multi-arch pattern: package:arch
            return package_part.split(":")[0]
        elif "-" in package_part and package_part.count("-") >= 1:
            # Could be package-arch or package-with-dashes
            # Check if last part looks like architecture
            parts = package_part.rsplit("-", 1)
            if len(parts) == 2 and parts[1] in ["amd64", "i386", "arm64", "armhf", "all"]:
                return parts[0]

        return package_part

    def _combine_md5_hashes(self, md5_hashes: list[str]) -> str | None:
        """Combine multiple MD5 hashes into a single SHA256 hash."""
        if not md5_hashes:
            return None

        content = "\n".join(sorted(md5_hashes))
        return hashlib.sha256(content.encode()).hexdigest()

    def is_os_package_manager(self) -> bool:
        """DPKG manages OS-level packages."""
        return True
