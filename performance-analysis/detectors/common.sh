#!/bin/bash

# Common functions and variables for detector benchmark scripts
# This file should be sourced by detector-specific benchmark scripts

# Execution guard - prevent direct execution of common.sh
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    echo "Error: common.sh should not be executed directly."
    echo "It should be sourced by detector benchmark scripts."
    exit 1
fi

# Path configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PERF_ANALYSIS_DIR="$(dirname "$SCRIPT_DIR")"
PROJECT_ROOT="$(dirname "$PERF_ANALYSIS_DIR")"
PROFILES_DIR="$PERF_ANALYSIS_DIR/profiles"
TIMING_DIR="$PERF_ANALYSIS_DIR/timing-results"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print utility functions
print_header() {
    echo -e "${BLUE}=== $1 ===${NC}"
}

print_timing() {
    echo -e "${GREEN}⏱  Execution time: $1${NC}"
}

print_packages() {
    echo -e "${YELLOW}📦 Package count: $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

# Parse arguments passed from detector-benchmarks.sh
parse_detector_args() {
    export INTERFACE="cli"
    export SCENARIO_TYPE="all"

    while [[ $# -gt 0 ]]; do
        case $1 in
            --interface)
                export INTERFACE="$2"
                shift 2
                ;;
            --scenario)
                export SCENARIO_TYPE="$2"
                shift 2
                ;;
            *)
                shift
                ;;
        esac
    done
}

# Initialize session and environment
initialize_detector_environment() {
    # Generate session ID if not already set
    if [[ -z "$SESSION_ID" ]]; then
        SESSION_ID=$(date +%Y-%m-%d_%H-%M-%S)
    fi

    # Activate virtual environment if not already active
    if [[ "$VIRTUAL_ENV" == "" ]]; then
        echo "Activating virtual environment..."
        source "$PROJECT_ROOT/venv/bin/activate"
    fi

    # Create necessary directories
    mkdir -p "$PROFILES_DIR"
    mkdir -p "$TIMING_DIR"
}

# Initialize CSV results file with headers
initialize_csv_file() {
    local csv_file="$1"

    if [[ ! -f "$csv_file" ]]; then
        echo "Session_ID,Scenario,Time(s),Packages,Timestamp,CPU_Cores,Memory_GB,Docker_Version,Python_Version" > "$csv_file"
    fi
}

# Get system information for CSV storage
get_system_info_csv() {
    python3 -c "
import sys
sys.path.append('$PERF_ANALYSIS_DIR')
from system_info import get_system_info, format_system_info_for_csv
info = get_system_info()
print(format_system_info_for_csv(info))
"
}

# Validate and store benchmark results with error checking
store_benchmark_results() {
    local session_id="$1"
    local scenario="$2"
    local runtime="$3"
    local package_count="$4"
    local csv_file="$5"

    # Validate results before collecting system info
    if (( $(echo "$runtime < 0" | bc -l) )); then
        print_error "Negative timing result ($runtime). Skipping CSV write."
        return 1
    elif [ "$package_count" -eq 0 ]; then
        print_error "Zero packages detected ($package_count). Skipping CSV write."
        return 1
    else
        # Get system information
        local system_info
        system_info=$(get_system_info_csv)

        # Store results with system information
        echo "$session_id,$scenario,$runtime,$package_count,$system_info" >> "$csv_file"
        return 0
    fi
}

# Core benchmarking function with timing and optional profiling
benchmark_scenario() {
    local scenario="$1"
    local command="$2"
    local csv_file="$3"

    print_header "$scenario"

    # Direct timing measurement
    echo "Measuring execution time..."
    start_time=$(date +%s.%N)
    result=$(eval "$command")
    end_time=$(date +%s.%N)
    runtime=$(echo "$end_time - $start_time" | bc -l)

    # Count packages from output (detector-specific logic will override this)
    package_count=0
    if echo "$result" | jq . >/dev/null 2>&1; then
        package_count=$(echo "$result" | jq '[.[] | .dependencies | keys] | add | length' 2>/dev/null || echo "0")
    fi

    print_timing "${runtime}s"
    print_packages "$package_count packages"

    # Get system information
    local system_info
    system_info=$(get_system_info_csv)

    # Store results for reporting with system information
    echo "$SESSION_ID,$scenario,$runtime,$package_count,$system_info" >> "$csv_file"

    echo ""

    # Return values for caller to use
    echo "$runtime|$package_count|$result"
}

# Run profiling analysis with py-spy
run_profiling_analysis() {
    local profile_name="$1"
    local command="$2"
    local duration="${3:-30}"

    if [[ "${ENABLE_PROFILING:-false}" == "true" ]]; then
        echo "Running profiling analysis..."
        if py-spy record -o "$PROFILES_DIR/${profile_name}.json" -d "$duration" -f speedscope -- \
            bash -c "$command" >/dev/null 2>&1; then
            echo "Profile saved: $PROFILES_DIR/${profile_name}.json"
        else
            local exit_code=$?
            echo "Warning: py-spy profiling failed with exit code $exit_code. Continuing..."
        fi
    fi
}

# Clean up Docker containers with error handling
cleanup_container() {
    local container_name="$1"

    echo "Cleaning up container: $container_name"
    docker stop "$container_name" >/dev/null 2>&1 || true
    docker rm "$container_name" >/dev/null 2>&1 || true
}

# Wait for Docker container to be ready
wait_for_container_ready() {
    local container_name="$1"
    local max_attempts="${2:-30}"
    local attempt=0

    echo "Waiting for container $container_name to be ready..."

    while [ $attempt -lt "$max_attempts" ]; do
        if docker exec "$container_name" echo "ready" >/dev/null 2>&1; then
            echo "Container $container_name is ready"
            return 0
        fi
        sleep 2
        attempt=$((attempt + 1))
    done

    echo "ERROR: Container $container_name failed to become ready after ${max_attempts} attempts"
    return 1
}

# Generic Docker dependency resolution measurement
measure_docker_dependency_resolution() {
    local container_name="$1"
    local interface="$2"

    echo "Measuring execution time..." >&2
    start_time=$(date +%s.%N)

    if [[ "$interface" == "cli" ]]; then
        result=$(cd "$PROJECT_ROOT" && python3 -m energy_dependency_inspector docker "$container_name")
    else
        # Programmatic interface
        result=$(cd "$PROJECT_ROOT" && python3 -c "import energy_dependency_inspector; print(energy_dependency_inspector.resolve_docker_dependencies('$container_name'))")
    fi

    end_time=$(date +%s.%N)
    runtime=$(echo "$end_time - $start_time" | bc -l)

    echo "$runtime|$result"
}



# Parse package counts from JSON output for different package managers
parse_package_counts() {
    local result="$1"
    local package_managers="$2"  # Space-separated list like "npm dpkg"

    local total_count=0

    if echo "$result" | jq . >/dev/null 2>&1; then
        for manager in $package_managers; do
            local count
            count=$(echo "$result" | jq ".${manager}.dependencies | keys | length" 2>/dev/null || echo "0")
            total_count=$((total_count + count))
        done
    fi

    echo "$total_count"
}

# Create and wait for Docker container with custom wait condition
create_and_wait_container() {
    local container_name="$1"
    local docker_command="$2"
    local wait_function="$3"  # Function name to call for waiting
    local wait_args="$4"      # Arguments for wait function

    echo "Creating container: $container_name"
    eval "$docker_command"

    echo "Waiting for container setup to complete..."
    if ! "$wait_function" "$container_name" "$wait_args"; then
        echo "ERROR: Container setup failed"
        cleanup_container "$container_name"
        return 1
    fi

    return 0
}

# Generic Docker benchmark execution with timing and profiling
run_docker_benchmark() {
    local scenario_name="$1"
    local container_name="$2"
    local interface="$3"
    local csv_file="$4"
    local profile_name="$5"
    local profile_duration="${6:-30}"
    local package_managers="$7"  # Space-separated list like "npm dpkg"

    print_header "$scenario_name"

    # Prepare hash collection flag
    local hash_flag=""
    local hash_arg=""
    if [[ "${SKIP_HASH_COLLECTION:-false}" == "true" ]]; then
        hash_flag="--skip-hash-collection"
        hash_arg=", skip_hash_collection=True"
        echo "Hash collection disabled for faster execution"
    fi

    # Prepare select detectors flag
    local select_flag=""
    local select_arg=""
    if [[ -n "${SELECT_DETECTORS:-}" ]]; then
        select_flag="--select-detectors '$SELECT_DETECTORS'"
        select_arg=", selected_detectors='$SELECT_DETECTORS'"
        echo "Using selected detectors: $SELECT_DETECTORS"
    fi

    echo "Measuring execution time..."
    start_time=$(date +%s.%N)

    local cmd_result=0
    if [[ "$interface" == "cli" ]]; then
        local cmd="cd '$PROJECT_ROOT' && python3 -m energy_dependency_inspector docker '$container_name'"
        [[ -n "$hash_flag" ]] && cmd="$cmd $hash_flag"
        [[ -n "$select_flag" ]] && cmd="$cmd $select_flag"
        result=$(eval "$cmd") || cmd_result=$?
    else
        result=$(cd "$PROJECT_ROOT" && python3 -c "import energy_dependency_inspector; print(energy_dependency_inspector.resolve_docker_dependencies('$container_name'$hash_arg$select_arg))") || cmd_result=$?
    fi

    end_time=$(date +%s.%N)

    if [ $cmd_result -ne 0 ]; then
        print_error "Command execution failed with exit code $cmd_result"
        echo "$scenario_name failed"
        return $cmd_result
    fi

    runtime=$(echo "$end_time - $start_time" | bc -l)

    # Count packages using the parse function
    local package_count
    package_count=$(parse_package_counts "$result" "$package_managers")

    print_timing "${runtime}s"
    print_packages "$package_count packages"

    # Store results
    store_benchmark_results "$SESSION_ID" "$scenario_name ($interface)" "$runtime" "$package_count" "$csv_file"

    # Optional profiling
    if [[ -n "$profile_name" ]]; then
        run_profiling_analysis "$profile_name" "cd '$PROJECT_ROOT' && python3 -m energy_dependency_inspector docker '$container_name' $hash_flag" "$profile_duration"
    fi

    echo "$scenario_name completed"
}

# Export functions and variables for use by detector scripts
export -f print_header print_timing print_packages print_error print_success print_warning
export -f parse_detector_args initialize_detector_environment initialize_csv_file
export -f get_system_info_csv store_benchmark_results benchmark_scenario run_profiling_analysis
export -f cleanup_container wait_for_container_ready
export -f measure_docker_dependency_resolution parse_package_counts create_and_wait_container run_docker_benchmark
