# pip Docker Container Dependency Detection Test

This directory contains tests to validate pip dependency detection using a simple Python Docker container environment.

## Overview

The test spins up a Python Docker container, installs test packages, and verifies that the dependency resolver correctly detects pip packages when analyzing the container.

## Test Approach

### pip Container Detection (`test_pip_docker_container_detection`)

- **Purpose**: Tests pip dependency detection inside Docker containers
- **Executor**: Uses `DockerExecutor` to analyze container contents
- **Container**: Uses `python:3.11-slim` Docker image
- **Test packages**: Installs requests, numpy, and click for validation
- **Focus**: pip project dependencies in containers (skips system packages for performance)

The test manages the complete container lifecycle including startup, package installation, and cleanup.

## Files

- `test_pip_docker_detection.py` - Main test suite for pip detection
- `conftest.py` - Pytest configuration with --verbose-resolver option
- `README.md` - This documentation file

## Running Tests

### Prerequisites

- Docker installed and running
- Python virtual environment activated
- `pytest`, `docker`, and other dependencies from `requirements.txt` installed
- Internet connection (to pull Python Docker image and install packages)

### Test Execution

```bash
source venv/bin/activate
python -m pytest tests/pip_detector/test_pip_docker_detection.py -v
```

### With Verbose Resolver Output

To see the complete dependency resolver output:

```bash
source venv/bin/activate
python -m pytest tests/pip_detector/test_pip_docker_detection.py -v -s --verbose-resolver
```

The `--verbose-resolver` option displays the complete JSON output with all detected pip dependencies.

### Quick Integration Test

```bash
source venv/bin/activate
python -m pytest tests/pip_detector/ -v
```

## Test Process

### pip Container Detection Test

1. **Container startup**: Pulls and starts Python Docker container
2. **Package installation**: Installs test packages (requests, numpy, click)
3. **Readiness check**: Waits for container with pip availability
4. **Container analysis**: Uses `DockerExecutor` to analyze pip packages inside container
5. **Validation**: Verifies test packages are detected with correct versions
6. **Cleanup**: Stops and removes the container

## Expected Results

### pip Container Detection Results

✅ **Test passes**: Test packages (requests, numpy, click) detected with correct versions
❌ **Test fails**: Pip dependencies not detected or validation errors

## What This Tests

### pip Container Detection Features

- **Simple container setup**: Single Python container without complex dependencies
- **Docker integration**: Container-based dependency detection using DockerExecutor
- **Scope detection**: Proper scope identification for pip packages in containers
- **Package validation**: Common Python packages with known versions

### Error Handling

- **Container lifecycle**: Proper startup, package installation, and cleanup
- **Network dependencies**: Handling Docker image pull and pip package installation
- **CLI equivalence**: Both API and formatted output work correctly

## Container Details

- **Image**: `python:3.11-slim` (official Python Docker image)
- **Environment**: Python with pip package manager
- **Test packages**: requests==2.31.0, numpy==1.24.3, click==8.1.7

## Dependencies Expected

The test validates detection of:

- requests - HTTP library
- numpy - Scientific computing library
- click - Command line interface library
- Their respective dependencies

The test validates that these packages are properly detected with correct versions and scope.
