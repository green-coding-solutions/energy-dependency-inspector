import hashlib
from typing import Dict, Any

from core.interfaces import EnvironmentExecutor, PackageManagerDetector


class AptDetector(PackageManagerDetector):
    """Detector for system packages managed by apt/dpkg (Debian/Ubuntu)."""

    NAME = "apt"

    def meets_requirements(self, executor: EnvironmentExecutor) -> bool:
        """Check if running on Debian/Ubuntu."""
        stdout, _, exit_code = executor.execute_command("cat /etc/os-release")
        if exit_code == 0:
            os_info = stdout.lower()
            return "debian" in os_info or "ubuntu" in os_info

        return executor.file_exists("/etc/debian_version")

    def is_available(self, executor: EnvironmentExecutor) -> bool:
        """Check if dpkg-query is available."""
        _, _, dpkg_exit_code = executor.execute_command("dpkg-query --version")
        return dpkg_exit_code == 0

    def get_dependencies(self, executor: EnvironmentExecutor, working_dir: str = None) -> Dict[str, Any]:
        """Extract system packages with versions using dpkg-query."""
        command = "dpkg-query -W -f='${Package}\t${Version}\t${Architecture}\n'"
        stdout, _, exit_code = executor.execute_command(command, working_dir)

        if exit_code != 0:
            return {"location": "global", "dependencies": {}}

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

        return {"location": "global", "dependencies": dependencies}

    def _get_package_hash(self, executor: EnvironmentExecutor, package_name: str) -> str:
        """Get package hash from dpkg md5sums file if available."""
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
                    return hashlib.sha256(content.encode()).hexdigest()[:32]
        except (OSError, IOError):
            pass

        return None
