import os
import subprocess
from typing import Tuple

from .interfaces import EnvironmentExecutor


class HostExecutor(EnvironmentExecutor):
    """Executor for running commands on the host system."""

    def execute_command(self, command: str, working_dir: str = None) -> Tuple[str, str, int]:
        """Execute a command on the host system.

        Args:
            command: The command to execute
            working_dir: Optional working directory

        Returns:
            Tuple of (stdout, stderr, exit_code)
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

    def file_exists(self, path: str) -> bool:
        """Check if a file exists on the host system.

        Args:
            path: Path to check

        Returns:
            True if file exists, False otherwise
        """
        return os.path.exists(path)
