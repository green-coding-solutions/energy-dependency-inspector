#!/usr/bin/env python3
"""
Dependency Resolver - CLI entry point

Usage: dependency_resolver.py [environment_type] [environment_identifier] [options]
"""

import sys
import argparse
from typing import Optional
from executors import HostExecutor, DockerExecutor, DockerComposeExecutor
from core.interfaces import EnvironmentExecutor
from core.orchestrator import Orchestrator


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Resolve dependencies from various package managers",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                                        # Analyze host system
  %(prog)s host                                   # Analyze host system explicitly
  %(prog)s docker a1b2c3d4e5f6                    # Analyze Docker container by ID
  %(prog)s docker nginx                           # Analyze Docker container by name
  %(prog)s docker_compose my_app                  # Analyze Docker Compose stack
  %(prog)s --working-dir /tmp/repo                # Set working directory on target environment
  %(prog)s --venv-path ~/.virtualenvs/myproject   # Use specific virtual environment for pip
  %(prog)s --debug                                # Enable debug output
  %(prog)s --skip-global                          # Skip global package manager detections
        """,
    )

    parser.add_argument(
        "environment_type",
        nargs="?",
        default="host",
        choices=["host", "docker", "docker_compose"],
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
        "--skip-global",
        action="store_true",
        help="Skip global package manager detections (system packages or globally installed Python packages)",
    )

    return parser.parse_args()


def validate_arguments(environment_type: str, environment_identifier: Optional[str]) -> None:
    """Validate command line arguments."""
    if environment_type == "docker" and not environment_identifier:
        print("Error: Docker environment requires a container identifier", file=sys.stderr)
        sys.exit(1)

    if environment_type == "docker_compose" and not environment_identifier:
        print("Error: Docker Compose environment requires a stack identifier", file=sys.stderr)
        sys.exit(1)

    if environment_type == "host" and environment_identifier:
        print("Warning: Environment identifier is ignored for host environment", file=sys.stderr)


def create_executor(environment_type: str, environment_identifier: Optional[str]) -> EnvironmentExecutor:
    """Create executor based on environment type."""
    if environment_type == "host":
        return HostExecutor()
    elif environment_type == "docker":
        return DockerExecutor(environment_identifier)
    elif environment_type == "docker_compose":
        return DockerComposeExecutor(environment_identifier)
    else:
        print(f"Error: Unsupported environment type: {environment_type}", file=sys.stderr)
        sys.exit(1)


def main() -> None:
    """Main entry point."""
    args = parse_arguments()

    validate_arguments(args.environment_type, args.environment_identifier)

    try:
        executor = create_executor(args.environment_type, args.environment_identifier)
        orchestrator = Orchestrator(debug=args.debug, skip_global=args.skip_global, venv_path=args.venv_path)
        result = orchestrator.resolve_and_format(executor, args.working_dir)
        print(result)
    except (RuntimeError, OSError, ValueError) as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
