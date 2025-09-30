"""Tests for venv_checker module."""

import os
import pytest
from unittest.mock import patch, MagicMock
from energy_dependency_inspector.core.venv_checker import check_venv
from energy_dependency_inspector.core import venv_checker


class TestVenvChecker:
    """Test cases for venv checker functionality."""

    def test_check_venv_passes_with_correct_setup(self) -> None:
        """Test that check_venv passes when Python version and venv are correct."""
        # This test runs in the actual environment, so if it doesn't exit, it passes
        try:
            check_venv()
            # If we reach here, the check passed
            assert True
        except SystemExit:
            pytest.fail("check_venv() should not exit when environment is correct")

    def test_check_venv_fails_with_old_python(self) -> None:
        """Test that check_venv exits with old Python version."""
        mock_version = MagicMock()
        mock_version.major = 3
        mock_version.minor = 9

        with patch("energy_dependency_inspector.core.venv_checker.sys.version_info", mock_version):
            with pytest.raises(SystemExit) as excinfo:
                check_venv()
            assert excinfo.value.code == 1

    @patch("energy_dependency_inspector.core.venv_checker.sys.prefix", "/wrong/path")
    def test_check_venv_fails_with_wrong_venv(self) -> None:
        """Test that check_venv exits when venv path is incorrect."""
        with pytest.raises(SystemExit) as excinfo:
            check_venv()
        assert excinfo.value.code == 1

    def test_check_venv_passes_with_correct_venv_path(self) -> None:
        """Test that check_venv passes when venv path matches expected location."""
        mock_version = MagicMock()
        mock_version.major = 3
        mock_version.minor = 10

        # Mock sys.prefix to match the expected venv path
        current_dir = os.path.dirname(os.path.abspath(venv_checker.__file__))
        expected_venv_path = os.path.realpath(os.path.join(current_dir, "..", "..", "venv"))

        with patch("energy_dependency_inspector.core.venv_checker.sys.version_info", mock_version):
            with patch("energy_dependency_inspector.core.venv_checker.sys.prefix", expected_venv_path):
                # This should not raise SystemExit
                try:
                    check_venv()
                    assert True
                except SystemExit:
                    pytest.fail("check_venv() should not exit when venv path is correct")
