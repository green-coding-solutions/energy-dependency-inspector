# Django Docker Compose Dependency Detection Test

This directory contains a test to validate pip dependency detection in a real-world Django Docker compose environment.

**Based on**: [Docker Awesome Compose Django Sample](https://github.com/docker/awesome-compose/tree/master/official-documentation-samples/django/)

## Overview

The test spins up a complete Django application with PostgreSQL database using Docker compose and verifies that the dependency resolver correctly detects pip packages in the containerized environment.

## Test Approach

1. **Real Django application**: Complete Django project with database configuration
2. **Docker compose stack**: Multi-container setup with web service and PostgreSQL
3. **Dependency validation**: Verifies detection of Django, psycopg2-binary, and other pip packages
4. **Container lifecycle management**: Proper startup, readiness checks, and cleanup

## Files

- `test_django_docker_detection.py` - Main test suite
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

1. **Stack startup**: Builds and starts Django + PostgreSQL containers
2. **Readiness check**: Waits for web container with pip availability
3. **Dependency detection**: Runs `DependencyResolver` against the container
4. **Validation**: Verifies Django and psycopg2 packages are detected with correct versions
5. **Format testing**: Tests both raw and JSON-formatted output
6. **Cleanup**: Stops and removes all containers and volumes

## Expected Result

✅ **Test passes**: Django v3.2.25 and psycopg2-binary detected with correct versions and location hash
❌ **Test fails**: Dependencies not detected or validation errors

## What This Tests

- **Real-world scenario**: Complex application with multiple dependencies
- **Docker integration**: Container-based dependency detection
- **CLI equivalence**: Both API and formatted output work correctly
- **Location hashing**: Proper hash generation for pip package location
- **Error handling**: Graceful container lifecycle management

## Container Details

- **Web service**: Python 3.11-slim with Django application
- **Database service**: PostgreSQL 13 for Django backend
- **Network**: Containers communicate via Docker compose networking
- **Volumes**: PostgreSQL data persistence during test execution
