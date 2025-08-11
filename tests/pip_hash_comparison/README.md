# pip Cross-Environment Hash Testing

This directory contains tests to validate the `_generate_location_hash` function from `detectors/pip_detector.py` across different environments.

## Overview

The test ensures that the hash function produces **identical results** when the same pip packages are installed across different Ubuntu versions, validating cross-platform consistency.

## Test Approach

### Cross-Environment Hash Comparison (`test_cross_environment_hash_comparison`)

- **Purpose**: Tests hash function consistency across environments
- **Executor**: Uses `DockerExecutor` and `HostExecutor` for cross-platform analysis
- **Environments**: Ubuntu 20.04, Ubuntu 24.04, Alpine, and host system
- **Test packages**: Installs six and urllib3 for validation
- **Focus**: Consistency of `_generate_location_hash` function across platforms

The test manages virtual environments, package installation, and hash generation across multiple platforms.

## Files

- `test_cross_environment_hash.py` - Main test suite for hash comparison
- `run_cross_env_tests.sh` - Automated test runner
- `Dockerfile.test-ubuntu{20,24}` - Docker environments for Ubuntu testing
- `Dockerfile.test-alpine` - Alpine Docker environment for testing
- `README.md` - This documentation file

## Running Tests

### Prerequisites

- Docker installed and running
- Python virtual environment activated
- `pytest`, `docker`, and other dependencies from `requirements.txt` installed
- Internet connection (to pull Docker images and install packages)

### Test Execution

```bash
source venv/bin/activate
python -m pytest tests/pip_hash_comparison/test_cross_environment_hash.py -v
```

### With Output

To see the hash comparison output:

```bash
source venv/bin/activate
python -m pytest tests/pip_hash_comparison/test_cross_environment_hash.py -v -s
```

### Quick Integration Test

```bash
source venv/bin/activate
python -m pytest tests/pip_hash_comparison/ -v
```

### Automated Test Runner

The automated test runner builds Docker images and runs the complete test suite:

```bash
./tests/pip_hash_comparison/run_cross_env_tests.sh
```

This script will:

1. Build Docker images for Ubuntu 20.04, 24.04, and Alpine environments
2. Run the cross-environment hash comparison tests
3. Clean up containers on completion

## Test Process

### Cross-Environment Hash Comparison Test

1. **Host environment**: Creates virtual environment and installs test packages on host
2. **Docker environments**: Spins up Ubuntu 20.04, 24.04, and Alpine containers
3. **Package installation**: Installs identical packages in each environment
4. **Hash generation**: Uses `_generate_location_hash` in each environment
5. **Comparison**: Validates all environments produce identical hashes
6. **Cleanup**: Stops and removes containers

## Expected Results

### Cross-Environment Hash Results

✅ **Test passes**: Same packages produce identical hashes across Ubuntu 20.04, 24.04, Alpine, and host
❌ **Test fails**: Hash function behavior differs between environments

## What This Tests

### Cross-Environment Hash Features

- **Multi-platform consistency**: Hash function behaves identically across platforms
- **Virtual environment isolation**: Clean environments for reliable testing
- **Package scope validation**: Proper hash generation for pip packages
- **Real installations**: Uses actual `pip install` commands with specific versions

### Error Handling

- **Environment creation**: Proper virtual environment setup across platforms
- **Package installation**: Handling pip installation failures
- **Hash generation**: Consistent hash computation across executors

## Container Details

- **Ubuntu 20.04**: `pip-hash-cross-env-test-ubuntu20`
- **Ubuntu 24.04**: `pip-hash-cross-env-test-ubuntu24`
- **Alpine**: `pip-hash-cross-env-test-alpine`
- **Host**: Uses system Python with temporary virtual environment

## Test Packages

The test uses lightweight packages for fast execution:

- `six==1.16.0` - Python 2/3 compatibility library
- `urllib3==1.26.18` - HTTP library

The test validates that these packages produce identical hashes when installed in different environments.
