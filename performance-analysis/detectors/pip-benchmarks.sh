#!/bin/bash

# PIP-Specific Performance Benchmarks for Energy Dependency Inspector
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


# Run mixed environment benchmark (Python + Debian packages)
run_mixed_environment_benchmark() {
    local interface="$1"
    local csv_file="$2"

    print_header "Mixed Environment Benchmark - Debian Linux + PIP"

    local container_name="pip_mixed_env"
    local docker_cmd="docker run -d --name $container_name python:3.11 sh -c \"apt-get update && apt-get install -y curl wget git build-essential sqlite3 && pip install requests flask pandas numpy && tail -f /dev/null\""

    # Create and wait for container
    if ! create_and_wait_container "$container_name" "$docker_cmd" "wait_for_mixed_env_ready" "requests"; then
        return 1
    fi

    # Run benchmark using common function with error handling
    local benchmark_result=0
    run_docker_benchmark "PIP Mixed (Debian + PIP)" "$container_name" "$interface" "$csv_file" "pip_mixed_environment" 45 "pip dpkg" || benchmark_result=$?

    # Cleanup (always executed)
    cleanup_container "$container_name"

    return $benchmark_result
}

# Wait for mixed environment to be ready
wait_for_mixed_env_ready() {
    local container_name="$1"
    local package_to_check="$2"
    local max_attempts=120
    local attempt=0

    echo "Waiting for mixed environment setup to complete..."
    while [ $attempt -lt $max_attempts ]; do
        # Check if pip package is installed and apt update/install is done
        if docker exec "$container_name" python -c "import $package_to_check" >/dev/null 2>&1 && \
           docker exec "$container_name" which curl >/dev/null 2>&1; then
            echo "Mixed environment setup completed"
            return 0
        fi
        sleep 2
        attempt=$((attempt + 1))
    done

    echo "Warning: Mixed environment may not be fully ready after ${max_attempts} attempts"
}

# Wait for pip install to complete
wait_for_pip_install() {
    local container_name="$1"
    local expected_min_packages="$2"

    echo "Waiting for pip install to complete..."

    # Wait fixed time for pip install (small=30s, large=60s)
    local wait_time=30
    if [ "$expected_min_packages" -gt 20 ]; then
        wait_time=60
    fi
    sleep "$wait_time"

    # Check final package count
    local pip_count
    pip_count=$(docker exec "$container_name" pip list --format=freeze 2>/dev/null | wc -l || echo "0")
    if [ "$pip_count" -ge "$expected_min_packages" ]; then
        echo "PIP install completed successfully ($pip_count packages installed)"
        return 0
    else
        echo "ERROR: PIP install failed - only $pip_count packages found, expected at least $expected_min_packages"
        return 1
    fi
}

# Parse arguments using common function
parse_detector_args "$@"

# Initialize detector environment using common function
initialize_detector_environment

echo "Starting PIP-specific performance scenarios..."
# shellcheck disable=SC2153
echo "Interface: $INTERFACE"
echo "Scenario: $SCENARIO_TYPE"
echo "Profiles will be saved to: $PROFILES_DIR"

# Initialize CSV file using common function
initialize_csv_file "$TIMING_DIR/pip_timing_results.csv"

# Function to create and profile Python containers with different package counts
create_pip_container() {
    local package_type="$1"
    local container_name="pip_benchmark_$package_type"
    local profile_name="pip_${package_type}_packages"

    print_header "PIP Benchmark: $package_type packages"

    # Create temporary requirements.txt with specified packages
    local temp_dir
    temp_dir=$(mktemp -d)
    local requirements_file="$temp_dir/requirements.txt"

    # Add packages based on type
    if [[ "$package_type" == "small" ]]; then
        cat > "$requirements_file" << EOF
requests==2.31.0
click==8.1.6
pyyaml==6.0.1
EOF
    elif [[ "$package_type" == "large" ]]; then
        cat > "$requirements_file" << EOF
# Data science stack
pandas==2.0.3
numpy==1.24.3
scipy==1.11.1
matplotlib==3.7.2
scikit-learn==1.3.0

# Web frameworks
django==4.2.4
flask==2.3.2
fastapi==0.101.1
requests==2.31.0

# Development tools
pytest==7.4.0
black==23.7.0
flake8==6.0.0
mypy==1.5.1

# Async and networking
aiohttp==3.8.5
celery==5.3.1
redis==4.6.0

# Utilities
click==8.1.6
pyyaml==6.0.1
jinja2==3.1.2
sqlalchemy==2.0.19

# Additional packages
boto3==1.28.25
cryptography==41.0.3
pillow==10.0.0
EOF
    fi

    # Create and run container
    echo "Creating container with $package_type packages..."
    docker run -d --name "$container_name" \
        -v "$temp_dir:/workspace" \
        python:3.11-slim \
        sh -c "cd /workspace && pip install -r requirements.txt; tail -f /dev/null"

    # Wait for pip install to complete
    local expected_min_packages=5  # Base expectation
    if [[ "$package_type" == "small" ]]; then
        expected_min_packages=10  # 3 direct packages + dependencies (typically ~10 total)
    elif [[ "$package_type" == "large" ]]; then
        expected_min_packages=50  # 23 direct packages + many dependencies
    fi

    if ! wait_for_pip_install "$container_name" "$expected_min_packages"; then
        echo "ERROR: PIP installation failed for $package_type packages"
        docker stop "$container_name" || true
        docker rm "$container_name" || true
        rm -rf "$temp_dir"
        return 1
    fi

    # Use common benchmark function for timing and profiling
    local profile_duration=30
    if [[ "$package_type" == "large" ]]; then
        profile_duration=60
    fi

    # Ensure cleanup happens regardless of success/failure
    local benchmark_result=0
    run_docker_benchmark "PIP $package_type" "$container_name" "$INTERFACE" "$TIMING_DIR/pip_timing_results.csv" "$profile_name" "$profile_duration" "pip" || benchmark_result=$?

    # Cleanup (always execute)
    cleanup_container "$container_name"
    rm -rf "$temp_dir"

    if [ $benchmark_result -eq 0 ]; then
        echo "PIP benchmark for $package_type packages completed"
    else
        echo "PIP benchmark for $package_type packages completed with errors"
    fi
    echo ""

    return $benchmark_result
}

# Run selected PIP benchmarks
case $SCENARIO_TYPE in
    "small")
        create_pip_container "small"
        ;;
    "large")
        create_pip_container "large"
        ;;
    "mixed")
        run_mixed_environment_benchmark "$INTERFACE" "$TIMING_DIR/pip_timing_results.csv"
        ;;
    "all")
        create_pip_container "small"
        create_pip_container "large"
        run_mixed_environment_benchmark "$INTERFACE" "$TIMING_DIR/pip_timing_results.csv"
        ;;
esac
