"""Tests for the programmatic interface in dependency_resolver/__init__.py."""

import pytest
from typing import Any
from unittest.mock import patch, MagicMock

from dependency_resolver import (
    resolve_host_dependencies,
    resolve_docker_dependencies,
    resolve_docker_dependencies_as_dict,
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
        mock_dependencies = {
            "source": {"type": "host", "name": "local-host"},
            "project": {
                "pip": {"location": "/home/user/.local/lib/python3.12/site-packages", "hash": "sha256:abc123..."},
                "packages": [{"name": "requests", "version": "2.28.0", "type": "pip"}],
            },
            "system": {"packages": []},
        }
        mock_orchestrator_instance.resolve_dependencies.return_value = mock_dependencies

        mock_formatter_instance = MagicMock()
        mock_formatter.return_value = mock_formatter_instance
        mock_formatter_instance.format_json.return_value = '{"source": {"type": "host", "name": "local-host"}, "project": {"pip": {"location": "/home/user/.local/lib/python3.12/site-packages", "hash": "sha256:abc123..."}, "packages": [{"name": "requests", "version": "2.28.0", "type": "pip"}]}, "system": {"packages": []}}'

        # Call function
        result = resolve_host_dependencies()

        # Verify calls
        mock_host_executor.assert_called_once()
        mock_orchestrator.assert_called_once_with(debug=False, skip_system_scope=False, venv_path=None)
        mock_orchestrator_instance.resolve_dependencies.assert_called_once_with(mock_executor_instance, None)
        mock_formatter.assert_called_once_with(debug=False)
        mock_formatter_instance.format_json.assert_called_once_with(mock_dependencies, pretty_print=False)

        assert (
            result
            == '{"source": {"type": "host", "name": "local-host"}, "project": {"pip": {"location": "/home/user/.local/lib/python3.12/site-packages", "hash": "sha256:abc123..."}, "packages": [{"name": "requests", "version": "2.28.0", "type": "pip"}]}, "system": {"packages": []}}'
        )

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
        mock_dependencies = {
            "source": {"type": "host", "name": "local-host"},
            "project": {
                "npm": {"location": "/tmp/test/node_modules", "hash": "sha256:npm456..."},
                "packages": [{"name": "express", "version": "4.18.0", "type": "npm"}],
            },
            "system": {"packages": []},
        }
        mock_orchestrator_instance.resolve_dependencies.return_value = mock_dependencies

        mock_formatter_instance = MagicMock()
        mock_formatter.return_value = mock_formatter_instance
        mock_formatter_instance.format_json.return_value = '{\n  "source": {\n    "type": "host",\n    "name": "local-host"\n  },\n  "project": {\n    "npm": {\n      "location": "/tmp/test/node_modules",\n      "hash": "sha256:npm456..."\n    },\n    "packages": [\n      {\n        "name": "express",\n        "version": "4.18.0",\n        "type": "npm"\n      }\n    ]\n  },\n  "system": {\n    "packages": []\n  }\n}'

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
        mock_dependencies = {
            "source": {
                "type": "container",
                "name": "test-container",
                "image": "ubuntu:20.04",
                "hash": "sha256:abc123...",
            },
            "project": {"packages": []},
            "system": {
                "packages": [
                    {"name": "curl", "version": "7.81.0-1ubuntu1.4", "hash": "sha256:def456...", "type": "dpkg"}
                ]
            },
        }
        mock_orchestrator_instance.resolve_dependencies.return_value = mock_dependencies

        mock_formatter_instance = MagicMock()
        mock_formatter.return_value = mock_formatter_instance
        mock_formatter_instance.format_json.return_value = '{"source": {"type": "container", "name": "test-container", "image": "ubuntu:20.04", "hash": "sha256:abc123..."}, "project": {"packages": []}, "system": {"packages": [{"name": "curl", "version": "7.81.0-1ubuntu1.4", "hash": "sha256:def456...", "type": "dpkg"}]}}'

        # Call function
        result = resolve_docker_dependencies("test-container")

        # Verify calls
        mock_docker_executor.assert_called_once_with("test-container")
        mock_orchestrator.assert_called_once_with(debug=False, skip_system_scope=False, venv_path=None)
        mock_orchestrator_instance.resolve_dependencies.assert_called_once_with(mock_executor_instance, None, False)
        mock_formatter.assert_called_once_with(debug=False)
        mock_formatter_instance.format_json.assert_called_once_with(mock_dependencies, pretty_print=False)

        assert (
            result
            == '{"source": {"type": "container", "name": "test-container", "image": "ubuntu:20.04", "hash": "sha256:abc123..."}, "project": {"packages": []}, "system": {"packages": [{"name": "curl", "version": "7.81.0-1ubuntu1.4", "hash": "sha256:def456...", "type": "dpkg"}]}}'
        )

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
        mock_dependencies = {
            "source": {"type": "container", "name": "my-container", "image": "ubuntu:20.04", "hash": "sha256:abc123..."}
        }
        mock_orchestrator_instance.resolve_dependencies.return_value = mock_dependencies

        mock_formatter_instance = MagicMock()
        mock_formatter.return_value = mock_formatter_instance
        mock_formatter_instance.format_json.return_value = '{\n  "source": {\n    "type": "container",\n    "name": "my-container",\n    "image": "ubuntu:20.04",\n    "hash": "sha256:abc123..."\n  }\n}'

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
        mock_dependencies = {
            "source": {"type": "host", "name": "local-host"},
            "project": {
                "pip": {"location": "/home/user/.local/lib/python3.12/site-packages", "hash": "sha256:abc123..."},
                "packages": [{"name": "flask", "version": "2.2.0", "type": "pip"}],
            },
            "system": {"packages": []},
        }
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
        mock_dependencies = {
            "source": {
                "type": "container",
                "name": "alpine-container",
                "image": "alpine:3.18",
                "hash": "sha256:def456...",
            },
            "project": {"packages": []},
            "system": {
                "packages": [{"name": "git", "version": "2.36.2-r0", "hash": "sha256:ghi789...", "type": "apk"}]
            },
        }
        mock_orchestrator_instance.resolve_dependencies.return_value = mock_dependencies

        # Call function
        result = resolve_dependencies_as_dict(environment_type="docker", environment_identifier="alpine-container")

        # Verify calls
        mock_docker_executor.assert_called_once_with("alpine-container")
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


class TestResolveDockerDependenciesAsDict:
    """Tests for resolve_docker_dependencies_as_dict function."""

    @patch("dependency_resolver.Orchestrator")
    @patch("dependency_resolver.DockerExecutor")
    def test_resolve_docker_dependencies_as_dict_default_args(
        self, mock_docker_executor: Any, mock_orchestrator: Any
    ) -> None:
        """Test resolve_docker_dependencies_as_dict with minimal arguments."""
        # Setup mocks
        mock_executor_instance = MagicMock()
        mock_docker_executor.return_value = mock_executor_instance

        mock_orchestrator_instance = MagicMock()
        mock_orchestrator.return_value = mock_orchestrator_instance
        mock_dependencies = {
            "source": {
                "type": "container",
                "name": "test-container",
                "image": "ubuntu:20.04",
                "hash": "sha256:abc123...",
            },
            "project": {"packages": []},
            "system": {
                "packages": [
                    {"name": "curl", "version": "7.81.0-1ubuntu1.4", "hash": "sha256:def456...", "type": "dpkg"}
                ]
            },
        }
        mock_orchestrator_instance.resolve_dependencies.return_value = mock_dependencies

        # Call function
        result = resolve_docker_dependencies_as_dict("test-container")

        # Verify calls
        mock_docker_executor.assert_called_once_with("test-container")
        mock_orchestrator.assert_called_once_with(debug=False, skip_system_scope=False, venv_path=None)
        mock_orchestrator_instance.resolve_dependencies.assert_called_once_with(mock_executor_instance, None, False)

        assert result == mock_dependencies

    @patch("dependency_resolver.Orchestrator")
    @patch("dependency_resolver.DockerExecutor")
    def test_resolve_docker_dependencies_as_dict_with_all_args(
        self, mock_docker_executor: Any, mock_orchestrator: Any
    ) -> None:
        """Test resolve_docker_dependencies_as_dict with all arguments."""
        # Setup mocks
        mock_executor_instance = MagicMock()
        mock_docker_executor.return_value = mock_executor_instance

        mock_orchestrator_instance = MagicMock()
        mock_orchestrator.return_value = mock_orchestrator_instance
        mock_dependencies = {
            "source": {"type": "container", "name": "my-container", "image": "ubuntu:20.04", "hash": "sha256:abc123..."}
        }
        mock_orchestrator_instance.resolve_dependencies.return_value = mock_dependencies

        # Call function with all arguments
        result = resolve_docker_dependencies_as_dict(
            container_identifier="my-container",
            working_dir="/app",
            debug=True,
            skip_system_scope=True,
            venv_path="/opt/venv",
            only_container_info=True,
        )

        # Verify calls
        mock_docker_executor.assert_called_once_with("my-container")
        mock_orchestrator.assert_called_once_with(debug=True, skip_system_scope=True, venv_path="/opt/venv")
        mock_orchestrator_instance.resolve_dependencies.assert_called_once_with(mock_executor_instance, "/app", True)

        assert result == mock_dependencies

    def test_resolve_docker_dependencies_as_dict_empty_container_identifier(self) -> None:
        """Test resolve_docker_dependencies_as_dict with empty container identifier."""
        with pytest.raises(ValueError, match="Container identifier is required"):
            resolve_docker_dependencies_as_dict("")

    def test_resolve_docker_dependencies_as_dict_none_container_identifier(self) -> None:
        """Test resolve_docker_dependencies_as_dict with None container identifier."""
        with pytest.raises(ValueError, match="Container identifier is required"):
            resolve_docker_dependencies_as_dict(None)  # type: ignore

    @patch("dependency_resolver.DockerExecutor")
    def test_resolve_docker_dependencies_as_dict_docker_executor_error(self, mock_docker_executor: Any) -> None:
        """Test resolve_docker_dependencies_as_dict when DockerExecutor raises error."""
        mock_docker_executor.side_effect = RuntimeError("Container 'nonexistent' not found")

        with pytest.raises(RuntimeError, match="Container 'nonexistent' not found"):
            resolve_docker_dependencies_as_dict("nonexistent")


class TestMain:
    """Tests for main function."""

    @patch("dependency_resolver.__main__.main")
    def test_main_calls_cli_main(self, mock_cli_main: Any) -> None:
        """Test that main function calls the CLI main function."""
        main()
        mock_cli_main.assert_called_once()
