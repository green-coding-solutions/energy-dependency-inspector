# Django Docker Compose Dependency Detection Test

This directory contains tests to validate both Docker Compose stack analysis and individual container dependency detection in a real-world Django Docker compose environment.

**Based on**: [Docker Awesome Compose Django Sample](https://github.com/docker/awesome-compose/tree/master/official-documentation-samples/django/)

## Overview

The test spins up a complete Django application with PostgreSQL database using Docker compose and verifies that the dependency resolver correctly:

- Detects Docker Compose container images and their SHA256 hashes when analyzing the stack
- Detects pip packages when analyzing individual containers

## Test Approach

The test suite includes two distinct test cases:

### 1. Container Pip Detection (`test_django_docker_container_pip_detection`)

- **Purpose**: Tests pip dependency detection inside individual Docker containers
- **Executor**: Uses `DockerExecutor` to analyze container contents
- **Validation**: Verifies detection of Django, psycopg2-binary, and other pip packages
- **Focus**: Application dependencies installed within containers

### 2. Docker Compose Stack Detection (`test_django_docker_compose_stack_detection`)

- **Purpose**: Tests Docker Compose stack analysis and container image detection
- **Executor**: Uses `DockerComposeExecutor` to analyze the entire stack
- **Validation**: Verifies detection of container images with full SHA256 hashes
- **Focus**: Infrastructure dependencies (container images used in the stack)

Both tests use the same Django + PostgreSQL setup with proper container lifecycle management.

## Files

- `test_django_docker_detection.py` - Main test suite with both container and stack tests
- `conftest.py` - Pytest configuration with custom command-line options
- `docker-compose.yml` - Multi-service container orchestration
- `Dockerfile` - Python web application container definition
- `requirements.txt` - Django application dependencies
- `manage.py` - Django management script
- `testproject/` - Django project files (settings, urls, wsgi)

## Running Tests

### Prerequisites

- Docker installed and running
- Python virtual environment activated
- `pytest`, `docker`, and other dependencies from `requirements.txt` installed

### Test Execution

```bash
source venv/bin/activate
python -m pytest tests/django_docker_compose/test_django_docker_detection.py -v
```

### With Verbose Resolver Output

To see the complete dependency resolver output:

```bash
source venv/bin/activate
python -m pytest tests/django_docker_compose/test_django_docker_detection.py -v -s --verbose-resolver
```

The `--verbose-resolver` option displays the complete JSON output with all detected dependencies.

### Quick Integration Test

```bash
source venv/bin/activate
python -m pytest tests/django_docker_compose/ -v
```

## Test Dependencies

The Django application uses:

- `Django>=3.0,<4.0` - Web framework
- `psycopg2-binary>=2.8` - PostgreSQL adapter

## Test Process

### Container Pip Detection Test

1. **Stack startup**: Builds and starts Django + PostgreSQL containers
2. **Readiness check**: Waits for web container with pip availability
3. **Container analysis**: Uses `DockerExecutor` to analyze pip packages inside web container
4. **Validation**: Verifies Django and psycopg2 packages are detected with correct versions
5. **Cleanup**: Stops and removes all containers and volumes

### Docker Compose Stack Detection Test

1. **Stack startup**: Builds and starts Django + PostgreSQL containers
2. **Stack readiness**: Waits for all containers to be running
3. **Stack analysis**: Uses `DockerComposeExecutor` to analyze container images
4. **Validation**: Verifies web and db services with full SHA256 image hashes
5. **Cleanup**: Stops and removes all containers and volumes

## Expected Results

### Container Pip Detection Results

✅ **Test passes**: Django v3.2.25 and psycopg2-binary detected with correct versions and location hash
❌ **Test fails**: Pip dependencies not detected or validation errors

### Docker Compose Stack Detection Results

✅ **Test passes**: Web and db services detected with full SHA256 image hashes
❌ **Test fails**: Container images not detected or hash validation errors

## What This Tests

### Container Pip Detection Features

- **Real-world scenario**: Complex application with multiple pip dependencies
- **Docker integration**: Container-based dependency detection using DockerExecutor
- **Location hashing**: Proper hash generation for pip package location
- **Pip package validation**: Django, psycopg2-binary, and other packages

### Docker Compose Stack Detection Features

- **Infrastructure analysis**: Container image detection using DockerComposeExecutor
- **Full SHA256 hashes**: Complete image hashes with sha256: prefix
- **Service mapping**: Proper extraction of service names from container names
- **Stack orchestration**: Multi-container setup analysis

### Both Tests

- **Error handling**: Graceful container lifecycle management
- **CLI equivalence**: Both API and formatted output work correctly

## Container Details

- **Web service**: Python 3.11-slim with Django application
- **Database service**: PostgreSQL 13 for Django backend
- **Network**: Containers communicate via Docker compose networking
- **Volumes**: PostgreSQL data persistence during test execution
