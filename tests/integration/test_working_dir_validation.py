"""Test working directory validation in Orchestrator."""

import os
import sys
import tempfile

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

from energy_dependency_inspector.core.orchestrator import Orchestrator
from energy_dependency_inspector.executors import HostExecutor


class TestWorkingDirValidation:
    """Test working directory validation in resolve_dependencies method."""

    def test_resolve_dependencies_with_valid_working_dir(self) -> None:
        """Test resolve_dependencies with a valid working directory."""
        orchestrator = Orchestrator(debug=False, skip_os_packages=True)
        executor = HostExecutor()

        with tempfile.TemporaryDirectory() as temp_dir:
            # Should not raise an exception
            result = orchestrator.resolve_dependencies(executor, working_dir=temp_dir)
            assert isinstance(result, dict)

    def test_resolve_dependencies_with_invalid_working_dir(self) -> None:
        """Test resolve_dependencies with an invalid working directory."""
        orchestrator = Orchestrator(debug=False, skip_os_packages=True)
        executor = HostExecutor()

        non_existent_dir = "/this/directory/does/not/exist"

        with pytest.raises(ValueError, match=f"Working directory does not exist: {non_existent_dir}"):
            orchestrator.resolve_dependencies(executor, working_dir=non_existent_dir)

    def test_resolve_dependencies_with_none_working_dir(self) -> None:
        """Test resolve_dependencies with None working directory (should work fine)."""
        orchestrator = Orchestrator(debug=False, skip_os_packages=True)
        executor = HostExecutor()

        # Should not raise an exception
        result = orchestrator.resolve_dependencies(executor, working_dir=None)
        assert isinstance(result, dict)
