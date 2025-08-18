"""Dependency Resolver - A tool for analyzing dependencies across multiple package managers."""

from .core.interfaces import EnvironmentExecutor
from .core.orchestrator import Orchestrator
from .core.output_formatter import OutputFormatter
from .core.resolver import DependencyResolver, ResolveRequest, ResolveResult
from .executors import HostExecutor, DockerExecutor, DockerComposeExecutor

from typing import Optional, Any


def resolve_host_dependencies(
    working_dir: Optional[str] = None,
    debug: bool = False,
    skip_system_scope: bool = False,
    venv_path: Optional[str] = None,
    pretty_print: bool = False,
) -> str:
    """
    Convenience function to resolve dependencies on the host system.

    Args:
        working_dir: Working directory to analyze (defaults to current directory)
        debug: Enable debug output
        skip_system_scope: Skip system-scope package managers
        venv_path: Explicit virtual environment path for pip detector
        pretty_print: Format JSON output with indentation

    Returns:
        JSON string containing all discovered dependencies
    """
    executor = HostExecutor()
    orchestrator = Orchestrator(debug=debug, skip_system_scope=skip_system_scope, venv_path=venv_path)
    dependencies = orchestrator.resolve_dependencies(executor, working_dir)
    formatter = OutputFormatter(debug=debug)
    return formatter.format_json(dependencies, pretty_print=pretty_print)


def resolve_docker_dependencies(
    container_identifier: str,
    working_dir: Optional[str] = None,
    debug: bool = False,
    skip_system_scope: bool = False,
    venv_path: Optional[str] = None,
    only_container_info: bool = False,
    pretty_print: bool = False,
) -> str:
    """
    Convenience function to resolve dependencies in a Docker container.

    Args:
        container_identifier: Container ID or name
        working_dir: Working directory to analyze within the container
        debug: Enable debug output
        skip_system_scope: Skip system-scope package managers
        venv_path: Explicit virtual environment path for pip detector
        only_container_info: Only analyze container metadata (skip dependency detection)
        pretty_print: Format JSON output with indentation

    Returns:
        JSON string containing all discovered dependencies
    """
    executor = DockerExecutor(container_identifier)
    orchestrator = Orchestrator(debug=debug, skip_system_scope=skip_system_scope, venv_path=venv_path)
    dependencies = orchestrator.resolve_dependencies(executor, working_dir, only_container_info)
    formatter = OutputFormatter(debug=debug)
    return formatter.format_json(dependencies, pretty_print=pretty_print)


def resolve_dependencies_as_dict(
    environment_type: str = "host",
    environment_identifier: Optional[str] = None,
    working_dir: Optional[str] = None,
    debug: bool = False,
    skip_system_scope: bool = False,
    venv_path: Optional[str] = None,
    only_container_info: bool = False,
) -> dict[str, Any]:
    """
    Generic function to resolve dependencies and return as a Python dictionary.

    Args:
        environment_type: Type of environment ("host", "docker", "docker_compose")
        environment_identifier: Environment identifier (required for docker/docker_compose)
        working_dir: Working directory to analyze
        debug: Enable debug output
        skip_system_scope: Skip system-scope package managers
        venv_path: Explicit virtual environment path for pip detector
        only_container_info: Only analyze container metadata (for docker environments)

    Returns:
        Dictionary containing all discovered dependencies
    """
    executor: EnvironmentExecutor
    if environment_type == "host":
        executor = HostExecutor()
    elif environment_type == "docker":
        if not environment_identifier:
            raise ValueError("Docker environment requires container identifier")
        executor = DockerExecutor(environment_identifier)
    elif environment_type == "docker_compose":
        if not environment_identifier:
            raise ValueError("Docker Compose environment requires service identifier")
        executor = DockerComposeExecutor(environment_identifier)
    else:
        raise ValueError(f"Unsupported environment type: {environment_type}")

    orchestrator = Orchestrator(debug=debug, skip_system_scope=skip_system_scope, venv_path=venv_path)
    return orchestrator.resolve_dependencies(executor, working_dir, only_container_info)


def main() -> None:
    """CLI entry point for installed package (used by dependency-resolver command)."""
    # pylint: disable=import-outside-toplevel
    from .__main__ import main as cli_main

    cli_main()
