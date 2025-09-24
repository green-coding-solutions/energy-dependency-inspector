#!/usr/bin/env python3
"""
Dependency Resolver - CLI entry point

Usage: python -m dependency_resolver [environment_type] [environment_identifier] [options]
"""

import sys
import argparse


# Check venv before importing modules that might have missing dependencies
from .core.venv_checker import check_venv

check_venv()

from .executors import HostExecutor, DockerExecutor
from .core.interfaces import EnvironmentExecutor
from .core.orchestrator import Orchestrator
from .core.output_formatter import OutputFormatter


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        prog="python -m dependency_resolver",
        description="Resolve dependencies from various package managers",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                                        # Analyze host system
  %(prog)s host                                   # Analyze host system explicitly
  %(prog)s docker a1b2c3d4e5f6                    # Analyze Docker container by ID
  %(prog)s docker nginx                           # Analyze Docker container by name
  %(prog)s --working-dir /tmp/repo                # Set working directory on target environment
  %(prog)s --venv-path ~/.virtualenvs/myproject   # Use specific virtual environment for pip
  %(prog)s --debug                                # Enable debug output
  %(prog)s --skip-os-packages                     # Skip OS package managers (dpkg, apk)
  %(prog)s --skip-hash-collection                 # Skip hash collection for improved performance
  %(prog)s --select-detectors "pip,dpkg"          # Use only pip and dpkg detectors
        """,
    )

    parser.add_argument(
        "environment_type",
        nargs="?",
        default="host",
        choices=["host", "docker"],
        help="Type of environment to analyze",
    )

    parser.add_argument(
        "environment_identifier",
        nargs="?",
        default=None,
        help="Environment identifier (container ID/name for docker)",
    )

    parser.add_argument("--working-dir", type=str, help="Working directory to use in the target environment")

    parser.add_argument("--venv-path", type=str, help="Explicit virtual environment path for pip detector")

    parser.add_argument("--debug", action="store_true", help="Print debug statements")

    parser.add_argument(
        "--skip-os-packages",
        action="store_true",
        help="Skip OS package managers (dpkg, apk) - language package managers like pip/npm will still run",
    )

    parser.add_argument(
        "--only-container-info",
        action="store_true",
        help="For docker environment, only analyze container metadata (skip dependency detection)",
    )

    parser.add_argument(
        "--pretty-print",
        action="store_true",
        help="Format JSON output with indentation",
    )

    parser.add_argument(
        "--skip-hash-collection",
        action="store_true",
        help="Skip hash collection for packages and project locations to improve performance",
    )

    parser.add_argument(
        "--select-detectors",
        type=str,
        help="Comma-separated list of detectors to use (e.g., 'pip,dpkg'). Available: pip, npm, dpkg, apk, maven, docker-info",
    )

    return parser.parse_args()


def validate_arguments(
    environment_type: str, environment_identifier: str | None, only_container_info: bool = False
) -> None:
    """Validate command line arguments."""
    if environment_type == "docker" and not environment_identifier:
        print("Error: Docker environment requires a container identifier", file=sys.stderr)
        sys.exit(1)

    if environment_type == "host" and environment_identifier:
        print("Warning: Environment identifier is ignored for host environment", file=sys.stderr)

    if only_container_info and environment_type != "docker":
        print("Error: --only-container-info flag is only valid for docker environment", file=sys.stderr)
        sys.exit(1)


def create_executor(
    environment_type: str, environment_identifier: str | None, debug: bool = False
) -> EnvironmentExecutor:
    """Create executor based on environment type."""
    if environment_type == "host":
        return HostExecutor(debug=debug)
    elif environment_type == "docker":
        if environment_identifier is None:
            print("Error: Docker environment requires container identifier", file=sys.stderr)
            sys.exit(1)
        return DockerExecutor(environment_identifier, debug=debug)
    else:
        print(f"Error: Unsupported environment type: {environment_type}", file=sys.stderr)
        sys.exit(1)


def main() -> None:
    """Main entry point."""
    args = parse_arguments()

    validate_arguments(args.environment_type, args.environment_identifier, args.only_container_info)

    try:
        executor = create_executor(args.environment_type, args.environment_identifier, debug=args.debug)
        orchestrator = Orchestrator(
            debug=args.debug,
            skip_os_packages=args.skip_os_packages,
            venv_path=args.venv_path,
            skip_hash_collection=args.skip_hash_collection,
            selected_detectors=args.select_detectors,
        )
        dependencies = orchestrator.resolve_dependencies(executor, args.working_dir, args.only_container_info)
        formatter = OutputFormatter(debug=args.debug)
        result = formatter.format_json(dependencies, pretty_print=args.pretty_print)
        print(result)
    except (RuntimeError, OSError, ValueError) as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
