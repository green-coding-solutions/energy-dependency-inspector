# Programmatic API Guide

The dependency-resolver can be used as a Python library in other projects. This guide covers all programmatic usage patterns.

## Quick Start

```python
import dependency_resolver

# Simple host system analysis
deps_json = dependency_resolver.resolve_host_dependencies()

# Docker container analysis
docker_deps = dependency_resolver.resolve_docker_dependencies("nginx")
```

## Convenience Functions

### Host System Analysis

```python
import dependency_resolver

# Get JSON string output
deps_json = dependency_resolver.resolve_host_dependencies()

# Get Python dictionary for further processing
deps_dict = dependency_resolver.resolve_dependencies_as_dict(
    environment_type="host",
    skip_system_scope=True,
    skip_hash_collection=True  # Skip hash collection for improved performance
)
```

### Docker Container Analysis

```python
import dependency_resolver

# Analyze Docker container - returns JSON string
docker_deps = dependency_resolver.resolve_docker_dependencies(
    container_identifier="nginx",
    working_dir="/app"
)

# Analyze Docker container - returns Python dictionary
docker_dict = dependency_resolver.resolve_docker_dependencies_as_dict(
    container_identifier="nginx",
    working_dir="/app",
    skip_system_scope=False,
    skip_hash_collection=False  # Include hashes in output
)
```

## Available Functions

- `resolve_host_dependencies()` - Analyze host system, returns JSON string
- `resolve_docker_dependencies()` - Analyze Docker container, returns JSON string
- `resolve_docker_dependencies_as_dict()` - Analyze Docker container, returns Python dictionary
- `resolve_dependencies_as_dict()` - Generic analysis, returns Python dictionary

## Advanced Usage with Core Classes

For more control over the dependency resolution process, use the core classes directly:

```python
from dependency_resolver import Orchestrator, HostExecutor, DockerExecutor, OutputFormatter

# Host system analysis with custom settings
executor = HostExecutor()
orchestrator = Orchestrator(
    debug=True,
    skip_system_scope=True,
    skip_hash_collection=True,
    selected_detectors="pip,npm"  # Only analyze Python and Node.js dependencies
)
dependencies = orchestrator.resolve_dependencies(executor)

# Format output
formatter = OutputFormatter()
json_output = formatter.format_json(dependencies, pretty_print=True)
```

### Docker Analysis with Core Classes

```python
from dependency_resolver import Orchestrator, DockerExecutor, OutputFormatter

# Docker container analysis
container_id = "nginx"
executor = DockerExecutor(container_id)
orchestrator = Orchestrator(
    debug=False,
    skip_system_scope=False,
    skip_hash_collection=False,
    selected_detectors="dpkg,docker-info"  # Analyze system packages and container info only
)

dependencies = orchestrator.resolve_dependencies(executor, working_dir="/app")

# Format and process results
formatter = OutputFormatter()
json_output = formatter.format_json(dependencies, pretty_print=True)

# Or work with raw dictionary
for scope, result in dependencies.items():
    if scope in ["project", "system"] and "packages" in result:
        print(f"Scope: {scope}")
        print(f"Found {len(result['packages'])} packages")
        # Access package manager metadata
        for manager, metadata in result.items():
            if manager != "packages":
                print(f"  {manager}: {metadata.get('location', 'system-wide')}")
```

## Available Classes

- `Orchestrator` - Main dependency resolution coordinator
- `HostExecutor` - Execute commands on host system
- `DockerExecutor` - Execute commands in Docker containers
- `OutputFormatter` - JSON formatting utilities

## Configuration Options

### Orchestrator Options

```python
orchestrator = Orchestrator(
    debug=True,                    # Enable debug output
    skip_system_scope=False,       # Skip system-wide package managers
    venv_path="/path/to/venv",     # Specify Python virtual environment path
    skip_hash_collection=False,    # Skip hash collection for improved performance
    selected_detectors="pip,npm"   # Use only specific detectors
)
```

### Detector Selection

Control which package managers are analyzed by specifying the `selected_detectors` parameter:

```python
from dependency_resolver import Orchestrator, HostExecutor

# Use only Python pip detector
orchestrator = Orchestrator(selected_detectors="pip")

# Use multiple specific detectors
orchestrator = Orchestrator(selected_detectors="pip,npm,maven")

# Use all detectors (default behavior)
orchestrator = Orchestrator(selected_detectors=None)
```

**Available detectors:** `pip`, `npm`, `dpkg`, `apk`, `maven`, `docker-info`

### Executor Options

```python
# Host executor (no additional options)
host_executor = HostExecutor()

# Docker executor
docker_executor = DockerExecutor(
    container_identifier="container_name_or_id"
)
```

### Output Formatter Options

```python
formatter = OutputFormatter()

# Format with pretty printing
json_output = formatter.format_json(dependencies, pretty_print=True)

# Format as compact JSON
json_output = formatter.format_json(dependencies, pretty_print=False)
```

## Error Handling

```python
import dependency_resolver

try:
    deps = dependency_resolver.resolve_host_dependencies()
    # Process dependencies
except Exception as e:
    print(f"Error resolving dependencies: {e}")
```

## Integration Examples

### Build System Integration

```python
import dependency_resolver
import json
import hashlib
from pathlib import Path

class DependencyTracker:
    """Track dependency changes across builds for cache invalidation."""

    def __init__(self, cache_dir="./build-cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)

    def get_dependency_fingerprint(self, working_dir=None):
        """Generate fingerprint of current dependencies for build caching."""
        try:
            deps = dependency_resolver.resolve_dependencies_as_dict(
                environment_type="host",
                working_dir=working_dir,
                skip_system_scope=True,      # Focus on project dependencies
                skip_hash_collection=True    # Skip hashes for faster fingerprinting
            )

            # Create stable fingerprint from dependency versions
            fingerprint_data = {}
            for scope, result in deps.items():
                if scope in ["project", "system"] and "packages" in result:
                    fingerprint_data[scope] = {
                        pkg["name"]: pkg.get("version", "")
                        for pkg in result["packages"]
                    }

            fingerprint_json = json.dumps(fingerprint_data, sort_keys=True)
            return hashlib.sha256(fingerprint_json.encode()).hexdigest()

        except Exception as e:
            print(f"Warning: Could not generate dependency fingerprint: {e}")
            return None

    def should_rebuild(self, target_name, working_dir=None):
        """Check if target should be rebuilt based on dependency changes."""
        current_fingerprint = self.get_dependency_fingerprint(working_dir)
        if not current_fingerprint:
            return True  # Rebuild if we can't determine dependencies

        cache_file = self.cache_dir / f"{target_name}.deps"
        if not cache_file.exists():
            # Save current fingerprint and indicate rebuild needed
            cache_file.write_text(current_fingerprint)
            return True

        cached_fingerprint = cache_file.read_text().strip()
        if cached_fingerprint != current_fingerprint:
            cache_file.write_text(current_fingerprint)
            return True

        return False

# Usage in build script
if __name__ == "__main__":
    tracker = DependencyTracker()

    if tracker.should_rebuild("my-application", working_dir="./src"):
        print("Dependencies changed, rebuilding...")
        # Run build commands
    else:
        print("Dependencies unchanged, using cached build")
```

### CI/CD Pipeline Integration

```python
import dependency_resolver
import json
import os

def generate_dependency_report():
    """Generate dependency report for CI/CD pipeline."""

    # Analyze current environment
    deps = dependency_resolver.resolve_dependencies_as_dict("host")

    # Save to file for artifact storage
    with open("dependency-report.json", "w") as f:
        json.dump(deps, f, indent=2)

    # Log summary
    total_packages = 0
    for scope, result in deps.items():
        if scope in ["project", "system"] and "packages" in result:
            count = len(result["packages"])
            print(f"{scope}: {count} packages")
            total_packages += count
            # Log package managers in this scope
            managers = [key for key in result.keys() if key != "packages"]
            if managers:
                print(f"  Package managers: {', '.join(managers)}")

    print(f"Total packages detected: {total_packages}")
    return deps

if __name__ == "__main__":
    generate_dependency_report()
```
