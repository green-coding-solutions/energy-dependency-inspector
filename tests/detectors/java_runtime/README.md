# Java Runtime Detector Tests

## Docker Test

The Java Runtime detector tests use Docker containers to simulate production environments where JAR files are present with or without Java runtime tools.

## Image Used

- **Primary**: `eclipse-temurin:17-jre` - Modern OpenJDK 17 runtime environment
- **Secondary**: `alpine:latest` - Minimal Linux for testing JAR detection without Java runtime

## Test Commands

The tests verify the following functionality:

- `java -version` (Java runtime verification)
- JAR file discovery using `find` command
- JAR manifest parsing using `unzip` command
- File size detection using `stat` command
- Hash generation using `find` and `sort` commands

## Test Scenarios

### 1. Full Java Runtime Detection (`test_java_runtime_docker_container_detection`)

**Environment**: eclipse-temurin:17-jre with created test JAR files

**Setup**:

- Creates `/tmp/test-java-app/` directory structure
- Generates test JAR files with different version detection scenarios:
  - `test-app-1.2.3.jar` - JAR with manifest-based version
  - `lib/commons-lang3-3.12.0.jar` - JAR with filename-based version
  - `lib/legacy.jar` - JAR without version information
  - `spring-boot.jar` - Larger JAR file for size testing

**Validates**:

- Correct scope (`project`)
- JAR file discovery and metadata extraction
- Version parsing from manifests and filenames
- Java runtime metadata collection
- Location-based hash generation

### 2. Java Available, No JARs (`test_java_runtime_no_jars_but_java_available`)

**Environment**: eclipse-temurin:17-jre with empty directory

**Validates**:

- Detector correctly reports no dependencies when no JAR files present
- Java runtime availability doesn't trigger detection without JARs

### 3. JARs Present, No Java (`test_java_runtime_jars_no_java`)

**Environment**: alpine:latest (no Java) with created JAR files

**Validates**:

- JAR-based detection works without Java runtime
- Missing Java metadata when Java unavailable
- Detector prioritizes JAR file presence over Java availability

## Running Tests

### All Java Runtime Tests

```bash
pytest tests/detectors/java_runtime/
```

### Verbose Output

```bash
pytest tests/detectors/java_runtime/ --verbose-resolver
```

### Specific Test

```bash
# Full detection test
pytest tests/detectors/java_runtime/test_java_runtime_docker_detection.py::TestJavaRuntimeDockerDetection::test_java_runtime_docker_container_detection

# No JARs test
pytest tests/detectors/java_runtime/test_java_runtime_docker_detection.py::TestJavaRuntimeDockerDetection::test_java_runtime_no_jars_but_java_available

# No Java test
pytest tests/detectors/java_runtime/test_java_runtime_docker_detection.py::TestJavaRuntimeDockerDetection::test_java_runtime_jars_no_java
```

### Debug Mode

```bash
pytest tests/detectors/java_runtime/ -s --tb=short
```

## Expected Test Output

### Successful Detection

```json
{
  "java-runtime": {
    "scope": "project",
    "location": "/tmp/test-java-app",
    "dependencies": {
      "test-app-1.2.3.jar": {
        "version": "1.2.3",
        "size": "1234"
      },
      "lib/commons-lang3-3.12.0.jar": {
        "version": "3.12.0",
        "size": "5678"
      },
      "lib/legacy.jar": {
        "version": "unknown",
        "size": "9012"
      }
    },
    "metadata": {
      "java_version": "17.0.8",
      "java_runtime": "OpenJDK Runtime Environment",
      "java_vendor": "Eclipse Adoptium"
    },
    "hash": "sha256:abc123..."
  }
}
```

## Test Requirements

- Docker must be available and running
- Python `docker` package installed (`pip install docker`)
- Sufficient disk space for test container images
- Network access to pull Docker images

## Troubleshooting

### Docker Permission Issues

```bash
# Add user to docker group (requires logout/login)
sudo usermod -aG docker $USER
```

### Container Startup Failures

```bash
# Verify Docker daemon is running
systemctl status docker

# Check available images
docker images | grep temurin
```

### Test Timeout Issues

```bash
# Increase timeout for slow networks
export DOCKER_TEST_TIMEOUT=120
pytest tests/detectors/java_runtime/
```

## Performance Notes

- Tests create minimal JAR files (< 1MB total) for fast execution
- Container startup typically takes 10-30 seconds
- Full test suite runs in under 2 minutes on modern hardware
- Cleanup is performed automatically even on test failures
