"""Test Java runtime Docker container dependency detection."""

import os
import sys
from typing import Dict, Any

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import pytest
from dependency_resolver.executors import DockerExecutor
from dependency_resolver.core.orchestrator import Orchestrator
from tests.common.docker_test_base import DockerTestBase

try:
    import docker
except ImportError:
    docker = None  # type: ignore


class TestJavaRuntimeDockerDetection(DockerTestBase):
    """Test Java runtime dependency detection using Docker container environment."""

    TEST_IMAGE = "eclipse-temurin:17-jre"

    @pytest.mark.skipif(docker is None, reason="Docker not available")
    def test_java_runtime_docker_container_detection(self, request: pytest.FixtureRequest) -> None:
        """Test Java runtime dependency detection inside a Docker container."""

        verbose_output = self.setup_verbose_output(request)
        container_id = None

        try:
            container_id = self.start_container(self.TEST_IMAGE, additional_args=[])
            self.wait_for_container_ready(container_id, "java -version", max_wait=60)

            # Create sample JAR files for testing
            self._setup_test_jar_files(container_id)

            executor = DockerExecutor(container_id)
            orchestrator = Orchestrator(debug=False, skip_system_scope=False)

            result = orchestrator.resolve_dependencies(executor, working_dir="/tmp/test-java-app")

            if verbose_output:
                self.print_verbose_results("DEPENDENCY RESOLVER OUTPUT:", result)

            self._validate_java_runtime_dependencies(result)

        finally:
            if container_id:
                self.cleanup_container(container_id)

    def _setup_test_jar_files(self, container_id: str) -> None:
        """Create test JAR files with manifests for detection testing."""
        # Create test directory
        docker_client = docker.from_env()
        container = docker_client.containers.get(container_id)

        # Install zip utility first - update package list only if needed
        result = container.exec_run(["apt-get", "update"])
        result = container.exec_run(["apt-get", "install", "-y", "zip"])
        if result.exit_code != 0:
            print(f"Failed to install zip: {result.output.decode()}")

        # Create application directory
        result = container.exec_run(["mkdir", "-p", "/tmp/test-java-app/lib"])
        if result.exit_code != 0:
            print(f"Failed to create directories: {result.output.decode()}")

        # Create working directory for temp files
        result = container.exec_run(["mkdir", "-p", "/tmp/work"])

        # Create a simple dummy file for JARs
        result = container.exec_run(["sh", "-c", "echo 'dummy content' > /tmp/work/dummy.txt"])

        # Create manifest file with proper format
        manifest_content = "Manifest-Version: 1.0\\nImplementation-Title: test-app\\nImplementation-Version: 1.2.3\\nImplementation-Vendor: Test Company\\nMain-Class: com.example.TestApp\\n\\n"

        # Create META-INF directory and manifest
        result = container.exec_run(["mkdir", "-p", "/tmp/work/META-INF"])
        result = container.exec_run(["sh", "-c", f"echo -e '{manifest_content}' > /tmp/work/META-INF/MANIFEST.MF"])

        # Create JAR with manifest using working directory approach
        result = container.exec_run(
            ["sh", "-c", "cd /tmp/work && zip -r /tmp/test-java-app/test-app-1.2.3.jar META-INF/"]
        )
        if result.exit_code != 0:
            print(f"Failed to create test-app JAR: {result.output.decode()}")

        # Create another JAR with filename-based version
        result = container.exec_run(
            ["sh", "-c", "cd /tmp/work && zip /tmp/test-java-app/lib/commons-lang3-3.12.0.jar dummy.txt"]
        )
        if result.exit_code != 0:
            print(f"Failed to create commons JAR: {result.output.decode()}")

        # Create JAR without version info
        result = container.exec_run(["sh", "-c", "cd /tmp/work && zip /tmp/test-java-app/lib/legacy.jar dummy.txt"])
        if result.exit_code != 0:
            print(f"Failed to create legacy JAR: {result.output.decode()}")

        # Create a larger JAR to test different sizes
        result = container.exec_run(
            ["sh", "-c", "dd if=/dev/zero of=/tmp/work/large.txt bs=1024 count=100 2>/dev/null"]
        )
        result = container.exec_run(["sh", "-c", "cd /tmp/work && zip /tmp/test-java-app/spring-boot.jar large.txt"])
        if result.exit_code != 0:
            print(f"Failed to create spring-boot JAR: {result.output.decode()}")

        # Verify files were created
        result = container.exec_run(["ls", "-la", "/tmp/test-java-app/", "/tmp/test-java-app/lib/"])
        print(f"Created files: {result.output.decode()}")

    def _validate_java_runtime_dependencies(self, result: Dict[str, Any]) -> None:
        """Validate Java runtime artifacts in the result."""
        assert "java-runtime" in result

        java_runtime_result = result["java-runtime"]
        assert "type" in java_runtime_result
        assert java_runtime_result["type"] == "runtime"
        assert "location" in java_runtime_result
        assert "artifacts" in java_runtime_result

        artifacts = java_runtime_result["artifacts"]
        assert isinstance(artifacts, dict)
        assert len(artifacts) > 0

        # Validate that we detected our test JAR files
        jar_names = list(artifacts.keys())

        # Should find our test JARs
        assert any("test-app" in jar for jar in jar_names), f"test-app JAR not found in {jar_names}"
        assert any("commons-lang3" in jar for jar in jar_names), f"commons-lang3 JAR not found in {jar_names}"
        assert any("legacy.jar" in jar for jar in jar_names), f"legacy.jar not found in {jar_names}"
        assert any("spring-boot.jar" in jar for jar in jar_names), f"spring-boot.jar not found in {jar_names}"

        # Validate JAR artifact structure
        for jar_info in artifacts.values():
            assert "version" in jar_info
            assert "size" in jar_info
            assert "type" in jar_info
            assert "path" in jar_info
            assert isinstance(jar_info["version"], str)
            assert isinstance(jar_info["size"], int)
            assert jar_info["type"] == "jar"
            assert jar_info["size"] > 0  # Size should be positive
            assert jar_info["path"].startswith("/")  # Absolute path

        # Validate specific version extraction
        test_app_jar = next((name for name in jar_names if "test-app" in name), None)
        if test_app_jar:
            assert artifacts[test_app_jar]["version"] == "1.2.3"

        commons_jar = next((name for name in jar_names if "commons-lang3" in name), None)
        if commons_jar:
            assert artifacts[commons_jar]["version"] == "3.12.0"

        legacy_jar = next((name for name in jar_names if "legacy.jar" in name), None)
        if legacy_jar:
            assert artifacts[legacy_jar]["version"] == "unknown"

        # Validate Java runtime environment if present
        if "runtime_environment" in java_runtime_result:
            runtime_env = java_runtime_result["runtime_environment"]
            assert "platform" in runtime_env
            assert runtime_env["platform"] == "java"
            if "version" in runtime_env:
                assert runtime_env["version"].startswith("17")
            if "runtime" in runtime_env:
                assert "Runtime Environment" in runtime_env["runtime"]
            if "vendor" in runtime_env:
                assert len(runtime_env["vendor"]) > 0

        # Validate hash is present
        assert "hash" in java_runtime_result
        assert len(java_runtime_result["hash"]) == 64  # SHA256 hex string

    @pytest.mark.skipif(docker is None, reason="Docker not available")
    def test_java_runtime_no_jars_but_java_available(self, request: pytest.FixtureRequest) -> None:
        """Test Java runtime detection when Java is available but no JARs present."""

        verbose_output = self.setup_verbose_output(request)
        container_id = None

        try:
            container_id = self.start_container(self.TEST_IMAGE, additional_args=[])
            self.wait_for_container_ready(container_id, "java -version", max_wait=60)

            executor = DockerExecutor(container_id)
            orchestrator = Orchestrator(debug=False, skip_system_scope=False)

            # Test in empty directory
            result = orchestrator.resolve_dependencies(executor, working_dir="/tmp")

            if verbose_output:
                self.print_verbose_results("DEPENDENCY RESOLVER OUTPUT (No JARs):", result)

            # Should not detect java-runtime without JAR files
            assert "java-runtime" not in result or len(result.get("java-runtime", {}).get("artifacts", {})) == 0

        finally:
            if container_id:
                self.cleanup_container(container_id)

    @pytest.mark.skipif(docker is None, reason="Docker not available")
    def test_java_runtime_jars_no_java(self, request: pytest.FixtureRequest) -> None:
        """Test Java runtime detection when JARs exist but Java is not available."""

        verbose_output = self.setup_verbose_output(request)
        container_id = None

        try:
            # Use a minimal image without Java runtime
            container_id = self.start_container("alpine:latest", additional_args=[])
            self.wait_for_container_ready(container_id, "echo ready", max_wait=30)

            # Create sample JAR files without Java runtime
            docker_client = docker.from_env()
            container = docker_client.containers.get(container_id)

            # Install zip and create directories
            result = container.exec_run(["apk", "add", "--no-cache", "zip"])
            if result.exit_code != 0:
                print(f"Failed to install zip: {result.output.decode()}")

            result = container.exec_run(["mkdir", "-p", "/tmp/test-java-app"])
            result = container.exec_run(["mkdir", "-p", "/tmp/work"])

            # Create dummy content file
            result = container.exec_run(["sh", "-c", "echo 'fake jar content' > /tmp/work/dummy.txt"])

            # Create JAR file using proper shell command
            result = container.exec_run(["sh", "-c", "cd /tmp/work && zip /tmp/test-java-app/app.jar dummy.txt"])
            if result.exit_code != 0:
                print(f"Failed to create app.jar: {result.output.decode()}")

            # Verify file was created
            result = container.exec_run(["ls", "-la", "/tmp/test-java-app/"])
            print(f"Created files in Alpine: {result.output.decode()}")

            executor = DockerExecutor(container_id)
            orchestrator = Orchestrator(debug=False, skip_system_scope=False)

            dependencies_result = orchestrator.resolve_dependencies(executor, working_dir="/tmp/test-java-app")

            if verbose_output:
                self.print_verbose_results("DEPENDENCY RESOLVER OUTPUT (JARs, No Java):", dependencies_result)

            # Should detect java-runtime based on JAR files even without Java runtime
            assert "java-runtime" in dependencies_result
            java_runtime_result = dependencies_result["java-runtime"]
            assert java_runtime_result["type"] == "runtime"
            assert len(java_runtime_result["artifacts"]) > 0
            assert "app.jar" in java_runtime_result["artifacts"]

            # Should not have Java runtime environment since Java is not available
            assert "runtime_environment" not in java_runtime_result

        finally:
            if container_id:
                self.cleanup_container(container_id)
