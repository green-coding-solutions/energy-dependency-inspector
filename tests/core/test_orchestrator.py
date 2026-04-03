import pytest
from pytest import CaptureFixture
from energy_dependency_inspector.core.orchestrator import Orchestrator


class TestOrchestrator:
    """Test cases for the Orchestrator class."""

    def test_orchestrator_default_detectors(self) -> None:
        """Test that orchestrator initializes with all detectors by default."""
        orchestrator = Orchestrator()

        # Should have all 9 detectors
        assert len(orchestrator.detectors) == 9

        detector_names = {detector.NAME for detector in orchestrator.detectors}
        expected_names = {"host-info", "docker-info", "dpkg", "apk", "maven", "pip", "npm", "composer", "pecl"}
        assert detector_names == expected_names

    def test_orchestrator_select_valid_detectors(self) -> None:
        """Test selecting valid detectors."""
        orchestrator = Orchestrator(selected_detectors="pip,composer,pecl,dpkg")

        # Should have only 4 detectors
        assert len(orchestrator.detectors) == 4

        detector_names = {detector.NAME for detector in orchestrator.detectors}
        expected_names = {"pip", "composer", "pecl", "dpkg"}
        assert detector_names == expected_names

    def test_orchestrator_select_single_detector(self) -> None:
        """Test selecting a single detector."""
        orchestrator = Orchestrator(selected_detectors="npm")

        # Should have only 1 detector
        assert len(orchestrator.detectors) == 1
        assert orchestrator.detectors[0].NAME == "npm"

    def test_orchestrator_select_all_detectors(self) -> None:
        """Test selecting all detectors explicitly."""
        orchestrator = Orchestrator(selected_detectors="host-info,pip,npm,composer,pecl,dpkg,apk,maven,docker-info")

        # Should have all 9 detectors
        assert len(orchestrator.detectors) == 9

        detector_names = {detector.NAME for detector in orchestrator.detectors}
        expected_names = {"host-info", "docker-info", "dpkg", "apk", "maven", "pip", "npm", "composer", "pecl"}
        assert detector_names == expected_names

    def test_orchestrator_invalid_detector_name(self) -> None:
        """Test that invalid detector names raise ValueError."""
        with pytest.raises(ValueError) as exc_info:
            Orchestrator(selected_detectors="pip,composer,pecl,invalid-detector")

        error_message = str(exc_info.value)
        assert "Invalid detector names: invalid-detector" in error_message
        assert "Available detectors:" in error_message

    def test_orchestrator_multiple_invalid_detector_names(self) -> None:
        """Test that multiple invalid detector names are reported."""
        with pytest.raises(ValueError) as exc_info:
            Orchestrator(selected_detectors="pip,composer,pecl,invalid1,invalid2")

        error_message = str(exc_info.value)
        assert "Invalid detector names: invalid1, invalid2" in error_message

    def test_orchestrator_whitespace_handling(self) -> None:
        """Test that whitespace in detector names is handled correctly."""
        orchestrator = Orchestrator(selected_detectors=" pip , composer , pecl , dpkg ")

        # Should have 4 detectors despite whitespace
        assert len(orchestrator.detectors) == 4

        detector_names = {detector.NAME for detector in orchestrator.detectors}
        expected_names = {"pip", "composer", "pecl", "dpkg"}
        assert detector_names == expected_names

    def test_orchestrator_empty_selection(self) -> None:
        """Test that empty string selection uses all detectors."""
        orchestrator = Orchestrator(selected_detectors="")

        # Should have all 9 detectors (empty string is falsy)
        assert len(orchestrator.detectors) == 9

    def test_orchestrator_none_selection(self) -> None:
        """Test that None selection uses all detectors."""
        orchestrator = Orchestrator(selected_detectors=None)

        # Should have all 9 detectors
        assert len(orchestrator.detectors) == 9

    def test_orchestrator_debug_output_for_selected_detectors(self, capsys: CaptureFixture[str]) -> None:
        """Test that debug output shows selected detectors."""
        Orchestrator(debug=True, selected_detectors="pip,npm,composer,pecl")

        captured = capsys.readouterr()
        assert "Selected detectors: composer, pecl, pip, npm" in captured.out
