# APK Detector Tests

Tests for the APK detector using Docker Alpine Linux containers.

## Overview

This test suite validates the APK detector's ability to:

- Detect system packages in Alpine Linux containers
- Parse package versions and architecture information
- Handle both minimal and extended Alpine installations

## Test Cases

**Combined Alpine Container Test**: Tests APK detection in Alpine 3.18 container with:

1. Base Alpine packages (minimal installation)
2. Additional packages installed during test (curl, git, bash, nano)

## Running Tests

```bash
# Run APK detector tests
pytest tests/detectors/apk/ -v

# Run with verbose resolver output
pytest tests/detectors/apk/ -v -s --verbose-resolver
```

## Requirements

- Docker must be available and running
- Python docker package installed
- APK detector implementation in `detectors/apk_detector.py`

## Expected Behavior

The tests verify that:

- APK packages are detected with proper version and architecture information
- System scope is correctly identified
- Common Alpine packages (musl, busybox, alpine-baselayout) are found
- Additional installed packages are detected when present
