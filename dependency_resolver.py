#!/usr/bin/env python3
"""
Dependency Resolver - CLI entry point

Usage: dependency_resolver.py [environment_type] [environment_identifier] [options]
"""

import sys
import argparse
from core.executor import HostExecutor, DockerExecutor, EnvironmentExecutor
from core.resolver import DependencyResolver


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Resolve dependencies from various package managers",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                              # Analyze host system
  %(prog)s host                         # Analyze host system explicitly
  %(prog)s docker a1b2c3d4e5f6          # Analyze Docker container by ID
  %(prog)s docker nginx                 # Analyze Docker container by name
  %(prog)s --working-dir /tmp/repo      # Set working directory on host
  %(prog)s --debug                      # Enable debug output
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

    parser.add_argument("--debug", action="store_true", help="Print debug statements")

    return parser.parse_args()


def main() -> None:
    """Main entry point."""
    args = parse_arguments()

    # Validate arguments
    if args.environment_type == "docker" and not args.environment_identifier:
        print("Error: Docker environment requires a container identifier", file=sys.stderr)
        sys.exit(1)

    if args.environment_type == "host" and args.environment_identifier:
        print("Warning: Environment identifier is ignored for host environment", file=sys.stderr)

    try:
        # Create executor based on environment type
        executor: EnvironmentExecutor
        if args.environment_type == "host":
            executor = HostExecutor()
        elif args.environment_type == "docker":
            executor = DockerExecutor(args.environment_identifier)
        else:
            print(f"Error: Unsupported environment type: {args.environment_type}", file=sys.stderr)
            sys.exit(1)

        # Create resolver and resolve dependencies
        resolver = DependencyResolver(debug=args.debug)
        result = resolver.resolve_and_format(executor, args.working_dir)

        # Output result
        print(result)

    except (RuntimeError, OSError, ValueError) as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
