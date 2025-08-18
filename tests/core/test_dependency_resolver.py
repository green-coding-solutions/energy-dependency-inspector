"""Tests for the DependencyResolver class."""

import pytest
from typing import Any
from unittest.mock import patch, MagicMock

from dependency_resolver import DependencyResolver, ResolveRequest, ResolveResult


class TestDependencyResolver:
    """Tests for DependencyResolver class."""

    def test_init_default_args(self) -> None:
        """Test DependencyResolver initialization with default arguments."""
        resolver = DependencyResolver()

        assert resolver.debug is False
        assert resolver.skip_system_scope is False
        assert resolver.max_workers is None

    def test_init_custom_args(self) -> None:
        """Test DependencyResolver initialization with custom arguments."""
        resolver = DependencyResolver(debug=True, skip_system_scope=True, max_workers=4)

        assert resolver.debug is True
        assert resolver.skip_system_scope is True
        assert resolver.max_workers == 4

    @patch("dependency_resolver.core.resolver.Orchestrator")
    def test_resolve_host_success(self, mock_orchestrator: Any) -> None:
        """Test single host environment resolution."""
        # Setup mocks
        mock_orchestrator_instance = MagicMock()
        mock_orchestrator.return_value = mock_orchestrator_instance
        mock_dependencies: dict[str, Any] = {"pip": {"dependencies": {"requests": {"version": "2.28.0"}}}}
        mock_orchestrator_instance.resolve_dependencies.return_value = mock_dependencies

        # Create resolver and resolve
        resolver = DependencyResolver(debug=True)
        result = resolver.resolve("host", working_dir="/tmp")

        # Verify
        assert result == mock_dependencies
        mock_orchestrator.assert_called_once_with(debug=True, skip_system_scope=False, venv_path=None)

    def test_resolve_invalid_environment_type(self) -> None:
        """Test resolve with invalid environment type."""
        resolver = DependencyResolver()

        with pytest.raises(ValueError, match="Unsupported environment type: invalid"):
            resolver.resolve("invalid")

    def test_resolve_docker_missing_identifier(self) -> None:
        """Test resolve with docker but missing identifier."""
        resolver = DependencyResolver()

        with pytest.raises(ValueError, match="Docker environment requires container identifier"):
            resolver.resolve("docker")

    @patch("dependency_resolver.core.resolver.Orchestrator")
    def test_resolve_batch_single_request(self, mock_orchestrator: Any) -> None:
        """Test batch resolution with single request."""
        # Setup mocks
        mock_orchestrator_instance = MagicMock()
        mock_orchestrator.return_value = mock_orchestrator_instance
        mock_dependencies: dict[str, Any] = {"pip": {"dependencies": {}}}
        mock_orchestrator_instance.resolve_dependencies.return_value = mock_dependencies

        # Create resolver and resolve batch
        resolver = DependencyResolver()
        requests = [ResolveRequest("host", working_dir="/tmp")]
        results = resolver.resolve_batch(requests)

        # Verify
        assert len(results) == 1
        assert results[0].success is True
        assert results[0].dependencies == mock_dependencies
        assert results[0].request.environment_type == "host"

    @patch("dependency_resolver.core.resolver.Orchestrator")
    def test_resolve_batch_multiple_requests(self, mock_orchestrator: Any) -> None:
        """Test batch resolution with multiple requests."""
        # Setup mocks
        mock_orchestrator_instance = MagicMock()
        mock_orchestrator.return_value = mock_orchestrator_instance
        mock_dependencies: dict[str, Any] = {"pip": {"dependencies": {}}}
        mock_orchestrator_instance.resolve_dependencies.return_value = mock_dependencies

        # Create resolver and resolve batch
        resolver = DependencyResolver(max_workers=2)
        requests = [ResolveRequest("host", working_dir="/tmp"), ResolveRequest("host", working_dir="/home")]
        results = resolver.resolve_batch(requests)

        # Verify
        assert len(results) == 2
        assert all(r.success for r in results)
        assert all(r.dependencies == mock_dependencies for r in results)

    def test_resolve_batch_empty_requests(self) -> None:
        """Test batch resolution with empty request list."""
        resolver = DependencyResolver()
        results = resolver.resolve_batch([])

        assert results == []

    @patch("dependency_resolver.core.resolver.Orchestrator")
    def test_resolve_batch_with_progress_callback(self, mock_orchestrator: Any) -> None:
        """Test batch resolution with progress callback."""
        # Setup mocks
        mock_orchestrator_instance = MagicMock()
        mock_orchestrator.return_value = mock_orchestrator_instance
        mock_dependencies: dict[str, Any] = {"pip": {"dependencies": {}}}
        mock_orchestrator_instance.resolve_dependencies.return_value = mock_dependencies

        # Track progress calls
        progress_calls = []

        def progress_callback(completed: int, total: int, result: ResolveResult) -> None:
            progress_calls.append((completed, total, result.success))

        # Create resolver and resolve batch
        resolver = DependencyResolver()
        requests = [ResolveRequest("host", venv_path="/test/venv")]
        results = resolver.resolve_batch(requests, progress_callback=progress_callback)

        # Verify progress was called
        assert len(progress_calls) == 1
        assert progress_calls[0] == (1, 1, True)
        assert len(results) == 1

    @patch("dependency_resolver.core.resolver.Orchestrator")
    def test_resolve_batch_as_dict(self, mock_orchestrator: Any) -> None:
        """Test batch resolution returning dictionary format."""
        # Setup mocks
        mock_orchestrator_instance = MagicMock()
        mock_orchestrator.return_value = mock_orchestrator_instance
        mock_dependencies: dict[str, Any] = {"pip": {"dependencies": {"requests": {"version": "2.28.0"}}}}
        mock_orchestrator_instance.resolve_dependencies.return_value = mock_dependencies

        # Create resolver and resolve batch
        resolver = DependencyResolver()
        requests = [
            ResolveRequest("host", metadata={"name": "test"}),
            ResolveRequest("docker", "nginx", metadata={"name": "container"}),
        ]
        result_dict = resolver.resolve_batch_as_dict(requests)

        # Verify
        assert "request_0" in result_dict
        # Second request key depends on execution order, could be "nginx" or "request_1"
        assert len(result_dict) == 2
        assert result_dict["request_0"] == mock_dependencies

    def test_resolve_batch_error_handling(self) -> None:
        """Test batch resolution handles errors gracefully."""
        resolver = DependencyResolver()
        requests = [ResolveRequest("invalid_type")]
        results = resolver.resolve_batch(requests)

        # Verify error is captured
        assert len(results) == 1
        assert results[0].success is False
        assert results[0].error is not None
        assert "Unsupported environment type" in results[0].error
        assert results[0].dependencies is None


class TestResolveRequest:
    """Tests for ResolveRequest dataclass."""

    def test_resolve_request_defaults(self) -> None:
        """Test ResolveRequest with default values."""
        request = ResolveRequest("host")

        assert request.environment_type == "host"
        assert request.environment_identifier is None
        assert request.working_dir is None
        assert request.venv_path is None
        assert request.only_container_info is False
        assert request.metadata == {}

    def test_resolve_request_full(self) -> None:
        """Test ResolveRequest with all values."""
        metadata = {"custom": "value"}
        request = ResolveRequest(
            environment_type="docker",
            environment_identifier="nginx",
            working_dir="/app",
            venv_path="/opt/venv",
            only_container_info=True,
            metadata=metadata,
        )

        assert request.environment_type == "docker"
        assert request.environment_identifier == "nginx"
        assert request.working_dir == "/app"
        assert request.venv_path == "/opt/venv"
        assert request.only_container_info is True
        assert request.metadata == metadata


class TestResolveResult:
    """Tests for ResolveResult dataclass."""

    def test_resolve_result_defaults(self) -> None:
        """Test ResolveResult with default values."""
        request = ResolveRequest("host")
        result = ResolveResult(request)

        assert result.request == request
        assert result.dependencies is None
        assert result.error is None
        assert result.execution_time == 0.0
        assert result.success is False

    def test_resolve_result_success(self) -> None:
        """Test ResolveResult for successful resolution."""
        request = ResolveRequest("host")
        dependencies: dict[str, Any] = {"pip": {"dependencies": {}}}
        result = ResolveResult(request=request, dependencies=dependencies, execution_time=1.5, success=True)

        assert result.request == request
        assert result.dependencies == dependencies
        assert result.error is None
        assert result.execution_time == 1.5
        assert result.success is True

    def test_resolve_result_error(self) -> None:
        """Test ResolveResult for failed resolution."""
        request = ResolveRequest("docker")
        result = ResolveResult(request=request, error="Container not found", execution_time=0.1, success=False)

        assert result.request == request
        assert result.dependencies is None
        assert result.error == "Container not found"
        assert result.execution_time == 0.1
        assert result.success is False
