"""Test CLI interface functionality."""

import pytest
import sys
from unittest.mock import patch
from dependency_resolver.__main__ import parse_arguments, validate_arguments, create_executor


class TestCliArguments:
    """Test CLI argument parsing and validation."""

    def test_default_arguments(self) -> None:
        """Test default argument values."""
        with patch.object(sys, "argv", ["dependency_resolver"]):
            args = parse_arguments()
            assert args.environment_type == "host"
            assert args.environment_identifier is None
            assert args.debug is False

    def test_docker_arguments(self) -> None:
        """Test docker environment arguments."""
        with patch.object(sys, "argv", ["dependency_resolver", "docker", "test_container"]):
            args = parse_arguments()
            assert args.environment_type == "docker"
            assert args.environment_identifier == "test_container"

    def test_validate_docker_requires_identifier(self) -> None:
        """Test docker validation requires identifier."""
        with pytest.raises(SystemExit):
            validate_arguments("docker", None)

    def test_create_host_executor(self) -> None:
        """Test host executor creation."""
        executor = create_executor("host", None)
        assert executor.__class__.__name__ == "HostExecutor"

    def test_create_docker_executor_without_identifier_fails(self) -> None:
        """Test docker executor creation fails without identifier."""
        with pytest.raises(SystemExit):
            create_executor("docker", None)

    def test_select_detectors_argument(self) -> None:
        """Test --select-detectors argument parsing."""
        with patch.object(sys, "argv", ["dependency_resolver", "--select-detectors", "pip,dpkg"]):
            args = parse_arguments()
            assert args.select_detectors == "pip,dpkg"

    def test_select_detectors_single(self) -> None:
        """Test --select-detectors with single detector."""
        with patch.object(sys, "argv", ["dependency_resolver", "--select-detectors", "npm"]):
            args = parse_arguments()
            assert args.select_detectors == "npm"

    def test_select_detectors_default_none(self) -> None:
        """Test --select-detectors defaults to None."""
        with patch.object(sys, "argv", ["dependency_resolver"]):
            args = parse_arguments()
            assert args.select_detectors is None
