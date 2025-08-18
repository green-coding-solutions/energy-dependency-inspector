"""DependencyResolver class for managing dependency resolution operations."""

from typing import Optional, Any, Callable, Dict, List
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
import time

from .interfaces import EnvironmentExecutor
from .orchestrator import Orchestrator
from .output_formatter import OutputFormatter
from ..executors import HostExecutor, DockerExecutor, DockerComposeExecutor


@dataclass
class ResolveRequest:
    """Configuration for a single dependency resolution request."""

    environment_type: str
    environment_identifier: Optional[str] = None
    working_dir: Optional[str] = None
    venv_path: Optional[str] = None
    only_container_info: bool = False
    # Optional metadata for tracking
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ResolveResult:
    """Result of a dependency resolution operation."""

    request: ResolveRequest
    dependencies: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    execution_time: float = 0.0
    success: bool = False


class DependencyResolver:
    """
    Main class for dependency resolution operations.

    Supports both single and batch resolution with parallel processing.
    """

    def __init__(
        self,
        debug: bool = False,
        skip_system_scope: bool = False,
        max_workers: Optional[int] = None,
    ):
        """
        Initialize the dependency resolver.

        Args:
            debug: Enable debug output
            skip_system_scope: Skip system-scope package managers
            max_workers: Maximum number of worker threads for parallel operations
        """
        self.debug = debug
        self.skip_system_scope = skip_system_scope
        self.max_workers = max_workers
        self.formatter = OutputFormatter(debug=debug)

    def resolve(
        self,
        environment_type: str = "host",
        environment_identifier: Optional[str] = None,
        working_dir: Optional[str] = None,
        venv_path: Optional[str] = None,
        only_container_info: bool = False,
    ) -> Dict[str, Any]:
        """
        Resolve dependencies for a single environment.

        Args:
            environment_type: Type of environment ("host", "docker", "docker_compose")
            environment_identifier: Environment identifier (required for docker/docker_compose)
            working_dir: Working directory to analyze
            venv_path: Explicit virtual environment path for pip detector
            only_container_info: Only analyze container metadata (for docker environments)

        Returns:
            Dictionary containing all discovered dependencies
        """
        # Validate inputs early to provide clear error messages
        if environment_type not in ["host", "docker", "docker_compose"]:
            raise ValueError(f"Unsupported environment type: {environment_type}")

        if environment_type == "docker" and not environment_identifier:
            raise ValueError("Docker environment requires container identifier")

        if environment_type == "docker_compose" and not environment_identifier:
            raise ValueError("Docker Compose environment requires service identifier")

        request = ResolveRequest(
            environment_type=environment_type,
            environment_identifier=environment_identifier,
            working_dir=working_dir,
            venv_path=venv_path,
            only_container_info=only_container_info,
        )

        result = self._resolve_single(request)
        if not result.success:
            raise RuntimeError(f"Resolution failed: {result.error}")

        return result.dependencies or {}

    def resolve_batch(
        self,
        requests: List[ResolveRequest],
        progress_callback: Optional[Callable[[int, int, ResolveResult], None]] = None,
        fail_fast: bool = False,
    ) -> List[ResolveResult]:
        """
        Resolve dependencies for multiple environments in parallel.

        Args:
            requests: List of resolution requests
            progress_callback: Optional callback for progress updates (completed, total, result)
            fail_fast: Stop processing on first error

        Returns:
            List of results in the same order as requests
        """
        if not requests:
            return []

        results: List[Optional[ResolveResult]] = [None] * len(requests)
        completed_count = 0

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all tasks
            future_to_index = {executor.submit(self._resolve_single, request): i for i, request in enumerate(requests)}

            # Process completed futures
            for future in as_completed(future_to_index):
                index = future_to_index[future]
                result = future.result()
                results[index] = result
                completed_count += 1

                # Call progress callback if provided
                if progress_callback:
                    progress_callback(completed_count, len(requests), result)

                # Handle fail_fast mode
                if fail_fast and not result.success:
                    # Cancel remaining futures
                    for remaining_future in future_to_index:
                        if not remaining_future.done():
                            remaining_future.cancel()
                    break

        return [r for r in results if r is not None]

    def resolve_batch_as_dict(
        self,
        requests: List[ResolveRequest],
        include_errors: bool = True,
        progress_callback: Optional[Callable[[int, int, ResolveResult], None]] = None,
    ) -> Dict[str, Any]:
        """
        Resolve dependencies in batch and return as a single dictionary.

        Args:
            requests: List of resolution requests
            include_errors: Include error information in results
            progress_callback: Optional callback for progress updates

        Returns:
            Dictionary with results keyed by environment identifier or index
        """
        results = self.resolve_batch(requests, progress_callback=progress_callback)

        output = {}
        for i, result in enumerate(results):
            # Generate a key for this result
            key = result.request.environment_identifier or f"request_{i}"

            if result.success:
                output[key] = result.dependencies
            elif include_errors:
                output[key] = {
                    "error": result.error,
                    "execution_time": result.execution_time,
                    "request": {
                        "environment_type": result.request.environment_type,
                        "environment_identifier": result.request.environment_identifier,
                        "working_dir": result.request.working_dir,
                    },
                }

        return output

    def _resolve_single(self, request: ResolveRequest) -> ResolveResult:
        """
        Internal method to resolve dependencies for a single request.

        Args:
            request: The resolution request

        Returns:
            ResolveResult containing the outcome
        """
        start_time = time.time()

        try:
            # Create appropriate executor
            executor = self._create_executor(request)

            # Create orchestrator with request-specific configuration
            orchestrator = Orchestrator(
                debug=self.debug, skip_system_scope=self.skip_system_scope, venv_path=request.venv_path
            )

            # Resolve dependencies
            dependencies = orchestrator.resolve_dependencies(executor, request.working_dir, request.only_container_info)

            execution_time = time.time() - start_time

            return ResolveResult(
                request=request, dependencies=dependencies, execution_time=execution_time, success=True
            )

        except (RuntimeError, OSError, ValueError) as e:
            execution_time = time.time() - start_time
            error_msg = str(e)

            if self.debug:
                print(f"Error resolving {request.environment_type}: {error_msg}")

            return ResolveResult(request=request, error=error_msg, execution_time=execution_time, success=False)

    def _create_executor(self, request: ResolveRequest) -> EnvironmentExecutor:
        """
        Create the appropriate executor for the given request.

        Args:
            request: The resolution request

        Returns:
            Configured executor instance
        """
        if request.environment_type == "host":
            return HostExecutor()
        elif request.environment_type == "docker":
            if not request.environment_identifier:
                raise ValueError("Docker environment requires container identifier")
            return DockerExecutor(request.environment_identifier)
        elif request.environment_type == "docker_compose":
            if not request.environment_identifier:
                raise ValueError("Docker Compose environment requires service identifier")
            return DockerComposeExecutor(request.environment_identifier)
        else:
            raise ValueError(f"Unsupported environment type: {request.environment_type}")
