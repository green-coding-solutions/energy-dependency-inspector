#!/bin/bash

# Script to run cross-environment hash comparison tests

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

set -e

echo "Running cross-environment hash comparison tests for _generate_location_hash"
echo "This will install packages on host and in Docker containers and compare hashes across environments"

# Check if Docker is available
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not available. Please install Docker to run cross-environment tests."
    exit 1
fi

# Function to cleanup containers
cleanup() {
    echo "Cleaning up test containers..."
    docker rm -f pip-hash-cross-env-test-ubuntu20 2>/dev/null || true
    docker rm -f pip-hash-cross-env-test-ubuntu24 2>/dev/null || true
    docker rm -f pip-hash-cross-env-test-alpine 2>/dev/null || true
}

# Cleanup on exit
trap cleanup EXIT

echo -e "\\n🔄 Building Docker images for cross-environment testing..."

# Build Docker images with Python 3.9
echo "Building pip-hash-cross-env-test-ubuntu20..."
docker build -t pip-hash-cross-env-test-ubuntu20 -f "$SCRIPT_DIR/Dockerfile.test-ubuntu20" "$SCRIPT_DIR"

echo "Building pip-hash-cross-env-test-ubuntu24..."
docker build -t pip-hash-cross-env-test-ubuntu24 -f "$SCRIPT_DIR/Dockerfile.test-ubuntu24" "$SCRIPT_DIR"

echo "Building pip-hash-cross-env-test-alpine..."
docker build -t pip-hash-cross-env-test-alpine -f "$SCRIPT_DIR/Dockerfile.test-alpine" "$SCRIPT_DIR"

echo -e "\\n🔄 Starting cross-environment comparison tests..."
cd "$SCRIPT_DIR/../.."
source venv/bin/activate

python -m pytest "$SCRIPT_DIR/test_cross_environment_hash.py::TestCrossEnvironmentHash::test_cross_environment_hash_comparison" -v -s

echo -e "\\n✅ Cross-environment tests completed successfully!"
echo "Result: Hash function produces consistent results across host and Ubuntu 20.04, 24.04, and Alpine containers"
