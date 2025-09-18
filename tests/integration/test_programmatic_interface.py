"""Tests for the programmatic interface in dependency_resolver/__init__.py."""

# pylint: disable=redefined-outer-name  # Standard pytest fixture usage

import pytest
from typing import Any, Dict
from unittest.mock import patch, MagicMock

from dependency_resolver import (
    resolve_host_dependencies,
    resolve_docker_dependencies,
    resolve_docker_dependencies_as_dict,
    resolve_dependencies_as_dict,
    main,
)


@pytest.fixture
def mock_host_setup() -> Any:
    """Fixture for common host environment mock setup."""
    with (
        patch("dependency_resolver.HostExecutor") as mock_executor_cls,
        patch("dependency_resolver.Orchestrator") as mock_orchestrator_cls,
    ):

        mock_executor = MagicMock()
        mock_executor_cls.return_value = mock_executor

        mock_orchestrator = MagicMock()
        mock_orchestrator_cls.return_value = mock_orchestrator

        yield {
            "executor_cls": mock_executor_cls,
            "executor": mock_executor,
            "orchestrator_cls": mock_orchestrator_cls,
            "orchestrator": mock_orchestrator,
        }


@pytest.fixture
def mock_docker_setup() -> Any:
    """Fixture for common docker environment mock setup."""
    with (
        patch("dependency_resolver.DockerExecutor") as mock_executor_cls,
        patch("dependency_resolver.Orchestrator") as mock_orchestrator_cls,
    ):

        mock_executor = MagicMock()
        mock_executor_cls.return_value = mock_executor

        mock_orchestrator = MagicMock()
        mock_orchestrator_cls.return_value = mock_orchestrator

        yield {
            "executor_cls": mock_executor_cls,
            "executor": mock_executor,
            "orchestrator_cls": mock_orchestrator_cls,
            "orchestrator": mock_orchestrator,
        }


@pytest.fixture
def mock_formatter() -> Any:
    """Fixture for OutputFormatter mock."""
    with patch("dependency_resolver.OutputFormatter") as mock_formatter_cls:
        mock_formatter_instance = MagicMock()
        mock_formatter_cls.return_value = mock_formatter_instance
        yield {"formatter_cls": mock_formatter_cls, "formatter": mock_formatter_instance}


def create_host_dependencies(package_name: str = "requests", package_version: str = "2.28.0") -> Dict[str, Any]:
    """Helper to create host dependency structure."""
    return {
        "source": {"type": "host", "name": "local-host"},
        "project": {
            "pip": {"location": "/home/user/.local/lib/python3.12/site-packages", "hash": "sha256:abc123..."},
            "packages": [{"name": package_name, "version": package_version, "type": "pip"}],
        },
        "system": {"packages": []},
    }


def create_container_dependencies(
    container_name: str = "test-container", package_name: str = "curl", package_version: str = "7.81.0-1ubuntu1.4"
) -> Dict[str, Any]:
    """Helper to create container dependency structure."""
    return {
        "source": {
            "type": "container",
            "name": container_name,
            "image": "ubuntu:20.04",
            "hash": "sha256:abc123...",
        },
        "project": {"packages": []},
        "system": {
            "packages": [{"name": package_name, "version": package_version, "hash": "sha256:def456...", "type": "dpkg"}]
        },
    }


def create_container_info_only(container_name: str = "my-container") -> Dict[str, Any]:
    """Helper to create container info only structure."""
    return {
        "source": {"type": "container", "name": container_name, "image": "ubuntu:20.04", "hash": "sha256:abc123..."}
    }


class TestResolveHostDependencies:
    """Tests for resolve_host_dependencies function."""

    def test_resolve_host_dependencies_default_args(self, mock_host_setup: Any, mock_formatter: Any) -> None:
        """Test resolve_host_dependencies with default arguments."""
        mock_dependencies = create_host_dependencies()
        mock_host_setup["orchestrator"].resolve_dependencies.return_value = mock_dependencies
        mock_formatter["formatter"].format_json.return_value = "formatted_json"

        result = resolve_host_dependencies()

        # Verify calls
        mock_host_setup["executor_cls"].assert_called_once()
        mock_host_setup["orchestrator_cls"].assert_called_once_with(
            debug=False, skip_system_scope=False, venv_path=None
        )
        mock_host_setup["orchestrator"].resolve_dependencies.assert_called_once_with(mock_host_setup["executor"], None)
        mock_formatter["formatter_cls"].assert_called_once_with(debug=False)
        mock_formatter["formatter"].format_json.assert_called_once_with(mock_dependencies, pretty_print=False)

        assert result == "formatted_json"

    def test_resolve_host_dependencies_with_all_args(self, mock_host_setup: Any, mock_formatter: Any) -> None:
        """Test resolve_host_dependencies with all arguments specified."""
        mock_dependencies = create_host_dependencies("express", "4.18.0")
        mock_host_setup["orchestrator"].resolve_dependencies.return_value = mock_dependencies
        mock_formatter["formatter"].format_json.return_value = "formatted_pretty_json"

        resolve_host_dependencies(
            working_dir="/tmp/test", debug=True, skip_system_scope=True, venv_path="/path/to/venv", pretty_print=True
        )

        # Verify calls
        mock_host_setup["orchestrator_cls"].assert_called_once_with(
            debug=True, skip_system_scope=True, venv_path="/path/to/venv"
        )
        mock_host_setup["orchestrator"].resolve_dependencies.assert_called_once_with(
            mock_host_setup["executor"], "/tmp/test"
        )
        mock_formatter["formatter_cls"].assert_called_once_with(debug=True)
        mock_formatter["formatter"].format_json.assert_called_once_with(mock_dependencies, pretty_print=True)


class TestResolveDockerDependencies:
    """Tests for resolve_docker_dependencies function."""

    def test_resolve_docker_dependencies_default_args(self, mock_docker_setup: Any, mock_formatter: Any) -> None:
        """Test resolve_docker_dependencies with minimal arguments."""
        mock_dependencies = create_container_dependencies("test-container")
        mock_docker_setup["orchestrator"].resolve_dependencies.return_value = mock_dependencies
        mock_formatter["formatter"].format_json.return_value = "formatted_json"

        result = resolve_docker_dependencies("test-container")

        # Verify calls
        mock_docker_setup["executor_cls"].assert_called_once_with("test-container")
        mock_docker_setup["orchestrator_cls"].assert_called_once_with(
            debug=False, skip_system_scope=False, venv_path=None
        )
        mock_docker_setup["orchestrator"].resolve_dependencies.assert_called_once_with(
            mock_docker_setup["executor"], None, False
        )
        mock_formatter["formatter_cls"].assert_called_once_with(debug=False)
        mock_formatter["formatter"].format_json.assert_called_once_with(mock_dependencies, pretty_print=False)

        assert result == "formatted_json"

    def test_resolve_docker_dependencies_with_all_args(self, mock_docker_setup: Any, mock_formatter: Any) -> None:
        """Test resolve_docker_dependencies with all arguments."""
        mock_dependencies = create_container_info_only("my-container")
        mock_docker_setup["orchestrator"].resolve_dependencies.return_value = mock_dependencies
        mock_formatter["formatter"].format_json.return_value = "formatted_pretty_json"

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
        mock_docker_setup["executor_cls"].assert_called_once_with("my-container")
        mock_docker_setup["orchestrator_cls"].assert_called_once_with(
            debug=True, skip_system_scope=True, venv_path="/opt/venv"
        )
        mock_docker_setup["orchestrator"].resolve_dependencies.assert_called_once_with(
            mock_docker_setup["executor"], "/app", True
        )
        mock_formatter["formatter_cls"].assert_called_once_with(debug=True)
        mock_formatter["formatter"].format_json.assert_called_once_with(mock_dependencies, pretty_print=True)


class TestResolveDependenciesAsDict:
    """Tests for resolve_dependencies_as_dict function."""

    def test_resolve_dependencies_as_dict_host(self, mock_host_setup: Any) -> None:
        """Test resolve_dependencies_as_dict with host environment."""
        mock_dependencies = create_host_dependencies("flask", "2.2.0")
        mock_host_setup["orchestrator"].resolve_dependencies.return_value = mock_dependencies

        result = resolve_dependencies_as_dict()

        # Verify calls
        mock_host_setup["executor_cls"].assert_called_once()
        mock_host_setup["orchestrator_cls"].assert_called_once_with(
            debug=False, skip_system_scope=False, venv_path=None
        )
        mock_host_setup["orchestrator"].resolve_dependencies.assert_called_once_with(
            mock_host_setup["executor"], None, False
        )

        assert result == mock_dependencies

    def test_resolve_dependencies_as_dict_docker(self, mock_docker_setup: Any) -> None:
        """Test resolve_dependencies_as_dict with docker environment."""
        mock_dependencies = create_container_dependencies("alpine-container", "git", "2.36.2-r0")
        # Update to apk type for alpine
        mock_dependencies["system"]["packages"][0]["type"] = "apk"
        mock_dependencies["source"]["image"] = "alpine:3.18"
        mock_docker_setup["orchestrator"].resolve_dependencies.return_value = mock_dependencies

        result = resolve_dependencies_as_dict(environment_type="docker", environment_identifier="alpine-container")

        # Verify calls
        mock_docker_setup["executor_cls"].assert_called_once_with("alpine-container")
        mock_docker_setup["orchestrator_cls"].assert_called_once_with(
            debug=False, skip_system_scope=False, venv_path=None
        )
        mock_docker_setup["orchestrator"].resolve_dependencies.assert_called_once_with(
            mock_docker_setup["executor"], None, False
        )

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

    def test_resolve_docker_dependencies_as_dict_default_args(self, mock_docker_setup: Any) -> None:
        """Test resolve_docker_dependencies_as_dict with minimal arguments."""
        mock_dependencies = create_container_dependencies("test-container")
        mock_docker_setup["orchestrator"].resolve_dependencies.return_value = mock_dependencies

        result = resolve_docker_dependencies_as_dict("test-container")

        # Verify calls
        mock_docker_setup["executor_cls"].assert_called_once_with("test-container")
        mock_docker_setup["orchestrator_cls"].assert_called_once_with(
            debug=False, skip_system_scope=False, venv_path=None
        )
        mock_docker_setup["orchestrator"].resolve_dependencies.assert_called_once_with(
            mock_docker_setup["executor"], None, False
        )

        assert result == mock_dependencies

    def test_resolve_docker_dependencies_as_dict_with_all_args(self, mock_docker_setup: Any) -> None:
        """Test resolve_docker_dependencies_as_dict with all arguments."""
        mock_dependencies = create_container_info_only("my-container")
        mock_docker_setup["orchestrator"].resolve_dependencies.return_value = mock_dependencies

        result = resolve_docker_dependencies_as_dict(
            container_identifier="my-container",
            working_dir="/app",
            debug=True,
            skip_system_scope=True,
            venv_path="/opt/venv",
            only_container_info=True,
        )

        # Verify calls
        mock_docker_setup["executor_cls"].assert_called_once_with("my-container")
        mock_docker_setup["orchestrator_cls"].assert_called_once_with(
            debug=True, skip_system_scope=True, venv_path="/opt/venv"
        )
        mock_docker_setup["orchestrator"].resolve_dependencies.assert_called_once_with(
            mock_docker_setup["executor"], "/app", True
        )

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
