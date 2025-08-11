# DPKG Detector Tests

Tests for the DPKG detector using Docker Ubuntu Linux containers.

## Overview

This test suite validates the DPKG detector's ability to:

- Detect system packages in Ubuntu Linux containers
- Parse package versions and architecture information
- Extract package hashes from dpkg md5sums files when available
- Handle both minimal and extended Ubuntu installations

## Test Cases

**Combined Ubuntu Container Test**: Tests DPKG detection in Ubuntu 22.04 container with:

1. Base Ubuntu packages (minimal installation)
2. Additional packages installed during test (curl, vim, wget, tree)

## Running Tests

```bash
# Run DPKG detector tests
pytest tests/dpkg_detector/ -v

# Run with verbose resolver output
pytest tests/dpkg_detector/ -v -s --verbose-resolver
```

## Requirements

- Docker must be available and running
- Python docker package installed
- DPKG detector implementation in `detectors/dpkg_detector.py`

## Expected Behavior

The tests verify that:

- DPKG packages are detected with proper version and architecture information
- System scope is correctly identified
- Common Ubuntu packages (base-files, libc6, bash, coreutils) are found
- Package hashes are extracted when md5sums files are available
- Additional installed packages and their dependencies are detected when present
