#!/bin/bash

# Build container and verify psutils is detected in /root/venv/ by dependency_resolver

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DOCKERFILE_PATH="$SCRIPT_DIR"
DEPENDENCY_RESOLVER_PATH="$SCRIPT_DIR/../../.."
CONTAINER_NAME="test-pip-root-venv-detection-$(date +%s)"

echo "Building Docker image from $DOCKERFILE_PATH..."
docker build -t "$CONTAINER_NAME" -f "$DOCKERFILE_PATH/Dockerfile" "$DOCKERFILE_PATH"

echo "Starting container..."
docker run --rm -d --name "$CONTAINER_NAME" "$CONTAINER_NAME"

echo "Running dependency_resolver on container $CONTAINER_NAME..."
cd "$DEPENDENCY_RESOLVER_PATH"
source venv/bin/activate

echo "Checking for psutils in output..."
if python3 -m dependency_resolver docker "$CONTAINER_NAME" | grep -q "psutils"; then
    echo "✓ psutils found in dependency output"
else
    echo "✗ psutils NOT found in dependency output"
fi

echo "Cleaning up..."
docker stop "$CONTAINER_NAME"
docker rmi "$CONTAINER_NAME"

echo "Test complete!"
