#!/bin/bash

# Sequential vs Parallel Execution Benchmarks for Energy Dependency Inspector
# Compares performance of running Energy Dependency Inspector multiple times

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
PROFILES_DIR="$SCRIPT_DIR/profiles"
TIMING_DIR="$SCRIPT_DIR/timing-results"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
# YELLOW='\033[1;33m'  # Reserved for future warning messages
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_header() {
    echo -e "${BLUE}=== $1 ===${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_timing() {
    echo -e "${GREEN}⏱  Execution time: $1${NC}"
}

# Check prerequisites
check_prerequisites() {
    print_header "Checking Prerequisites"

    # Check if Docker is running
    if ! docker info &> /dev/null; then
        print_error "Docker is not running. Please start Docker and try again."
        exit 1
    else
        print_success "Docker is running"
    fi

    # Check virtual environment
    if [[ "$VIRTUAL_ENV" == "" ]]; then
        echo "Activating virtual environment..."
        source "$PROJECT_ROOT/venv/bin/activate"
    else
        print_success "Virtual environment is active"
    fi

    # Create Python container with pip packages for testing
    echo "Setting up test container with Python/pip packages..."
    docker run -d --name parallel-bench-test python:3.9-slim sh -c "pip install requests numpy flask && sleep 300" || true
    sleep 5  # Wait for container to be ready
    print_success "Test container ready"

    # Ensure directories exist
    mkdir -p "$PROFILES_DIR"
    mkdir -p "$TIMING_DIR"
}

# Cleanup function
cleanup() {
    echo "Cleaning up test container..."
    docker stop parallel-bench-test >/dev/null 2>&1 || true
    docker rm parallel-bench-test >/dev/null 2>&1 || true
}

# Set trap for cleanup on exit
trap cleanup EXIT

# Main execution
main() {
    print_header "Sequential vs Parallel Execution Benchmark"

    check_prerequisites

    # Initialize results file with header if it doesn't exist
    local results_file="$TIMING_DIR/parallel_execution_results.csv"
    if [[ ! -f "$results_file" ]]; then
        printf "Timestamp,Execution_Mode,Total_Time(s),Iterations,Workers,CPU_Cores,Memory_GB,Docker_Version,Python_Version\n" > "$results_file"
    fi

    # Run the Python benchmark script
    python3 "$SCRIPT_DIR/parallel_execution_benchmark.py" "$results_file" "$MAX_WORKERS" "$INTERFACE" "$ITERATIONS"

    # Display results
    print_header "Benchmark Results"
    echo ""
    echo "Results:"
    column -t -s ',' "$results_file"

    echo ""
    echo "Results saved to: $results_file"


    print_success "Benchmark completed successfully!"
}

# Show usage information
show_usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "OPTIONS:"
    echo "  -h, --help                 Show this help message"
    echo "  --workers N                Number of parallel workers (default: 4)"
    echo "  --interface TYPE           Interface type: 'cli' or 'programmatic' (default: cli)"
    echo "  --iterations N             Number of benchmark runs (default: 10)"
    echo ""
    echo "This benchmark compares sequential vs parallel execution of the Energy Dependency Inspector"
    echo "by running it multiple times against a Docker container with Python/pip packages."
    echo ""
    echo "Interface types:"
    echo "  cli          - Use command line interface (subprocess calls)"
    echo "  programmatic - Use Python library interface (direct function calls)"
}

# Parse command line arguments
MAX_WORKERS=4
INTERFACE="cli"
ITERATIONS=10

while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_usage
            exit 0
            ;;
        --workers)
            if [[ -n $2 && $2 =~ ^[1-9][0-9]*$ ]]; then
                MAX_WORKERS="$2"
                shift 2
            else
                print_error "--workers requires a positive integer"
                show_usage
                exit 1
            fi
            ;;
        --interface)
            if [[ -n $2 && ($2 == "cli" || $2 == "programmatic") ]]; then
                INTERFACE="$2"
                shift 2
            else
                print_error "--interface requires 'cli' or 'programmatic'"
                show_usage
                exit 1
            fi
            ;;
        --iterations)
            if [[ -n $2 && $2 =~ ^[1-9][0-9]*$ ]]; then
                ITERATIONS="$2"
                shift 2
            else
                print_error "--iterations requires a positive integer"
                show_usage
                exit 1
            fi
            ;;
        *)
            print_error "Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
done

# Run main function
main
