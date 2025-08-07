import hashlib
from typing import Dict, Any

from core.interfaces import EnvironmentExecutor, PackageManagerDetector


class DpkgDetector(PackageManagerDetector):
    """Detector for system packages managed by dpkg (Debian/Ubuntu)."""

    NAME = "dpkg"

    def is_usable(self, executor: EnvironmentExecutor, working_dir: str = None) -> bool:
        """Check if dpkg is usable (running on Debian/Ubuntu and dpkg-query is available)."""
        stdout, _, exit_code = executor.execute_command("cat /etc/os-release")
        if exit_code == 0:
            os_info = stdout.lower()
            meets_requirements = "debian" in os_info or "ubuntu" in os_info
        else:
            meets_requirements = executor.file_exists("/etc/debian_version")

        if not meets_requirements:
            return False

        _, _, dpkg_exit_code = executor.execute_command("dpkg-query --version")
        return dpkg_exit_code == 0

    def get_dependencies(self, executor: EnvironmentExecutor, working_dir: str = None) -> Dict[str, Any]:
        """Extract system packages with versions using dpkg-query.

        Uses dpkg-query -W -f for reliable package information extraction.
        See docs/adr/0003-dpkg-query-for-package-information.md
        """
        command = "dpkg-query -W -f='${Package}\t${Version}\t${Architecture}\n'"
        stdout, _, exit_code = executor.execute_command(command, working_dir)

        if exit_code != 0:
            return {"scope": "system", "dependencies": {}}

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

                    package_hash = self._get_package_hash(executor, package_name)
                    if package_hash:
                        package_data["hash"] = package_hash

                    dependencies[package_name] = package_data

        return {"scope": "system", "dependencies": dependencies}

    def _get_package_hash(self, executor: EnvironmentExecutor, package_name: str) -> str:
        """Get package hash from dpkg md5sums file if available.

        Extracts MD5 hashes from /var/lib/dpkg/info/{package}.md5sums and combines into SHA256.
        See docs/adr/0008-apt-md5-hash-extraction.md and docs/adr/0005-hash-generation-strategy.md
        """
        md5sums_file = f"/var/lib/dpkg/info/{package_name}.md5sums"

        if not executor.file_exists(md5sums_file):
            return None

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
            pass

        return None

    def has_system_scope(self, executor: EnvironmentExecutor, working_dir: str = None) -> bool:
        """DPKG always has system scope (system packages)."""
        return True
