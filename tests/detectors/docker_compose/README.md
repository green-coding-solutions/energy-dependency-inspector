# Docker Compose Stack Dependency Detection Test

This directory contains tests to validate Docker Compose stack analysis using Django as an example multi-container environment.

**Based on**: [Docker Awesome Compose Django Sample](https://github.com/docker/awesome-compose/tree/master/official-documentation-samples/django/)

## Overview

The test spins up a complete Django application with PostgreSQL database using Docker compose and verifies that the dependency resolver correctly detects Docker Compose container images and their SHA256 hashes when analyzing the stack.

## Test Approach

### Docker Compose Stack Detection (`test_docker_compose_stack_detection`)

- **Purpose**: Tests Docker Compose stack analysis and container image detection
- **Executor**: Uses `DockerComposeExecutor` to analyze the entire stack
- **Container**: Uses Django + PostgreSQL stack as an example
- **Validation**: Verifies detection of container images with full SHA256 hashes
- **Focus**: Infrastructure dependencies (container images used in the stack)

The test manages the complete stack lifecycle including startup, readiness checks, and cleanup.

## Files

- `test_docker_compose_detection.py` - Main test suite for Docker Compose detection
- `conftest.py` - Pytest configuration with --verbose-resolver option
- `docker-compose.yml` - Multi-service container orchestration
- `Dockerfile` - Python web application container definition
- `requirements.txt` - Django application dependencies
- `manage.py` - Django management script
- `testproject/` - Django project files (settings, urls, wsgi)
- `README.md` - This documentation file

## Running Tests

### Prerequisites

- Docker installed and running
- Python virtual environment activated
- `pytest`, `docker`, and other dependencies from `requirements.txt` installed

### Test Execution

```bash
source venv/bin/activate
python -m pytest tests/detectors/docker_compose/test_docker_compose_detection.py -v
```

### With Verbose Resolver Output

To see the complete dependency resolver output:

```bash
source venv/bin/activate
python -m pytest tests/detectors/docker_compose/test_docker_compose_detection.py -v -s --verbose-resolver
```

The `--verbose-resolver` option displays the complete JSON output with all detected dependencies.

### Quick Integration Test

```bash
source venv/bin/activate
python -m pytest tests/detectors/docker_compose/ -v
```

## Test Dependencies

The Django application stack uses:

- **Web service**: Python 3.11-slim with Django application
- **Database service**: PostgreSQL 13 for Django backend

## Test Process

### Docker Compose Stack Detection Test

1. **Stack startup**: Builds and starts Django + PostgreSQL containers
2. **Stack readiness**: Waits for all containers to be running
3. **Stack analysis**: Uses `DockerComposeExecutor` to analyze container images
4. **Validation**: Verifies web and db services with full SHA256 image hashes
5. **Cleanup**: Stops and removes all containers and volumes

## Expected Results

### Docker Compose Stack Detection Results

✅ **Test passes**: Web and db services detected with full SHA256 image hashes
❌ **Test fails**: Container images not detected or hash validation errors

## What This Tests

### Docker Compose Stack Detection Features

- **Infrastructure analysis**: Container image detection using DockerComposeExecutor
- **Full SHA256 hashes**: Complete image hashes with sha256: prefix
- **Service mapping**: Proper extraction of service names from container names
- **Stack orchestration**: Multi-container setup analysis
- **Compose scope detection**: Proper scope identification for Docker Compose stacks

### Error Handling

- **Stack lifecycle**: Graceful container lifecycle management
- **Network dependencies**: Handling Docker compose networking
- **CLI equivalence**: Both API and formatted output work correctly

## Container Details

- **Web service**: Python 3.11-slim with Django application
- **Database service**: PostgreSQL 13 for Django backend
- **Network**: Containers communicate via Docker compose networking
- **Volumes**: PostgreSQL data persistence during test execution

## Dependencies Expected

The Docker Compose stack typically includes:

- Web service container image (built from Dockerfile)
- Database service container image (postgres:13)
- Complete SHA256 hashes for all images
- Service names mapped correctly from container names

The test validates that these infrastructure dependencies are properly detected.
