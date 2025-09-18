import os
import subprocess
import time

from ..core.interfaces import EnvironmentExecutor
from typing import Optional


class HostExecutor(EnvironmentExecutor):
    """Executor for running commands on the host system."""

    def __init__(self, debug: bool = False):
        """Initialize Host executor."""
        self.debug = debug

    def execute_command(self, command: str, working_dir: Optional[str] = None) -> tuple[str, str, int]:
        """Execute a command on the host system.

        Returns actual command exit code on success, or 1 for execution environment failures.
        """
        if self.debug:
            start_time = time.perf_counter()
            workdir_info = f" (workdir: {working_dir})" if working_dir else ""
            print(f"Executing host command: {command}{workdir_info}")
        else:
            start_time = None

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

            if self.debug and start_time is not None:
                elapsed_time = time.perf_counter() - start_time
                print(f"Host command completed in {elapsed_time:.3f}s with exit code: {result.returncode}")

            return result.stdout, result.stderr, result.returncode
        except subprocess.TimeoutExpired:
            if self.debug and start_time is not None:
                elapsed_time = time.perf_counter() - start_time
                print(f"Host command timed out after {elapsed_time:.3f}s")
            return "", "Command timed out after 30 seconds", 1
        except (subprocess.SubprocessError, OSError) as e:
            if self.debug and start_time is not None:
                elapsed_time = time.perf_counter() - start_time
                print(f"Host command failed after {elapsed_time:.3f}s: {str(e)}")
            return "", f"Command execution failed: {str(e)}", 1

    def path_exists(self, path: str) -> bool:
        """Check if a path (file or directory) exists on the host system."""
        return os.path.exists(path)
