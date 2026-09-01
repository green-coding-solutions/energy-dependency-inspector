#!/usr/bin/env python3
"""
System information collection utilities for benchmarking.

Provides standardized system information collection for performance benchmarks,
including CPU, memory, Docker version, and timestamp data.
"""

import subprocess
import platform
import psutil
from datetime import datetime
from typing import Dict, Union


def get_system_info() -> Dict[str, Union[str, int, float]]:
    """
    Collect comprehensive system information for benchmark context.

    Returns:
        Dict containing system information including:
        - timestamp: Current timestamp (YYYY-MM-DD HH:MM:SS)
        - cpu_cores: Number of physical CPU cores
        - memory_gb: Total system memory in GB (rounded to 1 decimal)
        - docker_version: Docker version string
        - python_version: Python version string
    """
    try:
        # Get Docker version
        docker_result = subprocess.run(["docker", "--version"], capture_output=True, text=True, check=False)
        if docker_result.returncode == 0:
            # Parse "Docker version 24.0.6, build ed223bc" to get "24.0.6"
            version_parts = docker_result.stdout.strip().split()
            docker_version = version_parts[2].rstrip(",") if len(version_parts) >= 3 else "unknown"
        else:
            docker_version = "unknown"

        cpu_cores = psutil.cpu_count(logical=False) or 0

        return {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "cpu_cores": cpu_cores,
            "memory_gb": round(psutil.virtual_memory().total / (1024**3), 1),
            "docker_version": docker_version,
            "python_version": platform.python_version(),
        }
    except (subprocess.SubprocessError, OSError, ImportError) as e:
        print(f"Warning: Could not collect complete system info: {e}")
        return {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "cpu_cores": "unknown",
            "memory_gb": "unknown",
            "docker_version": "unknown",
            "python_version": platform.python_version(),
        }


def get_csv_header_fields() -> str:
    """
    Get CSV header fields for system information.

    Returns:
        Comma-separated string of system info field names for CSV headers.
    """
    return "Timestamp,CPU_Cores,Memory_GB,Docker_Version,Python_Version"


def format_system_info_for_csv(system_info: Dict[str, Union[str, int, float]]) -> str:
    """
    Format system information dictionary as CSV row values.

    Args:
        system_info: Dictionary from get_system_info()

    Returns:
        Comma-separated string of system info values for CSV rows.
    """
    return (
        f"{system_info['timestamp']},{system_info['cpu_cores']},"
        f"{system_info['memory_gb']},{system_info['docker_version']},"
        f"{system_info['python_version']}"
    )
