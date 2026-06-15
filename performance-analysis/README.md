# Performance Analysis

This directory contains performance analysis documentation, benchmark scripts, and profiling results for the Energy Dependency Inspector application.

## Prerequisites

The performance analysis tools require additional dependencies:

```bash
# From the project root directory:
pip install .[performance-analysis]

# Or from this performance-analysis directory:
pip install ..[performance-analysis]
```

## Quick Start

```bash
# Run all detectors (default CLI interface)
./detector-benchmarks.sh

# Run specific detector type
./detector-benchmarks.sh host
./detector-benchmarks.sh npm
./detector-benchmarks.sh pip

# Run specific scenarios
./detector-benchmarks.sh --scenario skip-system host
./detector-benchmarks.sh --scenario small npm
./detector-benchmarks.sh --scenario mixed pip

# Run with programmatic interface
./detector-benchmarks.sh --interface programmatic
./detector-benchmarks.sh --interface programmatic host

# Combine options for targeted analysis
./detector-benchmarks.sh --scenario large --interface programmatic npm

# Run with profiling enabled
./detector-benchmarks.sh --profiling

# Run sequential vs parallel execution benchmark
./parallel-execution-benchmarks.sh

# Test different interfaces for parallel execution comparison
./parallel-execution-benchmarks.sh --interface programmatic
```

## Analysis Documents

- `performance-optimization-analysis.md` - Comprehensive performance analysis and optimization recommendations
- `docker-performance-comparison.md` - Docker environment performance comparison
- `dpkg-batch-optimization-benchmark.md` - DPKG batch optimization benchmarks

## Benchmark Scripts

### `detector-benchmarks.sh`

Main detector benchmark orchestrator with the following features:

- Prerequisites checking (py-spy, Docker, virtual environment)
- Selective detector execution (host, npm, pip, or all)
- Specific scenario selection (small, large, mixed, etc.)
- Interface selection (CLI or programmatic)
- Session-based result tracking with enhanced display
- Filtered historical results (shows only relevant scenario history)
- Profile cleanup options
- Colored output and progress indicators
- System information collection and CSV result appending

**Options:**

- `--interface TYPE`: Interface type - 'cli' or 'programmatic' (default: cli)
- `--scenario TYPE`: Specific scenario type - varies by detector (default: all)
- `--profiling`: Enable detailed profiling (slower, for analysis)
- `--clean`: Clean existing profiles before running
- `--skip-system-check`: Skip system dependency checks

**Specific scenario types by detector:**

- **host**: `skip-system`, `full-system`, `all` (default: all)
- **npm**: `small`, `large`, `mixed`, `all` (default: all)
- **pip**: `small`, `large`, `mixed`, `all` (default: all)

**Examples:**

```bash
# Run all detectors with default CLI interface
./detector-benchmarks.sh

# Run host detector with programmatic interface
./detector-benchmarks.sh --interface programmatic host

# Run specific scenario types
./detector-benchmarks.sh --scenario skip-system host
./detector-benchmarks.sh --scenario small npm
./detector-benchmarks.sh --scenario mixed pip

# Run all detectors with profiling enabled
./detector-benchmarks.sh --clean --profiling

# Combine options for targeted analysis
./detector-benchmarks.sh --scenario large --interface programmatic npm
```

### Detector-Specific Scripts

The detector-specific benchmark scripts are located in the `detectors/` subdirectory and should **not** be executed directly. They are automatically called by `detector-benchmarks.sh` with the appropriate parameters.

#### `detectors/host-benchmarks.sh`

Profiles dependency resolution on the host system with interface selection support:

- Skip OS Packages (fast, ~40 packages)
- Full system scan (slow, ~2700 packages)
- CLI and programmatic interface support
- System information collection (CPU, memory, versions)
- CSV result appending for historical tracking

#### `detectors/pip-benchmarks.sh`

Profiles Python dependency resolution with different package scales and interface support:

- Small Python package sets (3 packages)
- Large Python package sets (25+ packages)
- Mixed environment (Python + Debian system packages via DPKG)
- CLI and programmatic interface support
- System information collection and CSV result appending

#### `detectors/npm-benchmarks.sh`

Specialized NPM profiling with different scenarios and interface support:

- Small package count (3 packages)
- Large package count (20 packages)
- Mixed environment (NPM + Debian system packages via DPKG)
- CLI and programmatic interface support
- System information collection and CSV result appending

**Note:** These detector scripts use a common library (`detectors/common.sh`) that provides shared functionality including color definitions, print utilities, argument parsing, environment initialization, CSV management, benchmarking functions, and container management. This eliminates code duplication and ensures consistent behavior across all detectors.

### `parallel-execution-benchmarks.sh`

Compares sequential vs parallel execution performance with support for both CLI and programmatic interfaces:

- Sequential: Energy Dependency Inspector runs executed one after another
- Parallel: Energy Dependency Inspector runs executed concurrently using ThreadPoolExecutor
- Tests against Docker container with Python/pip packages
- Measures total execution time and calculates speedup/improvement
- Supports both CLI interface (subprocess calls) and programmatic interface (direct Python function calls)

**Options:**

- `--workers N`: Number of parallel workers (default: 4)
- `--interface TYPE`: Interface type - 'cli' or 'programmatic' (default: cli)
- `--iterations N`: Number of benchmark runs (default: 10)

**Examples:**

```bash
# Default CLI interface with 4 workers
./parallel-execution-benchmarks.sh

# Test programmatic interface with 2 workers
./parallel-execution-benchmarks.sh --workers 2 --interface programmatic

# Run quick test with fewer iterations
./parallel-execution-benchmarks.sh --iterations 5

# Compare interfaces with custom iterations
./parallel-execution-benchmarks.sh --interface cli --iterations 15
./parallel-execution-benchmarks.sh --interface programmatic --iterations 15
```

## Results and Data

### Profiling Results

All profiling results are saved to `profiles/` directory:

- **Speedscope files** (`.json`): Interactive flame graphs that can be viewed at <https://www.speedscope.app/>
- **Legacy SVG files** (`.svg`): Static flame graphs that can be opened in any web browser

Upload the `.json` files to <https://www.speedscope.app/> for the best interactive profiling experience with features like call tree navigation, flamegraph zoom, and timeline views.

### Timing Results

All benchmark timing results are saved to `timing-results/` directory with comprehensive system information:

- **Individual CSV files**: `host_timing_results.csv`, `npm_timing_results.csv`, `pip_timing_results.csv`
- **System information**: Each result includes timestamp, CPU cores, memory, Docker version, Python version
- **Historical tracking**: Results are appended rather than overwritten for trend analysis

**CSV Format:**

```csv
Scenario,Time(s),Packages,Timestamp,CPU_Cores,Memory_GB,Docker_Version,Python_Version
Host Full System (cli),45.23,2847,2024-01-15 14:30:22,8,16.0,24.0.6,3.11.2
```

## Generated During

These scripts and analysis were created during the performance optimization analysis to identify bottlenecks and optimization opportunities in the Energy Dependency Inspector application.
