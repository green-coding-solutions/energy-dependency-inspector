import os
import subprocess

from ..core.interfaces import EnvironmentExecutor


class HostExecutor(EnvironmentExecutor):
    """Executor for running commands on the host system."""

    def execute_command(self, command: str, working_dir: str = None) -> tuple[str, str, int]:
        """Execute a command on the host system.

        Returns actual command exit code on success, or 1 for execution environment failures.
        """
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                cwd=working_dir,
                timeout=30,
                check=False,
            )
            return result.stdout, result.stderr, result.returncode
        except subprocess.TimeoutExpired:
            return "", "Command timed out after 30 seconds", 1
        except (subprocess.SubprocessError, OSError) as e:
            return "", f"Command execution failed: {str(e)}", 1

    def path_exists(self, path: str) -> bool:
        """Check if a path (file or directory) exists on the host system."""
        return os.path.exists(path)
