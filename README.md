# dependency-resolver

A tool for creating snapshots of installed packages on specified target environments. The project provides both a command-line interface and a Python library for programmatic use.
Its main focus is dependency resolving of Docker containers, but it also supports host systems and Docker Compose stacks.
The output is a structured JSON that includes information about all the installed packages from supported sources with their version and unique hash values.

## Installation

```bash
# Clone and install
git clone https://github.com/green-coding-solutions/dependency-resolver
cd dependency-resolver
pip install .
```

## Usage

The dependency-resolver can be used in two ways:

1. **Command Line Interface (CLI)** - For direct terminal usage
2. **Programmatic Interface** - As a Python library in other projects

### Command Line Interface

```bash
# Analyze host system (default behavior)
python3 -m dependency_resolver

# Explicitly specify host environment
python3 -m dependency_resolver host

# Analyze Docker container by name
python3 -m dependency_resolver docker nginx

# Analyze Docker container by ID
python3 -m dependency_resolver docker a1b2c3d4e5f6

# Get only container metadata (skip dependency detection)
python3 -m dependency_resolver docker nginx --only-container-info

# Analyze Docker Compose stack
python3 -m dependency_resolver docker_compose my_app

# Enable debug output
python3 -m dependency_resolver --debug

# Set working directory
python3 -m dependency_resolver --working-dir /path/to/project

# Skip system scope package managers
python3 -m dependency_resolver --skip-system-scope

# Pretty print JSON output
python3 -m dependency_resolver --pretty-print
```

### Programmatic Interface

The dependency-resolver can be used as a Python library in other projects with both functional and class-based interfaces:

#### Functional Interface (Simple Usage)

```python
import dependency_resolver

# Simple host system analysis
deps_json = dependency_resolver.resolve_host_dependencies()

# Get results as Python dictionary for further processing
deps_dict = dependency_resolver.resolve_dependencies_as_dict(
    environment_type="host",
    skip_system_scope=True
)

# Docker container analysis
docker_deps = dependency_resolver.resolve_docker_dependencies(
    container_identifier="nginx",
    working_dir="/app"
)
```

#### Class-Based Interface (Advanced Usage)

For complex scenarios, especially when analyzing multiple environments in parallel:

```python
from dependency_resolver import DependencyResolver, ResolveRequest

# Create resolver with shared configuration
resolver = DependencyResolver(
    debug=True,
    skip_system_scope=False,
    max_workers=4  # Parallel processing
)

# Single environment analysis
result = resolver.resolve(
    environment_type="docker",
    environment_identifier="nginx"
)

# Parallel multi-environment analysis
requests = [
    ResolveRequest("docker", "container1"),
    ResolveRequest("docker", "container2"),
    ResolveRequest("host", working_dir="/path/to/project", venv_path="/opt/venv"),
    ResolveRequest("docker_compose", "my-stack")
]

def progress_callback(completed, total, result):
    print(f"Progress: {completed}/{total} - {result.request.environment_type} ({'✓' if result.success else '✗'})")

# Execute in parallel with progress tracking
results = resolver.resolve_batch(
    requests,
    progress_callback=progress_callback,
    fail_fast=False  # Continue processing even if some fail
)

# Process results
for result in results:
    if result.success:
        print(f"Found {len(result.dependencies)} detectors")
    else:
        print(f"Error: {result.error}")

# Get results as dictionary format
dict_results = resolver.resolve_batch_as_dict(requests)
```

#### Low-Level Interface

For maximum control, access core classes directly:

```python
from dependency_resolver import Orchestrator, HostExecutor, OutputFormatter

executor = HostExecutor()
orchestrator = Orchestrator(debug=True, skip_system_scope=True)
dependencies = orchestrator.resolve_dependencies(executor)
formatter = OutputFormatter()
json_output = formatter.format_json(dependencies, pretty_print=True)
```

**Available convenience functions:**

- `resolve_host_dependencies()` - Analyze host system, returns JSON string
- `resolve_docker_dependencies()` - Analyze Docker container, returns JSON string
- `resolve_dependencies_as_dict()` - Generic analysis, returns Python dictionary

**Available classes:**

- `DependencyResolver` - Main class for single and batch operations with parallel processing
- `ResolveRequest` - Configuration for individual resolution requests
- `ResolveResult` - Result object containing dependencies, errors, and execution metadata
- `Orchestrator` - Core dependency resolution coordinator
- `HostExecutor`, `DockerExecutor`, `DockerComposeExecutor` - Environment adapters
- `OutputFormatter` - JSON formatting utilities

**When to use each interface:**

- **Functional Interface**: Simple one-off dependency resolution
- **Class-Based Interface**: Multiple environments, parallel processing, shared configuration, progress tracking
- **Low-Level Interface**: Custom orchestration, advanced error handling, integration with existing frameworks

### Supported Environments

- **host** - Host system analysis (default)
- **docker** - Docker container analysis (requires container ID or name)
- **docker_compose** - Docker Compose stack analysis (requires stack/project name)

### Supported Package Managers

Currently supported:

- **apt/dpkg** - System packages Ubuntu/Debian
- **apk** - System packages of Alpine
- **pip** - Python packages
- **npm** - Node.js packages
- **docker-compose** - Container images from Docker Compose stacks
- **docker-info** - Individual Docker container metadata

### Output Format

The tool outputs JSON with the following structure:

```json
{
  "_container-info": {
    "name": "nginx-container",
    "image": "nginx:latest",
    "hash": "sha256:2cd1d97f893f..."
  },
  "docker-compose": {
    "scope": "compose",
    "dependencies": {
      "web": {
        "version": "django_app-web:latest",
        "hash": "sha256:3e4def6e2af8..."
      },
      "db": {
        "version": "postgres:13",
        "hash": "sha256:54706ca98cd5..."
      }
    }
  },
  "dpkg": {
    "scope": "system",
    "dependencies": {
      "package-name": {
        "version": "1.2.3 amd64",
        "hash": "abc123..."
      }
    }
  },
  "pip": {
    "scope": "project",
    "location": "/path/to/venv/lib/python3.12/site-packages",
    "hash": "def456...",
    "dependencies": {
      "package-name": {
        "version": "1.2.3"
      }
    }
  }
}
```

## Documentation

### Architecture & Detector Documentation

For detailed information about architectural decisions and package manager implementations:

- **Architecture Decision Records**: See [docs/adr/](./docs/adr/) for architectural decisions
- **Detector Documentation**: See [docs/detectors/](./docs/detectors/) for detailed implementation information:
  - [APK Detector](./docs/detectors/apk_detector.md) - Alpine Linux package detection
  - [DPKG Detector](./docs/detectors/dpkg_detector.md) - Debian/Ubuntu package detection
  - [NPM Detector](./docs/detectors/npm_detector.md) - Node.js package detection
  - [PIP Detector](./docs/detectors/pip_detector.md) - Python package detection
  - [Docker Compose Detector](./docs/detectors/docker_compose_detector.md) - Container image detection
  - [Docker Info Detector](./docs/detectors/docker_info_detector.md) - Individual container metadata

See the complete [SPECIFICATION.md](./SPECIFICATION.md) for detailed requirements and implementation constraints.

## Contributing

For development setup, contribution guidelines, and information about running tests and code quality checks, please see [CONTRIBUTING.md](./CONTRIBUTING.md).
