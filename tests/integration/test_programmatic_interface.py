"""Tests for the programmatic interface in dependency_resolver/__init__.py."""

import pytest
from typing import Any
from unittest.mock import patch, MagicMock

from dependency_resolver import (
    resolve_host_dependencies,
    resolve_docker_dependencies,
    resolve_dependencies_as_dict,
    main,
)


class TestResolveHostDependencies:
    """Tests for resolve_host_dependencies function."""

    @patch("dependency_resolver.Orchestrator")
    @patch("dependency_resolver.HostExecutor")
    @patch("dependency_resolver.OutputFormatter")
    def test_resolve_host_dependencies_default_args(
        self, mock_formatter: Any, mock_host_executor: Any, mock_orchestrator: Any
    ) -> None:
        """Test resolve_host_dependencies with default arguments."""
        # Setup mocks
        mock_executor_instance = MagicMock()
        mock_host_executor.return_value = mock_executor_instance

        mock_orchestrator_instance = MagicMock()
        mock_orchestrator.return_value = mock_orchestrator_instance
        mock_dependencies = {"pip": [{"name": "requests", "version": "2.28.0"}]}
        mock_orchestrator_instance.resolve_dependencies.return_value = mock_dependencies

        mock_formatter_instance = MagicMock()
        mock_formatter.return_value = mock_formatter_instance
        mock_formatter_instance.format_json.return_value = '{"pip": [{"name": "requests", "version": "2.28.0"}]}'

        # Call function
        result = resolve_host_dependencies()

        # Verify calls
        mock_host_executor.assert_called_once()
        mock_orchestrator.assert_called_once_with(debug=False, skip_system_scope=False, venv_path=None)
        mock_orchestrator_instance.resolve_dependencies.assert_called_once_with(mock_executor_instance, None)
        mock_formatter.assert_called_once_with(debug=False)
        mock_formatter_instance.format_json.assert_called_once_with(mock_dependencies, pretty_print=False)

        assert result == '{"pip": [{"name": "requests", "version": "2.28.0"}]}'

    @patch("dependency_resolver.Orchestrator")
    @patch("dependency_resolver.HostExecutor")
    @patch("dependency_resolver.OutputFormatter")
    def test_resolve_host_dependencies_with_all_args(
        self, mock_formatter: Any, mock_host_executor: Any, mock_orchestrator: Any
    ) -> None:
        """Test resolve_host_dependencies with all arguments specified."""
        # Setup mocks
        mock_executor_instance = MagicMock()
        mock_host_executor.return_value = mock_executor_instance

        mock_orchestrator_instance = MagicMock()
        mock_orchestrator.return_value = mock_orchestrator_instance
        mock_dependencies = {"npm": [{"name": "express", "version": "4.18.0"}]}
        mock_orchestrator_instance.resolve_dependencies.return_value = mock_dependencies

        mock_formatter_instance = MagicMock()
        mock_formatter.return_value = mock_formatter_instance
        mock_formatter_instance.format_json.return_value = (
            '{\n  "npm": [\n    {\n      "name": "express",\n      "version": "4.18.0"\n    }\n  ]\n}'
        )

        # Call function with all arguments
        resolve_host_dependencies(
            working_dir="/tmp/test", debug=True, skip_system_scope=True, venv_path="/path/to/venv", pretty_print=True
        )

        # Verify calls
        mock_orchestrator.assert_called_once_with(debug=True, skip_system_scope=True, venv_path="/path/to/venv")
        mock_orchestrator_instance.resolve_dependencies.assert_called_once_with(mock_executor_instance, "/tmp/test")
        mock_formatter.assert_called_once_with(debug=True)
        mock_formatter_instance.format_json.assert_called_once_with(mock_dependencies, pretty_print=True)


class TestResolveDockerDependencies:
    """Tests for resolve_docker_dependencies function."""

    @patch("dependency_resolver.Orchestrator")
    @patch("dependency_resolver.DockerExecutor")
    @patch("dependency_resolver.OutputFormatter")
    def test_resolve_docker_dependencies_default_args(
        self, mock_formatter: Any, mock_docker_executor: Any, mock_orchestrator: Any
    ) -> None:
        """Test resolve_docker_dependencies with minimal arguments."""
        # Setup mocks
        mock_executor_instance = MagicMock()
        mock_docker_executor.return_value = mock_executor_instance

        mock_orchestrator_instance = MagicMock()
        mock_orchestrator.return_value = mock_orchestrator_instance
        mock_dependencies = {"dpkg": [{"name": "curl", "version": "7.81.0-1ubuntu1.4"}]}
        mock_orchestrator_instance.resolve_dependencies.return_value = mock_dependencies

        mock_formatter_instance = MagicMock()
        mock_formatter.return_value = mock_formatter_instance
        mock_formatter_instance.format_json.return_value = (
            '{"dpkg": [{"name": "curl", "version": "7.81.0-1ubuntu1.4"}]}'
        )

        # Call function
        result = resolve_docker_dependencies("test-container")

        # Verify calls
        mock_docker_executor.assert_called_once_with("test-container")
        mock_orchestrator.assert_called_once_with(debug=False, skip_system_scope=False, venv_path=None)
        mock_orchestrator_instance.resolve_dependencies.assert_called_once_with(mock_executor_instance, None, False)
        mock_formatter.assert_called_once_with(debug=False)
        mock_formatter_instance.format_json.assert_called_once_with(mock_dependencies, pretty_print=False)

        assert result == '{"dpkg": [{"name": "curl", "version": "7.81.0-1ubuntu1.4"}]}'

    @patch("dependency_resolver.Orchestrator")
    @patch("dependency_resolver.DockerExecutor")
    @patch("dependency_resolver.OutputFormatter")
    def test_resolve_docker_dependencies_with_all_args(
        self, mock_formatter: Any, mock_docker_executor: Any, mock_orchestrator: Any
    ) -> None:
        """Test resolve_docker_dependencies with all arguments."""
        # Setup mocks
        mock_executor_instance = MagicMock()
        mock_docker_executor.return_value = mock_executor_instance

        mock_orchestrator_instance = MagicMock()
        mock_orchestrator.return_value = mock_orchestrator_instance
        mock_dependencies = {"container_info": {"id": "abc123", "image": "ubuntu:20.04"}}
        mock_orchestrator_instance.resolve_dependencies.return_value = mock_dependencies

        mock_formatter_instance = MagicMock()
        mock_formatter.return_value = mock_formatter_instance
        mock_formatter_instance.format_json.return_value = (
            '{\n  "container_info": {\n    "id": "abc123",\n    "image": "ubuntu:20.04"\n  }\n}'
        )

        # Call function with all arguments
        resolve_docker_dependencies(
            container_identifier="my-container",
            working_dir="/app",
            debug=True,
            skip_system_scope=True,
            venv_path="/opt/venv",
            only_container_info=True,
            pretty_print=True,
        )

        # Verify calls
        mock_docker_executor.assert_called_once_with("my-container")
        mock_orchestrator.assert_called_once_with(debug=True, skip_system_scope=True, venv_path="/opt/venv")
        mock_orchestrator_instance.resolve_dependencies.assert_called_once_with(mock_executor_instance, "/app", True)
        mock_formatter.assert_called_once_with(debug=True)
        mock_formatter_instance.format_json.assert_called_once_with(mock_dependencies, pretty_print=True)


class TestResolveDependenciesAsDict:
    """Tests for resolve_dependencies_as_dict function."""

    @patch("dependency_resolver.Orchestrator")
    @patch("dependency_resolver.HostExecutor")
    def test_resolve_dependencies_as_dict_host(self, mock_host_executor: Any, mock_orchestrator: Any) -> None:
        """Test resolve_dependencies_as_dict with host environment."""
        # Setup mocks
        mock_executor_instance = MagicMock()
        mock_host_executor.return_value = mock_executor_instance

        mock_orchestrator_instance = MagicMock()
        mock_orchestrator.return_value = mock_orchestrator_instance
        mock_dependencies = {"pip": [{"name": "flask", "version": "2.2.0"}]}
        mock_orchestrator_instance.resolve_dependencies.return_value = mock_dependencies

        # Call function
        result = resolve_dependencies_as_dict()

        # Verify calls
        mock_host_executor.assert_called_once()
        mock_orchestrator.assert_called_once_with(debug=False, skip_system_scope=False, venv_path=None)
        mock_orchestrator_instance.resolve_dependencies.assert_called_once_with(mock_executor_instance, None, False)

        assert result == mock_dependencies

    @patch("dependency_resolver.Orchestrator")
    @patch("dependency_resolver.DockerExecutor")
    def test_resolve_dependencies_as_dict_docker(self, mock_docker_executor: Any, mock_orchestrator: Any) -> None:
        """Test resolve_dependencies_as_dict with docker environment."""
        # Setup mocks
        mock_executor_instance = MagicMock()
        mock_docker_executor.return_value = mock_executor_instance

        mock_orchestrator_instance = MagicMock()
        mock_orchestrator.return_value = mock_orchestrator_instance
        mock_dependencies = {"apk": [{"name": "git", "version": "2.36.2-r0"}]}
        mock_orchestrator_instance.resolve_dependencies.return_value = mock_dependencies

        # Call function
        result = resolve_dependencies_as_dict(environment_type="docker", environment_identifier="alpine-container")

        # Verify calls
        mock_docker_executor.assert_called_once_with("alpine-container")
        mock_orchestrator.assert_called_once_with(debug=False, skip_system_scope=False, venv_path=None)
        mock_orchestrator_instance.resolve_dependencies.assert_called_once_with(mock_executor_instance, None, False)

        assert result == mock_dependencies

    @patch("dependency_resolver.Orchestrator")
    @patch("dependency_resolver.DockerComposeExecutor")
    def test_resolve_dependencies_as_dict_docker_compose(
        self, mock_docker_compose_executor: Any, mock_orchestrator: Any
    ) -> None:
        """Test resolve_dependencies_as_dict with docker_compose environment."""
        # Setup mocks
        mock_executor_instance = MagicMock()
        mock_docker_compose_executor.return_value = mock_executor_instance

        mock_orchestrator_instance = MagicMock()
        mock_orchestrator.return_value = mock_orchestrator_instance
        mock_dependencies = {"npm": [{"name": "react", "version": "18.2.0"}]}
        mock_orchestrator_instance.resolve_dependencies.return_value = mock_dependencies

        # Call function
        result = resolve_dependencies_as_dict(environment_type="docker_compose", environment_identifier="web-service")

        # Verify calls
        mock_docker_compose_executor.assert_called_once_with("web-service")
        mock_orchestrator.assert_called_once_with(debug=False, skip_system_scope=False, venv_path=None)
        mock_orchestrator_instance.resolve_dependencies.assert_called_once_with(mock_executor_instance, None, False)

        assert result == mock_dependencies

    def test_resolve_dependencies_as_dict_unsupported_environment(self) -> None:
        """Test resolve_dependencies_as_dict with unsupported environment type."""
        with pytest.raises(ValueError, match="Unsupported environment type: invalid"):
            resolve_dependencies_as_dict(environment_type="invalid")

    def test_resolve_dependencies_as_dict_docker_missing_identifier(self) -> None:
        """Test resolve_dependencies_as_dict with docker but missing identifier."""
        with pytest.raises(ValueError, match="Docker environment requires container identifier"):
            resolve_dependencies_as_dict(environment_type="docker")

    def test_resolve_dependencies_as_dict_docker_compose_missing_identifier(self) -> None:
        """Test resolve_dependencies_as_dict with docker_compose but missing identifier."""
        with pytest.raises(ValueError, match="Docker Compose environment requires service identifier"):
            resolve_dependencies_as_dict(environment_type="docker_compose")


class TestMain:
    """Tests for main function."""

    @patch("dependency_resolver.__main__.main")
    def test_main_calls_cli_main(self, mock_cli_main: Any) -> None:
        """Test that main function calls the CLI main function."""
        main()
        mock_cli_main.assert_called_once()
