#!/bin/bash

# Detector Benchmark Runner for Energy Dependency Inspector
# Generated during performance optimization analysis
#
# This script runs detector-specific performance benchmarks and generates flame graphs
# for analysis of the Energy Dependency Inspector application.

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
PROFILES_DIR="$SCRIPT_DIR/profiles"
TIMING_DIR="$SCRIPT_DIR/timing-results"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_header() {
    echo -e "${BLUE}================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}================================${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

# Check prerequisites
check_prerequisites() {
    print_header "Checking Prerequisites"

    # Check if py-spy is installed
    if ! command -v py-spy &> /dev/null; then
        print_error "py-spy is not installed. Installing..."
        pip install py-spy
    else
        print_success "py-spy is available"
    fi

    # Check if Docker is running
    if ! docker info &> /dev/null; then
        print_error "Docker is not running. Please start Docker and try again."
        exit 1
    else
        print_success "Docker is running"
    fi

    # Check virtual environment
    if [[ "$VIRTUAL_ENV" == "" ]]; then
        print_warning "Virtual environment not activated. Activating..."
        source "$PROJECT_ROOT/venv/bin/activate"
    else
        print_success "Virtual environment is active"
    fi

    # Ensure profiles directory exists
    mkdir -p "$PROFILES_DIR"
    print_success "Profiles directory ready: $PROFILES_DIR"
}

# Show usage information
show_usage() {
    echo "Usage: $0 [OPTIONS] [DETECTOR_TYPE]"
    echo ""
    echo "DETECTOR_TYPE:"
    echo "  all          Run all detectors (default)"
    echo "  host         Run only host detector"
    echo "  npm          Run only NPM detector"
    echo "  pip          Run only PIP detector"
    echo ""
    echo "OPTIONS:"
    echo "  -h, --help     Show this help message"
    echo "  --clean        Clean existing profiles before running"
    echo "  --skip-os-packages    Skip os packages checks"
    echo "  --skip-hash-collection Skip hash collection for faster execution"
    echo "  --profiling    Enable detailed profiling (slower, for analysis)"
    echo "  --interface TYPE       Interface type: 'cli' or 'programmatic' (default: cli)"
    echo "  --scenario TYPE        Specific scenario: varies by detector type"
    echo "  --select-detectors LIST Comma-separated list of detectors to use (e.g., 'pip,dpkg')"
    echo ""
    echo "Specific scenario types by detector:"
    echo "  host:  skip-system, full-system, all (default: all)"
    echo "  npm:   small, large, mixed, all (default: all)"
    echo "  pip:   small, large, mixed, all (default: all)"
    echo ""
    echo "Examples:"
    echo "  $0                        # Run all detectors with timing only"
    echo "  $0 host                   # Run only host detector"
    echo "  $0 --profiling npm        # Run NPM detector with profiling"
    echo "  $0 pip                    # Run PIP detector"
    echo "  $0 --clean --profiling    # Clean and run all detectors with profiling"
    echo "  $0 --skip-hash-collection # Run all detectors without hash collection"
    echo "  $0 --interface programmatic host  # Run host detector with programmatic interface"
    echo "  $0 --scenario small npm  # Run only small NPM scenario"
    echo "  $0 --scenario skip-system host  # Run only skip-system host scenario"
    echo "  $0 --select-detectors 'pip,dpkg' host  # Run host detector with only pip and dpkg"
}

# Parse command line arguments
DETECTOR_TYPE="all"
SPECIFIC_SCENARIO="all"
CLEAN_PROFILES=false
SKIP_OS_PACKAGES_CHECK=false
SKIP_HASH_COLLECTION=false
ENABLE_PROFILING=false
INTERFACE="cli"
SELECT_DETECTORS=""

while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_usage
            exit 0
            ;;
        --clean)
            CLEAN_PROFILES=true
            shift
            ;;
        --skip-os-packages)
            SKIP_OS_PACKAGES_CHECK=true
            shift
            ;;
        --skip-hash-collection)
            SKIP_HASH_COLLECTION=true
            shift
            ;;
        --profiling)
            ENABLE_PROFILING=true
            shift
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
        --scenario)
            if [[ -n $2 ]]; then
                SPECIFIC_SCENARIO="$2"
                shift 2
            else
                print_error "--scenario requires a scenario type"
                show_usage
                exit 1
            fi
            ;;
        --select-detectors)
            if [[ -n $2 ]]; then
                SELECT_DETECTORS="$2"
                shift 2
            else
                print_error "--select-detectors requires a comma-separated list of detectors"
                show_usage
                exit 1
            fi
            ;;
        all|host|npm|pip)
            DETECTOR_TYPE="$1"
            shift
            ;;
        *)
            print_error "Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
done

# Generate session ID for this benchmark run
SESSION_ID=$(date +%Y-%m-%d_%H-%M-%S)

# Export variables for child scripts
export ENABLE_PROFILING
export SKIP_HASH_COLLECTION
export SESSION_ID
export SELECT_DETECTORS

# Function to display enhanced results with current vs historical separation
display_enhanced_results() {
    local detector_type="$1"
    local specific_scenario="$2"

    # Check if any timing files exist
    local has_files=false
    for file in "$TIMING_DIR/host_timing_results.csv" "$TIMING_DIR/npm_timing_results.csv" "$TIMING_DIR/pip_timing_results.csv"; do
        if [[ -f "$file" ]]; then
            has_files=true
            break
        fi
    done

    if [[ "$has_files" == false ]]; then
        echo "No results files found."
        return
    fi

    # Extract current session results from all files
    local current_results=""
    for file in "$TIMING_DIR/host_timing_results.csv" "$TIMING_DIR/npm_timing_results.csv" "$TIMING_DIR/pip_timing_results.csv"; do
        if [[ -f "$file" ]]; then
            local session_results=$(grep "^$SESSION_ID," "$file" 2>/dev/null)
            if [[ -n "$session_results" ]]; then
                if [[ -z "$current_results" ]]; then
                    current_results="$session_results"
                else
                    current_results="$current_results"$'\n'"$session_results"
                fi
            fi
        fi
    done

    # Extract and filter historical results from all files
    local all_historical=""
    for file in "$TIMING_DIR/host_timing_results.csv" "$TIMING_DIR/npm_timing_results.csv" "$TIMING_DIR/pip_timing_results.csv"; do
        if [[ -f "$file" ]]; then
            local hist_results=$(grep -v "^$SESSION_ID," "$file" | tail -n +2 2>/dev/null)
            if [[ -n "$hist_results" ]]; then
                if [[ -z "$all_historical" ]]; then
                    all_historical="$hist_results"
                else
                    all_historical="$all_historical"$'\n'"$hist_results"
                fi
            fi
        fi
    done
    local historical_results=""

    if [[ -n "$all_historical" ]]; then
        # Create scenario patterns based on benchmark context
        local scenario_patterns=()

        case "$detector_type" in
            "host")
                case "$specific_scenario" in
                    "skip-system")
                        scenario_patterns+=("Host Skip System")
                        ;;
                    "full-system")
                        scenario_patterns+=("Host Full System")
                        ;;
                    "all")
                        scenario_patterns+=("Host Skip System" "Host Full System")
                        ;;
                esac
                ;;
            "npm")
                case "$specific_scenario" in
                    "small")
                        scenario_patterns+=("NPM small")
                        ;;
                    "large")
                        scenario_patterns+=("NPM large")
                        ;;
                    "mixed")
                        scenario_patterns+=("NPM Mixed")
                        ;;
                    "all")
                        scenario_patterns+=("NPM small" "NPM large" "NPM Mixed")
                        ;;
                esac
                ;;
            "pip")
                case "$specific_scenario" in
                    "small")
                        scenario_patterns+=("PIP small")
                        ;;
                    "large")
                        scenario_patterns+=("PIP large")
                        ;;
                    "mixed")
                        scenario_patterns+=("PIP Mixed")
                        ;;
                    "all")
                        scenario_patterns+=("PIP small" "PIP large" "PIP Mixed")
                        ;;
                esac
                ;;
            "all")
                # When running all benchmarks, show all historical results
                historical_results="$all_historical"
                ;;
        esac

        # Filter historical results based on patterns (if not "all" detector type)
        if [[ "$detector_type" != "all" && ${#scenario_patterns[@]} -gt 0 ]]; then
            for pattern in "${scenario_patterns[@]}"; do
                local matches=$(echo "$all_historical" | grep "$pattern" 2>/dev/null)
                if [[ -n "$matches" ]]; then
                    if [[ -z "$historical_results" ]]; then
                        historical_results="$matches"
                    else
                        historical_results="$historical_results"$'\n'"$matches"
                    fi
                fi
            done
        fi
    fi

    echo ""
    if [[ -n "$current_results" ]]; then
        print_header "CURRENT RUN RESULTS (Session: $SESSION_ID)"
        echo "Session_ID,Scenario,Time(s),Packages,Timestamp,CPU_Cores,Memory_GB,Docker_Version,Python_Version" > /tmp/current_results.csv
        echo "$current_results" >> /tmp/current_results.csv
        # Display with star markers for current results - properly handle scenario names with spaces
        awk -F',' 'NR==1 {print "Scenario,Time(s),Packages,Timestamp"} NR>1 {print "★ "$2","$3","$4","$5}' /tmp/current_results.csv | column -t -s ','
        rm -f /tmp/current_results.csv
        echo ""
    fi

    if [[ -n "$historical_results" ]]; then
        # Create descriptive header based on filter context
        local filter_description=""
        if [[ "$detector_type" == "all" ]]; then
            filter_description="ALL DETECTORS"
        else
            case "$specific_scenario" in
                "all")
                    filter_description="$(echo "$detector_type" | tr '[:lower:]' '[:upper:]') DETECTOR"
                    ;;
                *)
                    case "$detector_type" in
                        "host")
                            if [[ "$specific_scenario" == "skip-system" ]]; then
                                filter_description="HOST SKIP-SYSTEM SCENARIOS"
                            else
                                filter_description="HOST FULL-SYSTEM SCENARIOS"
                            fi
                            ;;
                        "npm"|"pip")
                            filter_description="$(echo "$detector_type" | tr '[:lower:]' '[:upper:]') $(echo "$specific_scenario" | tr '[:lower:]' '[:upper:]') SCENARIOS"
                            ;;
                    esac
                    ;;
            esac
        fi

        print_header "HISTORICAL RESULTS ($filter_description)"
        echo "Session_ID,Scenario,Time(s),Packages,Timestamp,CPU_Cores,Memory_GB,Docker_Version,Python_Version" > /tmp/historical_results.csv
        echo "$historical_results" >> /tmp/historical_results.csv
        # Display historical results with session info - properly handle scenario names with spaces
        awk -F',' 'NR==1 {print "Session,Scenario,Time(s),Packages,Timestamp"} NR>1 {print $1","$2","$3","$4","$5}' /tmp/historical_results.csv | column -t -s ','
        rm -f /tmp/historical_results.csv
        echo ""
    fi

    if [[ -z "$current_results" && -z "$historical_results" ]]; then
        echo "No benchmark results found."
    fi
}

# Clean profiles if requested
if [[ "$CLEAN_PROFILES" == true ]]; then
    print_header "Cleaning Existing Profiles"
    rm -f "$PROFILES_DIR"/*.svg "$PROFILES_DIR"/*.json
    print_success "Existing profiles cleaned"
fi

# Main execution
main() {
    print_header "Energy Dependency Inspector Performance Benchmarks"
    echo "Session ID: $SESSION_ID"
    echo "Detector type: $DETECTOR_TYPE"
    echo "Specific scenario: $SPECIFIC_SCENARIO"
    echo "Interface: $INTERFACE"
    echo "Selected detectors: ${SELECT_DETECTORS:-all}"
    echo "Profiles directory: $PROFILES_DIR"
    echo "Profiling enabled: ${ENABLE_PROFILING}"
    echo ""

    if [[ "$SKIP_OS_PACKAGES_CHECK" == false ]]; then
        check_prerequisites
    fi

    case $DETECTOR_TYPE in
        "all")
            print_header "Running All Benchmarks"
            "$SCRIPT_DIR/detectors/host-benchmarks.sh" --interface "$INTERFACE" --scenario "$SPECIFIC_SCENARIO"
            "$SCRIPT_DIR/detectors/npm-benchmarks.sh" --interface "$INTERFACE" --scenario "$SPECIFIC_SCENARIO"
            "$SCRIPT_DIR/detectors/pip-benchmarks.sh" --interface "$INTERFACE" --scenario "$SPECIFIC_SCENARIO"
            ;;
        "host")
            print_header "Running Host Benchmarks"
            "$SCRIPT_DIR/detectors/host-benchmarks.sh" --interface "$INTERFACE" --scenario "$SPECIFIC_SCENARIO"
            ;;
        "npm")
            print_header "Running NPM Benchmarks"
            "$SCRIPT_DIR/detectors/npm-benchmarks.sh" --interface "$INTERFACE" --scenario "$SPECIFIC_SCENARIO"
            ;;
        "pip")
            print_header "Running PIP Benchmarks"
            "$SCRIPT_DIR/detectors/pip-benchmarks.sh" --interface "$INTERFACE" --scenario "$SPECIFIC_SCENARIO"
            ;;
    esac

    # Ensure timing directory exists
    mkdir -p "$TIMING_DIR"

    # Display results with current vs historical separation
    display_enhanced_results "$DETECTOR_TYPE" "$SPECIFIC_SCENARIO"

    if [[ "$ENABLE_PROFILING" == true ]]; then
        local svg_count=$(ls "$PROFILES_DIR"/*.svg 2>/dev/null | wc -l)
        local json_count=$(ls "$PROFILES_DIR"/*.json 2>/dev/null | wc -l)
        echo "Total profiles generated: $((svg_count + json_count)) (SVG: $svg_count, JSON: $json_count)"
        echo "Profiles location: $PROFILES_DIR"
        echo ""
        echo "To view profiles:"
        echo "  - Upload .json files to https://www.speedscope.app/ for interactive analysis"
        echo "  - Open .svg files in a web browser: file://$PROFILES_DIR/[profile_name].svg"
    fi

    print_success "All benchmarks completed successfully!"
}

# Run main function
main
