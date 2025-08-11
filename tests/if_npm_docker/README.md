# IF npm Docker Container Dependency Detection Test

This directory contains tests to validate npm dependency detection in the Impact Framework (IF) Docker container environment.

**Based on**: [Green Software Foundation IF project](https://github.com/Green-Software-Foundation/if)

## Overview

The test pulls and runs the official IF Docker image and verifies that the dependency resolver correctly detects npm packages within the container.

## Test Approach

### npm Container Detection (`test_if_npm_docker_container_detection`)

- **Purpose**: Tests npm dependency detection inside the IF Docker container
- **Executor**: Uses `DockerExecutor` to analyze container contents
- **Container**: Uses `ghcr.io/green-software-foundation/if` Docker image
- **Validation**: Verifies detection of TypeScript, Jest, and other npm packages
- **Focus**: Application dependencies installed within the IF container

The test manages the complete container lifecycle including startup, readiness checks, and cleanup.

## Files

- `test_if_npm_docker_detection.py` - Main test suite for IF npm detection
- `conftest.py` - Pytest configuration with --verbose-resolver option
- `README.md` - This documentation file

## Running Tests

### Prerequisites

- Docker installed and running
- Python virtual environment activated
- `pytest`, `docker`, and other dependencies from `requirements.txt` installed
- Internet connection (to pull the IF Docker image)

### Test Execution

```bash
source venv/bin/activate
python -m pytest tests/if_npm_docker/test_if_npm_docker_detection.py -v
```

### With Verbose Resolver Output

To see the complete dependency resolver output:

```bash
source venv/bin/activate
python -m pytest tests/if_npm_docker/test_if_npm_docker_detection.py -v -s --verbose-resolver
```

The `--verbose-resolver` option displays the complete JSON output with all detected npm dependencies.

### Quick Integration Test

```bash
source venv/bin/activate
python -m pytest tests/if_npm_docker/ -v
```

## Test Process

### npm Container Detection Test

1. **Container startup**: Pulls and starts IF Docker container
2. **Readiness check**: Waits for container with npm availability
3. **Container analysis**: Uses `DockerExecutor` to analyze npm packages inside container
4. **Validation**: Verifies TypeScript-related and other npm packages are detected correctly
5. **Cleanup**: Stops and removes the container

## Expected Results

### npm Container Detection Results

✅ **Test passes**: TypeScript, Jest, and other npm dependencies detected with correct versions and project scope
❌ **Test fails**: npm dependencies not detected or validation errors

## What This Tests

### npm Container Detection Features

- **Real-world scenario**: Production Docker container with complex npm dependencies
- **Docker integration**: Container-based dependency detection using DockerExecutor
- **Project scope detection**: Proper scope identification for npm packages in containers
- **Location hashing**: Hash generation for npm package location (if project scope)
- **Package validation**: TypeScript, Jest, and other typical Node.js project packages

### Error Handling

- **Container lifecycle**: Proper startup, readiness checks, and cleanup
- **Network dependencies**: Handling Docker image pull from registry
- **CLI equivalence**: Both API and formatted output work correctly

## Container Details

- **Image**: `ghcr.io/green-software-foundation/if` (official IF Docker image)
- **Environment**: Node.js with TypeScript and related npm dependencies
- **Package manager**: npm (with package.json and package-lock.json)

## Dependencies Expected

The IF project typically includes:

- TypeScript and @types/* packages for type definitions
- Jest for testing framework
- Various Node.js utilities and frameworks
- Build and development tools

The test validates that these categories of dependencies are properly detected.
