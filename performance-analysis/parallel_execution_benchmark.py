#!/usr/bin/env python3
"""
Sequential vs Parallel Execution Benchmark

Compares performance of running Energy Dependency Inspector multiple times:
- Sequential: 10 runs one after another
- Parallel: 10 runs using ThreadPoolExecutor (max_workers=4)
"""

import sys
import time
import subprocess
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Tuple

# Import system info utilities
from system_info import get_system_info

# Add project root to Python path for programmatic interface
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    import energy_dependency_inspector

    ENERGY_DEPENDENCY_INSPECTOR_AVAILABLE = True
except ImportError:
    ENERGY_DEPENDENCY_INSPECTOR_AVAILABLE = False


def run_energy_dependency_inspector_cli() -> bool:
    """Execute Energy Dependency Inspector for the test container using CLI."""
    project_root = Path(__file__).parent.parent
    cmd = ["python3", "-m", "energy_dependency_inspector", "docker", "parallel-bench-test"]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=project_root, timeout=60, check=False)
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        print("Warning: Energy Dependency Inspector execution timed out", file=sys.stderr)
        return False
    except (OSError, ValueError) as e:
        print(f"Error running Energy Dependency Inspector: {e}", file=sys.stderr)
        return False


def run_energy_dependency_inspector_programmatic() -> bool:
    """Execute Energy Dependency Inspector for the test container using programmatic interface."""
    if not ENERGY_DEPENDENCY_INSPECTOR_AVAILABLE:
        print("Error: energy_dependency_inspector module not available for programmatic interface", file=sys.stderr)
        return False

    try:
        # Use programmatic interface as shown in README.md
        result = energy_dependency_inspector.resolve_docker_dependencies(container_identifier="parallel-bench-test")
        # Consider it successful if we get a non-empty result
        return bool(result and len(result) > 10)  # Basic validation that we got JSON output
    except (RuntimeError, ValueError, ImportError, AttributeError) as e:
        print(f"Error running Energy Dependency Inspector programmatically: {e}", file=sys.stderr)
        return False


def benchmark_sequential(iterations: int = 10, use_programmatic: bool = False) -> Tuple[float, int]:
    """Run Energy Dependency Inspector sequentially multiple times."""
    interface_type = "programmatic" if use_programmatic else "CLI"
    runner_func = (
        run_energy_dependency_inspector_programmatic if use_programmatic else run_energy_dependency_inspector_cli
    )

    print(f"Running {iterations} sequential executions using {interface_type} interface...")

    start_time = time.time()
    successful_runs = 0

    for i in range(iterations):
        print(f"  Sequential run {i+1}/{iterations}")
        if runner_func():
            successful_runs += 1

    end_time = time.time()
    total_time = end_time - start_time

    print(f"Sequential execution completed: {successful_runs}/{iterations} successful")
    print(f"Total time: {total_time:.2f}s")

    return total_time, successful_runs


def benchmark_parallel(iterations: int = 10, max_workers: int = 4, use_programmatic: bool = False) -> Tuple[float, int]:
    """Run Energy Dependency Inspector in parallel using ThreadPoolExecutor."""
    interface_type = "programmatic" if use_programmatic else "CLI"
    runner_func = (
        run_energy_dependency_inspector_programmatic if use_programmatic else run_energy_dependency_inspector_cli
    )

    print(f"Running {iterations} parallel executions using {interface_type} interface (max_workers={max_workers})...")

    start_time = time.time()

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        futures = [executor.submit(runner_func) for _ in range(iterations)]

        # Wait for all tasks to complete and count successful runs
        successful_runs = 0
        for i, future in enumerate(futures):
            print(f"  Parallel run {i+1}/{iterations} completed")
            if future.result():
                successful_runs += 1

    end_time = time.time()
    total_time = end_time - start_time

    print(f"Parallel execution completed: {successful_runs}/{iterations} successful")
    print(f"Total time: {total_time:.2f}s")

    return total_time, successful_runs


def main() -> None:
    """Main benchmark execution."""
    if len(sys.argv) < 2 or len(sys.argv) > 5:
        print("Usage: python3 parallel_execution_benchmark.py <results_file> [max_workers] [interface] [iterations]")
        print("  interface: 'cli' (default) or 'programmatic'")
        print("  iterations: number of benchmark runs (default: 10)")
        sys.exit(1)

    results_file = sys.argv[1]
    max_workers = int(sys.argv[2]) if len(sys.argv) >= 3 else 4
    interface = sys.argv[3] if len(sys.argv) >= 4 else "cli"
    iterations = int(sys.argv[4]) if len(sys.argv) >= 5 else 10

    # Get system information
    system_info = get_system_info()

    if interface not in ["cli", "programmatic"]:
        print("Error: interface must be 'cli' or 'programmatic'")
        sys.exit(1)

    if iterations < 1:
        print("Error: iterations must be a positive integer")
        sys.exit(1)

    use_programmatic = interface == "programmatic"

    if use_programmatic and not ENERGY_DEPENDENCY_INSPECTOR_AVAILABLE:
        print("Error: energy_dependency_inspector module not available for programmatic interface")
        print("Make sure the energy_dependency_inspector package is installed and accessible")
        sys.exit(1)

    print("=" * 60)
    print("Sequential vs Parallel Execution Benchmark")
    print("=" * 60)
    print("Test container: parallel-bench-test")
    print(f"Interface: {interface}")
    print(f"Iterations: {iterations}")
    print(f"Parallel workers: {max_workers}")
    print("")

    # Run sequential benchmark
    print("🔄 SEQUENTIAL BENCHMARK")
    print("-" * 30)
    seq_time, seq_success = benchmark_sequential(iterations, use_programmatic=use_programmatic)

    print("")

    # Run parallel benchmark
    print("⚡ PARALLEL BENCHMARK")
    print("-" * 30)
    par_time, par_success = benchmark_parallel(iterations, max_workers=max_workers, use_programmatic=use_programmatic)

    print("")
    print("📊 RESULTS SUMMARY")
    print("-" * 30)
    print(f"Sequential: {seq_time:.2f}s ({seq_success}/{iterations} successful)")
    print(f"Parallel:   {par_time:.2f}s ({par_success}/{iterations} successful)")

    if seq_time > 0:
        speedup = seq_time / par_time
        print(f"Speedup:    {speedup:.2f}x")

        if speedup > 1:
            improvement = ((seq_time - par_time) / seq_time) * 100
            print(f"Improvement: {improvement:.1f}% faster")
        else:
            degradation = ((par_time - seq_time) / seq_time) * 100
            print(f"Degradation: {degradation:.1f}% slower")

    # Save results to CSV only if runs were successful
    if seq_success > 0 and par_success > 0:
        with open(results_file, "a", encoding="utf-8") as f:
            # Write sequential results with system info
            f.write(
                f"{system_info['timestamp']},Sequential-{interface},{seq_time:.2f},{iterations},1,{system_info['cpu_cores']},{system_info['memory_gb']},{system_info['docker_version']},{system_info['python_version']}\n"
            )
            # Write parallel results with system info
            f.write(
                f"{system_info['timestamp']},Parallel-{interface},{par_time:.2f},{iterations},{max_workers},{system_info['cpu_cores']},{system_info['memory_gb']},{system_info['docker_version']},{system_info['python_version']}\n"
            )
        print(f"\nResults appended to: {results_file}")
    else:
        print(
            f"\nResults NOT saved - insufficient successful runs (Sequential: {seq_success}/{iterations}, Parallel: {par_success}/{iterations})"
        )


if __name__ == "__main__":
    main()
