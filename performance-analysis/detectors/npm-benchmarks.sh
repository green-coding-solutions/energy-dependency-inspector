#!/bin/bash

# NPM-Specific Performance Benchmarks for Energy Dependency Inspector
# Generated during performance optimization analysis
# This script should only be called from detector-benchmarks.sh

set -e

# Execution guard - prevent direct execution unless called by detector-benchmarks.sh
if [[ "${BASH_SOURCE[0]}" == "${0}" && -z "$SESSION_ID" ]]; then
    echo "Error: This script should not be executed directly."
    echo "Please use detector-benchmarks.sh to run benchmarks."
    exit 1
fi

# Source common functions and variables
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"

# Efficient waiting functions
wait_for_npm_install() {
    local container_name="$1"
    local expected_min_packages="$2"  # Minimum expected package count
    local max_attempts=120  # Increased timeout for npm installs
    local attempt=0

    while [ $attempt -lt $max_attempts ]; do
        # Check if npm install process is still running
        if ! docker exec "$container_name" pgrep npm >/dev/null 2>&1; then
            # Process finished, now check if installation was successful
            local npm_count
            npm_count=$(docker exec "$container_name" npm list --depth=0 2>/dev/null | grep -c "^[[:space:]]*[^[:space:]].*--" || echo "0")
            npm_count=$(echo "$npm_count" | tr -d '\n\r ' | sed 's/[^0-9]//g')
            npm_count=${npm_count:-0}
            # Ensure it's a valid number
            if ! [[ "$npm_count" =~ ^[0-9]+$ ]]; then
                npm_count=0
            fi
            if [ "$npm_count" -ge "$expected_min_packages" ]; then
                echo "NPM install completed successfully ($npm_count packages installed)"
                return 0
            else
                echo "ERROR: NPM install failed - only $npm_count packages found, expected at least $expected_min_packages"
                return 1
            fi
        fi
        sleep 2
        attempt=$((attempt + 1))
    done

    echo "ERROR: NPM install timed out after ${max_attempts} attempts"
    return 1
}

wait_for_container_ready() {
    local container_name="$1"
    local package_to_check="$2"
    local max_attempts=90
    local attempt=0

    echo "Waiting for container setup to complete..."
    while [ $attempt -lt $max_attempts ]; do
        # Check if the package is installed globally
        if docker exec "$container_name" npm list -g "$package_to_check" >/dev/null 2>&1; then
            echo "Container setup completed"
            return 0
        fi
        sleep 2
        attempt=$((attempt + 1))
    done

    echo "ERROR: Container setup failed after ${max_attempts} attempts"
    return 1
}

# Parse arguments using common function
parse_detector_args "$@"

# Initialize detector environment using common function
initialize_detector_environment

echo "Starting NPM-specific performance scenarios..."
echo "Interface: $INTERFACE"
echo "Scenario: $SCENARIO_TYPE"
echo "Profiles will be saved to: $PROFILES_DIR"

# Initialize CSV file using common function
initialize_csv_file "$TIMING_DIR/npm_timing_results.csv"

# Cleanup function for NPM containers
cleanup_npm_container() {
    local container_name="$1"
    local temp_dir="$2"

    docker stop "$container_name" || true
    docker rm "$container_name" || true
    sudo rm -rf "$temp_dir"
}

# Function to create and profile NPM containers with different package counts
create_npm_container() {
    local package_count="$1"
    local container_name="npm_benchmark_$package_count"
    local profile_name="npm_${package_count}_packages"

    print_header "NPM Benchmark: $package_count packages"

    # Create temporary package.json with specified number of packages
    local temp_dir
    temp_dir=$(mktemp -d)
    cat > "$temp_dir/package.json" << EOF
{
  "name": "npm-benchmark-$package_count",
  "version": "1.0.0",
  "dependencies": {
EOF

    # Add packages based on count
    if [[ "$package_count" == "small" ]]; then
        cat >> "$temp_dir/package.json" << EOF
    "lodash": "^4.17.21",
    "express": "^4.18.0",
    "axios": "^1.6.0"
EOF
    elif [[ "$package_count" == "large" ]]; then
        cat >> "$temp_dir/package.json" << EOF
    "lodash": "^4.17.21",
    "express": "^4.18.0",
    "axios": "^1.6.0",
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "webpack": "^5.88.0",
    "webpack-cli": "^5.1.0",
    "typescript": "^5.0.0",
    "eslint": "^8.45.0",
    "prettier": "^3.0.0",
    "jest": "^29.6.0",
    "babel-core": "^6.26.3",
    "@types/node": "^20.0.0",
    "@types/react": "^18.2.0",
    "sass": "^1.64.0",
    "postcss": "^8.4.0",
    "autoprefixer": "^10.4.0",
    "tailwindcss": "^3.3.0",
    "vite": "^4.4.0",
    "vitest": "^0.34.0"
EOF
    fi

    cat >> "$temp_dir/package.json" << EOF
  }
}
EOF

    # Create and run container
    echo "Creating container with $package_count packages..."
    docker run -d --name "$container_name" \
        -v "$temp_dir:/app" \
        -w /app \
        node:18-alpine \
        sh -c "npm install && tail -f /dev/null"

    # Wait for npm install to complete
    echo "Waiting for npm install to complete..."
    local expected_min_packages=3  # Base expectation
    if [[ "$package_count" == "small" ]]; then
        expected_min_packages=3   # 3 direct packages
    elif [[ "$package_count" == "large" ]]; then
        expected_min_packages=20  # 20 direct packages
    fi

    if ! wait_for_npm_install "$container_name" "$expected_min_packages"; then
        echo "ERROR: NPM installation failed for $package_count packages"
        cleanup_npm_container "$container_name" "$temp_dir"
        return 1
    fi

    # Use common benchmark function for timing and profiling
    # Ensure cleanup happens regardless of success/failure
    local benchmark_result=0
    run_docker_benchmark "NPM $package_count" "$container_name" "$INTERFACE" "$TIMING_DIR/npm_timing_results.csv" "$profile_name" 30 "npm" || benchmark_result=$?

    # Cleanup (always executed)
    cleanup_npm_container "$container_name" "$temp_dir"

    if [ $benchmark_result -eq 0 ]; then
        echo "NPM benchmark for $package_count packages completed"
    else
        echo "NPM benchmark for $package_count packages completed with errors"
    fi

    return $benchmark_result
}

# Mixed environment benchmark function to eliminate duplication
run_mixed_environment_benchmark() {
    print_header "Mixed Environment Benchmarks - Debian Linux + NPM"

    local container_name="npm_mixed_env"
    local docker_cmd="docker run -d --name $container_name node:18 sh -c \"apt-get update && apt-get install -y curl wget git && npm install -g express lodash axios && tail -f /dev/null\""

    # Create and wait for container
    if ! create_and_wait_container "$container_name" "$docker_cmd" "wait_for_container_ready" "express"; then
        return 1
    fi

    # Run benchmark using common function with error handling
    local benchmark_result=0
    run_docker_benchmark "NPM Mixed (Debian + NPM)" "$container_name" "$INTERFACE" "$TIMING_DIR/npm_timing_results.csv" "npm_mixed_environment" 45 "npm dpkg" || benchmark_result=$?

    # Cleanup (always executed)
    cleanup_container "$container_name"

    return $benchmark_result
}

# Run selected NPM benchmarks
case $SCENARIO_TYPE in
    "small")
        create_npm_container "small"
        ;;
    "large")
        create_npm_container "large"
        ;;
    "mixed")
        run_mixed_environment_benchmark
        ;;
    "all")
        create_npm_container "small"
        create_npm_container "large"
        run_mixed_environment_benchmark
        ;;
esac
