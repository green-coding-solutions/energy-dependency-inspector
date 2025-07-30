# Cross-Environment Hash Testing

This directory contains tests to validate the `_generate_location_hash` function from `detectors/pip_detector.py` across different Ubuntu environments.

## Overview

The test ensures that the hash function produces **identical results** when the same pip packages are installed across different Ubuntu versions, validating cross-platform consistency.

## Test Approach

1. **Real pip installations**: Uses actual `pip install` commands with specific package versions
2. **Cross-environment comparison**: Compares hash results between Ubuntu 20.04, 24.04, and Alpine
3. **Docker-based testing**: Creates isolated environments for reliable testing

## Files

- `test_cross_environment_hash.py` - Main test suite
- `run_cross_env_tests.sh` - Automated test runner
- `Dockerfile.test-ubuntu{20,24}` - Docker environments for Ubuntu testing
- `Dockerfile.test-alpine` - Alpine Docker environment for testing

## Running Tests

### Quick Test

```bash
./tests/run_cross_env_tests.sh
```

### Manual Test

```bash
source venv/bin/activate
TEST_DOCKER=1 python -m pytest test_cross_environment_hash.py -v -s
```

## Test Packages

The test uses lightweight packages for fast execution:

- `six==1.16.0` - Python 2/3 compatibility library
- `urllib3==1.26.18` - HTTP library

## Expected Result

✅ **Test passes**: Same packages produce identical hashes across Ubuntu 20.04, 24.04, and Alpine
❌ **Test fails**: Hash function behavior differs between environments

## Prerequisites

- Docker installed and running
- Python virtual environment activated
- `pytest` and `docker` Python packages installed
