"""Test Maven Docker container dependency detection."""

import os
import sys
from typing import Dict, Any

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import pytest
from dependency_resolver.executors import DockerExecutor
from dependency_resolver.core.orchestrator import Orchestrator
from dependency_resolver.detectors.maven_detector import MavenDetector
from tests.common.docker_test_base import DockerTestBase

try:
    import docker
except ImportError:
    docker = None  # type: ignore


class TestMavenDockerDetection(DockerTestBase):
    """Test Maven dependency detection using Docker container environment."""

    TEST_IMAGE = "maven:3.9-eclipse-temurin-17"

    @pytest.mark.skipif(docker is None, reason="Docker not available")
    def test_maven_docker_container_detection(self, request: pytest.FixtureRequest) -> None:
        """Test Maven dependency detection inside a Docker container with sample project."""

        verbose_output = self.setup_verbose_output(request)
        container_id = None

        try:
            # Start container with Maven image
            container_id = self.start_container(self.TEST_IMAGE, additional_args=[])
            self.wait_for_container_ready(container_id, "mvn --version", max_wait=60)

            executor = DockerExecutor(container_id)

            # Create a simple Maven project for testing
            self._create_test_maven_project(executor)

            orchestrator = Orchestrator(debug=False, skip_system_scope=False)

            # Test with Maven project directory
            result = orchestrator.resolve_dependencies(executor, working_dir="/tmp/test-maven-project")

            if verbose_output:
                self.print_verbose_results("DEPENDENCY RESOLVER OUTPUT:", result)

            self._validate_maven_dependencies(result)

        finally:
            if container_id:
                self.cleanup_container(container_id)

    @pytest.mark.skipif(docker is None, reason="Docker not available")
    def test_maven_wrapper_detection(self, request: pytest.FixtureRequest) -> None:
        """Test Maven dependency detection using Maven wrapper (mvnw)."""

        verbose_output = self.setup_verbose_output(request)
        container_id = None

        try:
            # Start container with Maven image
            container_id = self.start_container(self.TEST_IMAGE, additional_args=[])
            self.wait_for_container_ready(container_id, "mvn --version", max_wait=60)

            executor = DockerExecutor(container_id)

            # Create a Maven project with Maven wrapper
            self._create_test_maven_project_with_wrapper(executor)

            orchestrator = Orchestrator(debug=False, skip_system_scope=False)

            # Test with Maven project directory
            result = orchestrator.resolve_dependencies(executor, working_dir="/tmp/test-maven-project")

            if verbose_output:
                self.print_verbose_results("DEPENDENCY RESOLVER OUTPUT (Maven wrapper):", result)

            self._validate_maven_dependencies(result)

        finally:
            if container_id:
                self.cleanup_container(container_id)

    @pytest.mark.skipif(docker is None, reason="Docker not available")
    def test_maven_without_maven_command(self, request: pytest.FixtureRequest) -> None:
        """Test Maven dependency detection in environment without Maven command (pom.xml parsing only)."""

        verbose_output = self.setup_verbose_output(request)
        container_id = None

        try:
            # Use a basic Eclipse Temurin JRE image without Maven
            container_id = self.start_container("eclipse-temurin:17-jre", additional_args=[])
            self.wait_for_container_ready(container_id, "java -version", max_wait=60)

            executor = DockerExecutor(container_id)

            # Create a Maven project structure with pom.xml
            self._create_test_maven_project_without_maven(executor)

            orchestrator = Orchestrator(debug=False, skip_system_scope=False)

            # Test with Maven project directory
            result = orchestrator.resolve_dependencies(executor, working_dir="/tmp/test-maven-project")

            if verbose_output:
                self.print_verbose_results("DEPENDENCY RESOLVER OUTPUT (pom.xml parsing):", result)

            self._validate_maven_dependencies_pom_only(result)

        finally:
            if container_id:
                self.cleanup_container(container_id)

    @pytest.mark.skipif(docker is None, reason="Docker not available")
    def test_maven_wrapper_priority_over_system_maven(self, request: pytest.FixtureRequest) -> None:
        """Test that Maven wrapper takes priority over system Maven when both are available."""

        verbose_output = self.setup_verbose_output(request)
        container_id = None

        try:
            # Start container with Maven image (has both system Maven and we'll add wrapper)
            container_id = self.start_container(self.TEST_IMAGE, additional_args=[])
            self.wait_for_container_ready(container_id, "mvn --version", max_wait=60)

            executor = DockerExecutor(container_id)

            # Create a Maven project with wrapper (this should be preferred)
            self._create_test_maven_project_with_wrapper(executor)

            # Create detector directly to test the command selection logic
            detector = MavenDetector(debug=True)

            # Test that wrapper is detected and preferred
            maven_cmd = detector._get_maven_command(executor, "/tmp/test-maven-project")
            assert maven_cmd == "./mvnw", f"Expected './mvnw' but got '{maven_cmd}'"

            # Test that Maven is available (should use wrapper)
            assert detector._maven_available(executor, "/tmp/test-maven-project")

            if verbose_output:
                print(f"Maven command selected: {maven_cmd}")

        finally:
            if container_id:
                self.cleanup_container(container_id)

    def _create_test_maven_project(self, executor: DockerExecutor) -> None:
        """Create a test Maven project in the container."""
        # Create project directory
        executor.execute_command("mkdir -p /tmp/test-maven-project")

        # Create a sample pom.xml
        pom_content = """<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0
         http://maven.apache.org/xsd/maven-4.0.0.xsd">
    <modelVersion>4.0.0</modelVersion>

    <groupId>com.example</groupId>
    <artifactId>test-project</artifactId>
    <version>1.0.0</version>
    <packaging>jar</packaging>

    <properties>
        <maven.compiler.source>17</maven.compiler.source>
        <maven.compiler.target>17</maven.compiler.target>
        <junit.version>5.9.0</junit.version>
    </properties>

    <dependencies>
        <dependency>
            <groupId>org.junit.jupiter</groupId>
            <artifactId>junit-jupiter</artifactId>
            <version>${junit.version}</version>
            <scope>test</scope>
        </dependency>
        <dependency>
            <groupId>com.fasterxml.jackson.core</groupId>
            <artifactId>jackson-core</artifactId>
            <version>2.15.2</version>
        </dependency>
        <dependency>
            <groupId>org.apache.commons</groupId>
            <artifactId>commons-lang3</artifactId>
            <version>3.12.0</version>
        </dependency>
    </dependencies>
</project>"""

        # Write pom.xml
        executor.execute_command(f"cat > /tmp/test-maven-project/pom.xml << 'EOF'\n{pom_content}\nEOF")

        # Create basic source structure
        executor.execute_command("mkdir -p /tmp/test-maven-project/src/main/java")
        executor.execute_command("mkdir -p /tmp/test-maven-project/src/test/java")

    def _create_test_maven_project_with_wrapper(self, executor: DockerExecutor) -> None:
        """Create a test Maven project with Maven wrapper in the container."""
        # First create the basic Maven project
        self._create_test_maven_project(executor)

        # Create Maven wrapper script (simplified version)
        mvnw_content = """#!/bin/sh
# Simple Maven wrapper for testing
exec mvn "$@"
"""
        executor.execute_command(f"cat > /tmp/test-maven-project/mvnw << 'EOF'\n{mvnw_content}\nEOF")
        executor.execute_command("chmod +x /tmp/test-maven-project/mvnw")

        # Create .mvn directory and wrapper properties (typical Maven wrapper structure)
        executor.execute_command("mkdir -p /tmp/test-maven-project/.mvn/wrapper")

        wrapper_properties = """distributionUrl=https://repo.maven.apache.org/maven2/org/apache/maven/apache-maven/3.9.4/apache-maven-3.9.4-bin.zip
wrapperUrl=https://repo.maven.apache.org/maven2/org/apache/maven/wrapper/maven-wrapper/3.2.0/maven-wrapper-3.2.0.jar
"""
        executor.execute_command(
            f"cat > /tmp/test-maven-project/.mvn/wrapper/maven-wrapper.properties << 'EOF'\n{wrapper_properties}\nEOF"
        )

    def _create_test_maven_project_without_maven(self, executor: DockerExecutor) -> None:
        """Create a test Maven project structure without using Maven commands."""
        # Create project directory
        executor.execute_command("mkdir -p /tmp/test-maven-project")

        # Create the same pom.xml as above
        pom_content = """<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0
         http://maven.apache.org/xsd/maven-4.0.0.xsd">
    <modelVersion>4.0.0</modelVersion>

    <groupId>com.example</groupId>
    <artifactId>test-project</artifactId>
    <version>1.0.0</version>
    <packaging>jar</packaging>

    <properties>
        <maven.compiler.source>17</maven.compiler.source>
        <maven.compiler.target>17</maven.compiler.target>
        <junit.version>5.9.0</junit.version>
    </properties>

    <dependencies>
        <dependency>
            <groupId>org.junit.jupiter</groupId>
            <artifactId>junit-jupiter</artifactId>
            <version>${junit.version}</version>
            <scope>test</scope>
        </dependency>
        <dependency>
            <groupId>com.fasterxml.jackson.core</groupId>
            <artifactId>jackson-core</artifactId>
            <version>2.15.2</version>
        </dependency>
        <dependency>
            <groupId>org.apache.commons</groupId>
            <artifactId>commons-lang3</artifactId>
            <version>3.12.0</version>
        </dependency>
    </dependencies>
</project>"""

        # Write pom.xml
        executor.execute_command(f"cat > /tmp/test-maven-project/pom.xml << 'EOF'\n{pom_content}\nEOF")

    def _validate_maven_dependencies(self, result: Dict[str, Any]) -> None:
        """Validate Maven dependencies in the result."""
        self.validate_basic_structure(result, "maven")

        maven_result = result["maven"]
        dependencies = maven_result["dependencies"]

        # Should have project scope and location
        assert maven_result["scope"] == "project"
        assert "location" in maven_result
        assert maven_result["location"] == "/tmp/test-maven-project"

        # Should have hash for project scope
        if dependencies:
            assert "hash" in maven_result

        # Validate dependencies structure
        self.validate_dependency_structure(dependencies)

        # Should have some of our test dependencies (excluding test scope)
        expected_deps = ["com.fasterxml.jackson.core:jackson-core", "org.apache.commons:commons-lang3"]

        for dep in expected_deps:
            assert dep in dependencies, f"Expected dependency {dep} not found in {list(dependencies.keys())}"
            assert "version" in dependencies[dep]
            assert len(dependencies[dep]["version"]) > 0

        # Should NOT have test-scoped dependencies
        assert "org.junit.jupiter:junit-jupiter" not in dependencies

    def _validate_maven_dependencies_pom_only(self, result: Dict[str, Any]) -> None:
        """Validate Maven dependencies when using pom.xml parsing only."""
        self.validate_basic_structure(result, "maven")

        maven_result = result["maven"]
        dependencies = maven_result["dependencies"]

        # Should have project scope and location
        assert maven_result["scope"] == "project"
        assert "location" in maven_result
        assert maven_result["location"] == "/tmp/test-maven-project"

        # Should have hash for project scope
        if dependencies:
            assert "hash" in maven_result

        # Validate dependencies structure
        self.validate_dependency_structure(dependencies)

        # Should have our test dependencies with resolved versions
        expected_deps = {
            "com.fasterxml.jackson.core:jackson-core": "2.15.2",
            "org.apache.commons:commons-lang3": "3.12.0",
        }

        for dep, expected_version in expected_deps.items():
            assert dep in dependencies, f"Expected dependency {dep} not found in {list(dependencies.keys())}"
            assert dependencies[dep]["version"] == expected_version

        # Should NOT have test-scoped dependencies
        assert "org.junit.jupiter:junit-jupiter" not in dependencies
