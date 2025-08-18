# Docker Info Detector Tests

This directory contains tests for the Docker Info detector, which extracts metadata from individual Docker containers.

## Test Structure

### `test_docker_info_detection.py`

**TestDockerInfoDetection:**

- `test_docker_info_detection_real_container()` - Integration test with real container
- `test_docker_info_detector_unit_tests()` - Unit tests for detector methods
- `test_docker_info_detector_non_docker_executor()` - Test with invalid executor

**TestDockerInfoDetectorIntegration:**

- `test_orchestrator_only_container_info_mode()` - Test container-info-only mode

## Test Coverage

### Core Functionality

- ✅ Container metadata extraction (name, image, hash)
- ✅ Both full analysis and container-info-only modes
- ✅ Simplified JSON output format (`_container-info`)
- ✅ Error handling and graceful degradation

### Integration Tests

- ✅ Real container testing with nginx:alpine and alpine:latest
- ✅ Orchestrator integration with `only_container_info=True`
- ✅ Validation of container info structure and format

### Unit Tests

- ✅ Detector name and scope validation
- ✅ Executor type checking (`is_usable()`)
- ✅ Non-DockerExecutor handling

## Running Tests

```bash
# Run all docker info detector tests
pytest tests/detectors/docker_info/ -v

# Run with verbose output from resolver
pytest tests/detectors/docker_info/ -v --verbose-resolver

# Run specific test
pytest tests/detectors/docker_info/test_docker_info_detection.py::TestDockerInfoDetection::test_docker_info_detection_real_container -v
```

## Test Requirements

- Docker daemon running
- Python `docker` library installed (`pip install docker`)
- Internet access for pulling test images (nginx:alpine, alpine:latest)

## Expected Output

### Container-Info-Only Mode

```json
{
  "_container-info": {
    "name": "container-id",
    "image": "nginx:alpine",
    "hash": "sha256:abc123..."
  }
}
```

### Full Analysis Mode

```json
{
  "_container-info": {
    "name": "container-id",
    "image": "nginx:alpine",
    "hash": "sha256:abc123..."
  },
  "dpkg": { ... },
  "apk": { ... }
}
```

## Test Validation

Tests validate:

- **Structure**: Correct JSON format and required fields
- **Types**: String values for name, image, and hash
- **Hash format**: SHA256 format validation (sha256: + 64 hex chars)
- **Integration**: Proper orchestrator behavior in different modes
- **Error handling**: Graceful handling of container access failures
