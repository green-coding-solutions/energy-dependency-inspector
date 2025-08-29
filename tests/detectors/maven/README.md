# Maven Detector Tests

This directory contains tests for the Maven dependency detector.

## Docker Test

The Maven detector tests use Docker containers to create controlled environments for testing Maven dependency detection.

### Images Used

- **`maven:3.9-eclipse-temurin-17`**: Full Maven environment with Maven CLI available
- **`eclipse-temurin:17-jre`**: Java runtime only, for testing pom.xml parsing without Maven command

### Test Commands

The tests verify these commands work in the target environment:

- `mvn --version` / `./mvnw --version` (Maven availability)
- `java -version` (Java runtime verification)
- `mvn dependency:list -B -q -DoutputFile=/dev/stdout -DexcludeTransitive=true` (dependency extraction)

### Test Scenarios

1. **Maven with CLI**: Tests dependency resolution using system Maven command
2. **Maven with Wrapper**: Tests dependency resolution using Maven wrapper (mvnw)
3. **Maven Wrapper Priority**: Tests that Maven wrapper takes priority over system Maven
4. **Maven without CLI**: Tests pom.xml parsing when Maven command is unavailable

### Running Tests

```bash
# Run all Maven detector tests
pytest tests/detectors/maven/

# Run with verbose output
pytest tests/detectors/maven/ --verbose-resolver

# Run specific test
pytest tests/detectors/maven/test_maven_docker_detection.py::TestMavenDockerDetection::test_maven_docker_container_detection

# Run Maven wrapper tests
pytest tests/detectors/maven/test_maven_docker_detection.py::TestMavenDockerDetection::test_maven_wrapper_detection

# Run Maven wrapper priority test
pytest tests/detectors/maven/test_maven_docker_detection.py::TestMavenDockerDetection::test_maven_wrapper_priority_over_system_maven

# Run pom.xml parsing test only
pytest tests/detectors/maven/test_maven_docker_detection.py::TestMavenDockerDetection::test_maven_without_maven_command
```

### Test Project Structure

The tests create a sample Maven project with:

```text
/tmp/test-maven-project/
├── pom.xml
└── src/
    ├── main/java/
    └── test/java/
```

**Sample Dependencies in Test:**

- `com.fasterxml.jackson.core:jackson-core:2.15.2` (compile scope)
- `org.apache.commons:commons-lang3:3.12.0` (compile scope)
- `org.junit.jupiter:junit-jupiter:5.9.0` (test scope - should be excluded)

### Validation

The tests verify:

- Maven detector is properly identified in results
- Project scope detection works correctly
- Location path is correctly resolved
- Dependencies are extracted with proper versions
- Test-scoped dependencies are excluded
- Hash generation works for project scope
- Both Maven CLI and pom.xml parsing approaches work
- Property resolution works (e.g., `${junit.version}`)

### Notes

- Tests use temporary directories to avoid conflicts
- Test dependencies are chosen to be lightweight and stable
- Tests verify both positive cases (dependencies found) and edge cases (no Maven CLI)
