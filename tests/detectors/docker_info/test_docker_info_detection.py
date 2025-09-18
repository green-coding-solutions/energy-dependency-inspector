"""Test Docker Info detector for individual container metadata."""

import os
import sys
from typing import Dict, Any
from unittest.mock import Mock

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import pytest

from dependency_resolver.executors import DockerExecutor
from dependency_resolver.detectors.docker_info_detector import DockerInfoDetector
from dependency_resolver.core.orchestrator import Orchestrator
from tests.common.docker_test_base import DockerTestBase

try:
    import docker
except ImportError:
    docker = None  # type: ignore


class TestDockerInfoDetection(DockerTestBase):
    """Test Docker Info detector for individual container metadata."""

    @pytest.mark.skipif(docker is None, reason="Docker not available")
    def test_docker_info_detection_real_container(self, request: pytest.FixtureRequest) -> None:
        """Test Docker Info detection using a real container."""
        verbose_output = self.setup_verbose_output(request)
        container_id = None

        try:
            # Start a test container
            container_id = self.start_container("nginx:alpine", sleep_duration="60")

            # Wait for container to be ready
            self.wait_for_container_ready(container_id, "echo ready", max_wait=10)

            # Test Docker Info detection
            executor = DockerExecutor(container_id)
            orchestrator = Orchestrator(debug=False)

            # Test full analysis (includes container info)
            result = orchestrator.resolve_dependencies(executor)

            if verbose_output:
                self.print_verbose_results("DOCKER INFO DETECTION OUTPUT (FULL):", result)

            # Validate container info is included
            self._validate_container_info_in_full_result(result)

            # Test container-info-only mode
            result_info_only = orchestrator.resolve_dependencies(executor, only_container_info=True)

            if verbose_output:
                self.print_verbose_results("DOCKER INFO DETECTION OUTPUT (INFO ONLY):", result_info_only)

            # Validate container-info-only result
            self._validate_container_info_only_result(result_info_only)

        finally:
            if container_id:
                self.cleanup_container(container_id)

    def test_docker_info_detector_unit_tests(self) -> None:
        """Unit tests for Docker Info detector without real containers."""
        detector = DockerInfoDetector()

        # Test detector name
        assert detector.NAME == "docker-info"

        # Test system scope
        mock_executor = Mock()
        assert not detector.has_system_scope(mock_executor)

        # Test is_usable with DockerExecutor
        docker_executor = Mock(spec=DockerExecutor)
        assert detector.is_usable(docker_executor)

        # Test is_usable with non-DockerExecutor
        other_executor = Mock()
        assert not detector.is_usable(other_executor)

    def test_docker_info_detector_non_docker_executor(self) -> None:
        """Test behavior with non-DockerExecutor."""
        detector = DockerInfoDetector()
        mock_executor = Mock()  # Not a DockerExecutor

        result = detector.get_dependencies(mock_executor)

        assert not result

    def _validate_container_info_in_full_result(self, result: Dict[str, Any]) -> None:
        """Validate that container info is present in full analysis result."""
        assert isinstance(result, dict), "Result should be a dictionary"

        # Check for source
        assert "source" in result, f"Expected 'source' in result keys: {list(result.keys())}"

        container_info = result["source"]
        self._validate_container_info_structure(container_info)

        # Should also have other detectors
        other_detectors = [key for key in result.keys() if key != "source"]
        assert len(other_detectors) > 0, "Should have other detectors in full analysis"

        print(f"✓ Container info included in full analysis with {len(other_detectors)} other detectors")

    def _validate_container_info_only_result(self, result: Dict[str, Any]) -> None:
        """Validate container-info-only result structure."""
        assert isinstance(result, dict), "Result should be a dictionary"

        # Should only have source
        assert "source" in result, f"Expected 'source' in result keys: {list(result.keys())}"
        assert len(result) == 1, f"Container-info-only should have exactly 1 key, got: {list(result.keys())}"

        container_info = result["source"]
        self._validate_container_info_structure(container_info)

        print("✓ Container-info-only mode working correctly")

    def _validate_container_info_structure(self, container_info: Dict[str, Any]) -> None:
        """Validate the structure of container info."""
        assert isinstance(container_info, dict), "Container info should be a dictionary"

        # Required fields
        required_fields = ["type", "name", "image", "hash"]
        for field in required_fields:
            assert field in container_info, f"Container info should have '{field}': {container_info}"

        # Validate type field
        assert container_info["type"] == "container", f"Type should be 'container': {container_info['type']}"

        name = container_info["name"]
        image = container_info["image"]
        hash_value = container_info["hash"]

        # Validate field types and content
        assert isinstance(name, str) and len(name) > 0, f"Name should be non-empty string: {name}"
        assert isinstance(image, str) and len(image) > 0, f"Image should be non-empty string: {image}"
        assert isinstance(hash_value, str) and len(hash_value) > 0, f"Hash should be non-empty string: {hash_value}"

        # Validate hash format (should start with sha256:)
        if hash_value != "unknown":
            assert hash_value.startswith("sha256:"), f"Hash should start with 'sha256:': {hash_value}"
            assert len(hash_value) == 71, f"Hash should be 71 chars (sha256: + 64 hex): {hash_value}"

        # Optional error field
        if "error" in container_info:
            error = container_info["error"]
            assert isinstance(error, str), f"Error should be string: {error}"

        print(f"✓ Container info structure valid: {name} -> {image} ({hash_value[:19]}...)")


class TestDockerInfoDetectorIntegration:
    """Integration tests for Docker Info detector with orchestrator."""

    @pytest.mark.skipif(docker is None, reason="Docker not available")
    def test_orchestrator_only_container_info_mode(self) -> None:
        """Test orchestrator with only_container_info=True."""
        container_id = None

        try:
            # Start a test container
            base = DockerTestBase()
            container_id = base.start_container("alpine:latest", sleep_duration="30")

            executor = DockerExecutor(container_id)
            orchestrator = Orchestrator(debug=False)

            # Test only_container_info mode
            result = orchestrator.resolve_dependencies(executor, only_container_info=True)

            # Should only contain source
            assert isinstance(result, dict)
            assert "source" in result
            assert len(result) == 1

            container_info = result["source"]
            assert "type" in container_info
            assert "name" in container_info
            assert "image" in container_info
            assert "hash" in container_info
            assert container_info["type"] == "container"

        finally:
            if container_id:
                base = DockerTestBase()
                base.cleanup_container(container_id)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
