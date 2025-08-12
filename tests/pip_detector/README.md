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

### Virtual Environment Detection Tests (`test_pip_venv_detection.py`)

Comprehensive test suite covering all virtual environment detection scenarios:

- **`test_venv_path_argument`**: Tests detection when `--venv-path` argument is provided
- **`test_virtual_env_environment_variable`**: Tests detection using `VIRTUAL_ENV` environment variable
- **`test_venv_directory_in_project`**: Tests detection when venv directory exists in project directory
- **`test_virtualenvs_project_name_detection`**: Tests detection using `~/.virtualenvs/{project_name}` pattern
- **`test_venv_located_at_opt_venv`**: Tests system-wide fallback mechanism finding venv at `/opt/venv`
- **`test_no_venv_found_returns_empty`**: Tests behavior when no venv is found

All tests use Docker containers with `python:3.11-slim` and install test packages (requests, click) for validation.

## Files

- `test_pip_docker_detection.py` - Main test suite for pip detection
- `test_pip_venv_detection.py` - Virtual environment detection test suite
- `conftest.py` - Pytest configuration with --verbose-resolver option
- `README.md` - This documentation file

## Running Tests

### Prerequisites

- Docker installed and running
- Python virtual environment activated
- `pytest`, `docker`, and other dependencies from `requirements.txt` installed
- Internet connection (to pull Python Docker image and install packages)

### Test Execution

#### All pip detector tests

```bash
source venv/bin/activate
python -m pytest tests/pip_detector/ -v
```

#### Docker detection tests only

```bash
source venv/bin/activate
python -m pytest tests/pip_detector/test_pip_docker_detection.py -v
```

#### Virtual environment detection tests only

```bash
source venv/bin/activate
python -m pytest tests/pip_detector/test_pip_venv_detection.py -v
```

#### Specific venv detection test

```bash
source venv/bin/activate
python -m pytest tests/pip_detector/test_pip_venv_detection.py::TestPipVenvDetection::test_venv_located_at_opt_venv -v
```

### With Verbose Resolver Output

To see the complete dependency resolver output:

```bash
source venv/bin/activate
python -m pytest tests/pip_detector/test_pip_venv_detection.py -v -s --verbose-resolver
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

### Virtual Environment Detection Features

- **Explicit venv path**: Detection via `--venv-path` argument
- **Environment variables**: Detection via `VIRTUAL_ENV` environment variable
- **Project-local venvs**: Detection of `venv/`, `.venv/`, `env/` directories in project
- **User venv patterns**: Detection via `~/.virtualenvs/{project_name}` pattern
- **System-wide fallback**: Container-only fallback searching `/opt`, `/home`, `/usr/local`
- **Error handling**: Graceful handling when no venv is found

### Error Handling

- **Container lifecycle**: Proper startup, package installation, and cleanup
- **Network dependencies**: Handling Docker image pull and pip package installation
- **CLI equivalence**: Both API and formatted output work correctly
- **Venv discovery**: Robust fallback mechanisms for various venv locations

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
