#!/bin/bash

# Host Performance Benchmarks for Energy Dependency Inspector
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

# Host-specific benchmark function using common benchmarking
host_benchmark_scenario() {
    local scenario="$1"
    local command="$2"
    local profile_duration="${3:-30}"

    # Use common benchmark function
    benchmark_scenario "$scenario" "$command" "$TIMING_DIR/host_timing_results.csv" >/dev/null

    # Optional profiling specific to host scenarios
    if [[ "${ENABLE_PROFILING:-false}" == "true" ]]; then
        local profile_name=$(echo "$scenario" | tr ' ' '_' | tr '[:upper:]' '[:lower:]')
        run_profiling_analysis "$profile_name" "$command" "$profile_duration"
    fi
}

# Parse arguments using common function
parse_detector_args "$@"

# Initialize detector environment using common function
initialize_detector_environment

echo "Starting host performance scenarios..."
echo "Interface: $INTERFACE"
echo "Scenario: $SCENARIO_TYPE"
echo "Profiles will be saved to: $PROFILES_DIR"

# Initialize CSV file using common function
initialize_csv_file "$TIMING_DIR/host_timing_results.csv"

# Prepare hash collection flag
HASH_FLAG=""
HASH_ARG=""
if [[ "${SKIP_HASH_COLLECTION:-false}" == "true" ]]; then
    HASH_FLAG="--skip-hash-collection"
    HASH_ARG=", skip_hash_collection=True"
    echo "Hash collection disabled for faster execution"
fi

# Prepare select detectors flag
SELECT_FLAG=""
SELECT_ARG=""
if [[ -n "${SELECT_DETECTORS:-}" ]]; then
    SELECT_FLAG="--select-detectors '$SELECT_DETECTORS'"
    SELECT_ARG=", selected_detectors='$SELECT_DETECTORS'"
    echo "Using selected detectors: $SELECT_DETECTORS"
fi

# Run selected scenarios based on scenario type and interface
case $SCENARIO_TYPE in
    "skip-system")
        if [[ "$INTERFACE" == "cli" ]]; then
            cmd="cd '$PROJECT_ROOT' && python3 -m energy_dependency_inspector host --skip-os-packages"
            [[ -n "$HASH_FLAG" ]] && cmd="$cmd $HASH_FLAG"
            [[ -n "$SELECT_FLAG" ]] && cmd="$cmd $SELECT_FLAG"
            host_benchmark_scenario "Host Skip OS Packages ($INTERFACE)" \
                "$cmd" \
                30
        else
            host_benchmark_scenario "Host Skip OS Packages ($INTERFACE)" \
                "cd '$PROJECT_ROOT' && python3 -c 'import energy_dependency_inspector; print(energy_dependency_inspector.resolve_host_dependencies(skip_os_packages=True$HASH_ARG$SELECT_ARG))'" \
                30
        fi
        ;;
    "full-system")
        if [[ "$INTERFACE" == "cli" ]]; then
            cmd="cd '$PROJECT_ROOT' && python3 -m energy_dependency_inspector host"
            [[ -n "$HASH_FLAG" ]] && cmd="$cmd $HASH_FLAG"
            [[ -n "$SELECT_FLAG" ]] && cmd="$cmd $SELECT_FLAG"
            host_benchmark_scenario "Host Full System ($INTERFACE)" \
                "$cmd" \
                60
        else
            host_benchmark_scenario "Host Full System ($INTERFACE)" \
                "cd '$PROJECT_ROOT' && python3 -c 'import energy_dependency_inspector; print(energy_dependency_inspector.resolve_host_dependencies($HASH_ARG$SELECT_ARG))'" \
                60
        fi
        ;;
    "all")
        if [[ "$INTERFACE" == "cli" ]]; then
            cmd1="cd '$PROJECT_ROOT' && python3 -m energy_dependency_inspector host --skip-os-packages"
            [[ -n "$HASH_FLAG" ]] && cmd1="$cmd1 $HASH_FLAG"
            [[ -n "$SELECT_FLAG" ]] && cmd1="$cmd1 $SELECT_FLAG"
            host_benchmark_scenario "Host Skip OS Packages ($INTERFACE)" \
                "$cmd1" \
                30

            cmd2="cd '$PROJECT_ROOT' && python3 -m energy_dependency_inspector host"
            [[ -n "$HASH_FLAG" ]] && cmd2="$cmd2 $HASH_FLAG"
            [[ -n "$SELECT_FLAG" ]] && cmd2="$cmd2 $SELECT_FLAG"
            host_benchmark_scenario "Host Full System ($INTERFACE)" \
                "$cmd2" \
                60
        else
            # Programmatic interface
            host_benchmark_scenario "Host Skip OS Packages ($INTERFACE)" \
                "cd '$PROJECT_ROOT' && python3 -c 'import energy_dependency_inspector; print(energy_dependency_inspector.resolve_host_dependencies(skip_os_packages=True$HASH_ARG$SELECT_ARG))'" \
                30

            host_benchmark_scenario "Host Full System ($INTERFACE)" \
                "cd '$PROJECT_ROOT' && python3 -c 'import energy_dependency_inspector; print(energy_dependency_inspector.resolve_host_dependencies($HASH_ARG$SELECT_ARG))'" \
                60
        fi
        ;;
esac
